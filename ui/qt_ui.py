'''
量角器 - Fluent 界面（PySide6 + QFluentWidgets）
设计思路与旧 tkinter 版不同：左侧是 Fluent 导航（按数据类型分页），
右侧是「条目列表 | 译文/原文」+ 可自由拖拽的 AI 侧栏。
引擎（bena/anne）完全不用知道这些。
'''
import os
import traceback

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFontDatabase, QIcon, QKeySequence, QTextLayout, QTextOption
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QPalette

from ui.qt_widgets import (
    BodyLabel,
    CaptionLabel,
    CheckBox,
    FluentIcon,
    FluentWindow,
    InfoBar,
    InfoBarPosition,
    ListWidget,
    NavigationItemPosition,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    SearchLineEdit,
    SegmentedWidget,
    SubtitleLabel,
    TitleLabel,
    ToolButton,
)

import anne
import bena
import bootstrap
try:
    from qfluentwidgets import ComboBox
except ImportError:      # 没有 Fluent 时退回原生控件（备用环境）
    from PySide6.QtWidgets import QComboBox as ComboBox
from ui import palette
from ui.json_highlight import JsonHighlighter
from ui.qt_search import SearchDebouncer
from ui.qt_workers import ItemTranslateWorker
from ui.qt_tree import (
    ROLE_AI_STATE,
    ROLE_LINK,
    ROLE_MATCH_SPANS,
    ROLE_NODE_PATH,
    ROLE_ORIGIN_TEXT,
    NodeDelegate,
    TreeRenderer,
    ai_color,
    extract_copy_options,
    format_ranges,
    make_tree,
    raw_json_text,
)
from ui.treemodel import filter_items, match_spans

APP_TITLE = "贝娜的量角器"

# 数据类型 → 配色 token / 前缀图标（L2 类型分级）
TYPE_STYLE = {
    "buff" : ("type.buff","●"),
    "buff_template" : ("type.template","◆"),
    "global_buff" : ("type.global","★"),
    "rogue_item" : ("type.relic","▲"),
}

# 目录行把「类型 token」存在这个 role 上，由委托绘制时决定颜色
ROLE_TYPE_TOKEN = Qt.UserRole + 21

# 这些控件的文字一律用透明底（见 DataPage/主窗口的 _page_qss）
FIELD_TYPES = (
    "StrongBodyLabel","BodyLabel","CaptionLabel","SubtitleLabel","TitleLabel",
    "LargeTitleLabel","CheckBox","LineEdit","SearchLineEdit","PlainTextEdit",
    "TextEdit","SpinBox","DoubleSpinBox","ComboBox","ListWidget","TreeWidget",
)


class TypeColorDelegate(QStyledItemDelegate):
    '''目录列表的绘制：左侧类型色条 + 按行的类型 token 取当前配色上色

    这样换主题/改配色只要重绘可见区域即可，不用遍历上万条目去改颜色。
    注意：QFluentWidgets 的 ListWidget 会按自己的「私有协议」回调委托
    （setSelectedRows / setHoverRow 等），少了这些方法会在 clear/选中时抛异常，
    所以下面把这几个接口都补成幂等实现。
    '''

    def __init__(self,parent=None):
        super().__init__(parent)
        self._selected_rows = set()
        self._hover_row = -1
        self._pressed_row = -1
        self._editing_index = None

    # ---- QFluentWidgets 私有协议（缺了会报错，实现成无害即可）----
    def setSelectedRows(self,rows):
        self._selected_rows = set(rows or [])

    def selectedRows(self):
        return sorted(self._selected_rows)

    def setHoverRow(self,row):
        self._hover_row = int(row)

    def setPressedRow(self,row):
        self._pressed_row = int(row)

    def setEditingIndex(self,index):
        self._editing_index = index

    def setItemDelegate(self,delegate):
        return None

    def paint(self,painter,option,index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt,index)
        token = index.data(ROLE_TYPE_TOKEN)
        color = palette.qcolor(token) if token else None
        if color is None:
            color = palette.qcolor("text.secondary")
        selected = bool(opt.state & QStyle.State_Selected)
        # 先把行动手画出来（底色 + 圆角），再交给样式画文字——
        # 走的仍然是 style.drawControl(CE_ItemViewItem)，选中/悬浮语义不会丢。
        self._paint_row_background(painter,opt,selected)
        opt.palette.setColor(QPalette.Text,color)
        opt.palette.setColor(QPalette.HighlightedText,color)
        opt.text = ""
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem,opt,painter,opt.widget)
        # 类型色条：让「这条是 Buff / 模板 / 全局 / 藏品」一眼可辨
        bar = opt.rect.adjusted(2,3,-opt.rect.width() + 5,-3)
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(bar,1.5,1.5)
        painter.restore()
        self._paint_text(painter,opt,index,color)

    def _paint_row_background(self,painter,opt,selected):
        '''选中/悬浮行底色：不能依赖 Fluent 自带的选中色（配我们的目录底色几乎看不见）'''
        row = opt.rect
        painter.save()
        painter.setPen(Qt.NoPen)
        if selected:
            painter.setBrush(QColor(palette.hex("surface.selected")))
        elif opt.state & QStyle.State_MouseOver:
            painter.setBrush(QColor(palette.hex("surface.hover")))
        else:
            painter.restore()
            return
        painter.drawRoundedRect(row.adjusted(0,1,-1,-1),5,5)
        painter.restore()

    def _paint_text(self,painter,opt,index,base_color):
        '''文字单独用 QTextLayout 画一次（命中高亮靠 FormatRange，不重画第二遍）'''
        text = index.data(Qt.DisplayRole)
        if not text:
            return
        font = index.data(Qt.FontRole) or opt.font
        spans = index.data(ROLE_MATCH_SPANS) or []
        content = opt.rect.adjusted(10,3,-6,-3)
        if content.width() <= 0:
            return
        layout = QTextLayout(str(text),font)
        wrap = QTextOption()
        wrap.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        layout.setTextOption(wrap)
        layout.beginLayout()
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(float(content.width()))
        layout.endLayout()
        painter.save()
        painter.setClipRect(opt.rect)
        painter.setPen(base_color)
        layout.draw(painter,QPointF(content.left(),content.top()),
                    format_ranges(str(text),spans,base_color))
        painter.restore()

# 导航分组与数据类型的对应关系（基础类型固定；肉鸽季度由 bena 从数据推导，见 nav_sections()）
NAV_SECTIONS = [
    ("常见Buff","buff",FluentIcon.TAG),
    ("Buff模板","buff_template",FluentIcon.LIBRARY),
    ("全局Buff","global_buff",FluentIcon.GLOBE),
]


def nav_sections():
    '''左侧导航的完整清单：基础类型 + 数据里实际存在的肉鸽季度

    以前肉鸽六季是写死在这张表里的（含中文名），游戏一出新季度就得改代码。
    现在季度号与名称都来自 `bena.roguelike_season_catalog()`，
    加新肉鸽时这里、加载项清单、跳转解析都会自动跟上。
    '''
    sections = list(NAV_SECTIONS)
    try:
        catalog = bena.roguelike_season_catalog()
    except Exception as error:
        print("[量角器]读取肉鸽季度列表失败："+str(error))
        catalog = {}
    for key,label in catalog.items():
        sections.append((f"{label}肉鸽",key,FluentIcon.TILES))
    return sections


# 兼容旧引用：模块级的函数名（别在 import 期求值，那时数据可能还没下载）
NAV_SECTIONS_ALL = nav_sections

# 一个导航页对应一个数据类型；肉鸽各季共用 rogue_item
DATA_TYPE_ALIASES = {key:"rogue_item" for key in
                     ("rogue_1","rogue_2","rogue_3","rogue_4","rogue_5","rogue_6")}


class ProtractorItem:
    '''目录里的一条（与原 protractor.py 的 Item 等价）'''

    def __init__(self,index,data_type,data_key,data_reference):
        self.data_type = data_type
        self.data_key = data_key
        self.data_reference = data_reference
        self.display_name = ""
        self.index = index
        # data_reference 可能是 None（例如 display_by_id 传了个不存在的 id，
        # 或某条数据没解析出来）：这时退回用 key 当显示名，绝不能在这里崩掉
        if data_reference is None:
            self.display_name = str(data_key)
        elif self.data_type == "buff_template":
            self.display_name = "[模板]"+data_reference.display_name
        elif self.data_type == "buff":
            self.display_name = "[Buff]"+data_reference.display_name
        elif self.data_type == "global_buff":
            self.display_name = "[GBuff]"+data_reference.display_name
        elif self.data_type == "rogue_item":
            self.display_name = "["+data_reference.display_type+"]"+data_reference.display_name
        else:
            self.display_name = str(data_reference)

    @property
    def full_key(self):
        return self.data_type + "." + self.data_key


class SidebarSlot(QWidget):
    '''侧栏插槽：每个数据页的分栏里都有一个，真正装侧栏的只有一个

    QSplitter 一旦有了 widget 就不能再塞第二个，所以不能把同一个侧栏同时放进所有页；
    切页时由这里把侧栏「搬」到当前页的插槽里（插槽留在原页、保持空着，不破坏分栏结构）。
    '''

    def __init__(self,parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarSlot")
        self.setMinimumWidth(0)
        self.sidebar = None
        # 必须有个布局：否则把侧栏 setParent 进来之后没人给它排位，
        # 它会保持旧尺寸（表现为「插槽变宽了，侧栏还是原来那么窄」）。
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0,0,0,0)
        self._layout.setSpacing(0)

    # 对外表现得像个普通侧栏控件
    def width(self):
        return self.sidebar.width() if self.sidebar is not None else 0

    def isVisible(self):
        return super().isVisible() and self.sidebar is not None

    def take_sidebar(self):
        '''如果侧栏现在在我这里，把它摘下来交给调用方'''
        if self.sidebar is None:
            return None
        panel = self.sidebar
        self.sidebar = None
        self._layout.removeWidget(panel)
        panel.setParent(None)
        return panel

    def mount(self,panel):
        panel.setParent(self)
        self.sidebar = panel
        if self._layout.indexOf(panel) < 0:
            self._layout.addWidget(panel)
        return panel


class DataPage(QWidget):
    '''一个数据类型页：搜索 + 条目列表 + 译文/原文 + AI 侧栏

    条目是懒加载的：先在数据层收集好，等这一页真的被打开时再往列表里插，
    否则启动时要给九个页面上万条建列表项（实测 3.5s，全花在布局重算上）。
    '''

    def __init__(self,title,section_key,data_type,owner):
        super().__init__(owner.window)
        self.setObjectName(section_key)
        self.title = title
        self.section_key = section_key
        self.data_type = data_type
        self.owner = owner
        self.items = []              # 全部条目
        self.filtered = []           # 当前显示（过滤后）
        self.loaded = False          # 是否已经把条目填进列表控件
        self.nav_visible = True      # 左侧导航里是否显示（apply_nav_filter 维护）
        self.colors_dirty = False
        self.current = None
        self.translation = None
        self.raw = None
        self.displaying = ""
        self.current_pending = None  # 当前条目还没译出来的片段数（None = 还没算）

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16,12,16,12)
        layout.setSpacing(10)

        # ---- 顶部：标题 + 搜索 ----
        self.toolbar = QWidget(self)
        top = QHBoxLayout(self.toolbar)
        top.setContentsMargins(0,0,0,0)
        top.setSpacing(10)
        self.heading = SubtitleLabel(title,self)
        top.addWidget(self.heading)
        self.count_label = CaptionLabel("0 条",self)
        top.addWidget(self.count_label)
        top.addStretch(1)
        self.search = SearchLineEdit(self)
        self.search.setPlaceholderText("搜索名称或 ID，空格分词可组合多个条件")
        self.search.setFixedWidth(320)
        self.search.returnPressed.connect(self.apply_filter)
        # 防抖：连续输入合并成一次重建（上万条目录每敲一个字重建一次会明显卡）
        self.debouncer = SearchDebouncer(self.search,self.apply_filter,delay=200)
        top.addWidget(self.search)
        # 排序：默认保持数据里的顺序（与游戏数据一致、稳定）；
        # 想按名字找的时候切到「按名称」，切换后仍会保住当前选中的那条。
        # 说明：这里**不提供**「只看待译」筛选——那需要把整页上万条都翻一遍才知道
        # 有没有未译片段，会直接卡死界面；待译数量只在当前条目上显示（见 count_label）。
        self.sort_box = ComboBox(self)
        for value,label in (("default","默认顺序"),("name","按名称"),("id","按 ID")):
            self.sort_box.addItem(label,userData=value)
        self.sort_box.setFixedWidth(120)
        self.sort_box.currentIndexChanged.connect(lambda _: self.apply_filter())
        top.addWidget(self.sort_box)
        self.ai_button = PushButton("AI 侧栏",self)
        self.ai_button.setCheckable(True)
        self.ai_button.setChecked(True)
        self.ai_button.clicked.connect(owner.toggle_sidebar)
        top.addWidget(self.ai_button)
        layout.addWidget(self.toolbar)

        # ---- 主体：列表 | 译文/原文 | AI ----
        self.splitter = QSplitter(Qt.Horizontal,self)
        self.splitter.setChildrenCollapsible(False)
        layout.addWidget(self.splitter,1)

        self.directory = ListWidget(self)
        self.directory.setMinimumWidth(180)
        self.directory.setStyleSheet(_card_qss())
        self.directory.setItemDelegate(TypeColorDelegate(self.directory))
        self.directory.currentItemChanged.connect(lambda *_: self.owner.show_selected(self))
        self.splitter.addWidget(self.directory)

        viewer = QWidget(self)
        viewer_layout = QVBoxLayout(viewer)
        viewer_layout.setContentsMargins(0,0,0,0)
        viewer_layout.setSpacing(6)
        self.pivot = None
        if not os.environ.get("BENA_UI_NO_PIVOT"):
            self.pivot = SegmentedWidget(viewer)
            self.pivot.addItem("translation","译文",lambda: self.tabs.setCurrentIndex(0))
            self.pivot.addItem("origin","原文",lambda: self.tabs.setCurrentIndex(1))
            self.pivot.setCurrentItem("translation")
            pivot_row = QHBoxLayout()
            pivot_row.addWidget(self.pivot)
            pivot_row.addStretch(1)
            viewer_layout.addLayout(pivot_row)

        self.tabs = QStackedWidget(viewer)
        self.tree = make_tree(viewer)
        # 让唯一一列吃满可视宽度，长句才能按栏宽折行、不出现大片空白
        header = self.tree.header()
        if header is not None:
            try:
                from PySide6.QtWidgets import QHeaderView
                header.setSectionResizeMode(0,QHeaderView.Stretch)
            except Exception:
                pass
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.context_menu)
        self.renderer = TreeRenderer().bind(self.tree)
        self.tabs.addWidget(self.tree)

        self.origin = PlainTextEdit(viewer)
        self.origin.setReadOnly(True)
        self.origin.setLineWrapMode(PlainTextEdit.NoWrap)
        self.origin.setFont(_mono_font())
        self.json_highlighter = JsonHighlighter(self.origin.document())
        self.tabs.addWidget(self.origin)
        viewer_layout.addWidget(self.tabs,1)

        # 搜索无结果的空状态：以前是一整块空白，看不出「是没搜到」还是「还没加载」
        self.empty_hint = BodyLabel("",viewer)
        self.empty_hint.setWordWrap(True)
        self.empty_hint.setAlignment(Qt.AlignCenter)
        self.empty_hint.setVisible(False)
        viewer_layout.addWidget(self.empty_hint,1)
        self.clear_button = PushButton("清空搜索",viewer)
        self.clear_button.setFixedWidth(140)
        self.clear_button.clicked.connect(self.clear_search)
        self.clear_button.setVisible(False)
        clear_row = QHBoxLayout()
        clear_row.addStretch(1)
        clear_row.addWidget(self.clear_button)
        clear_row.addStretch(1)
        viewer_layout.addLayout(clear_row)
        self.splitter.addWidget(viewer)

        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,1)
        # 三栏（列表 | 译文/原文 | AI 侧栏插槽）：给侧栏一个合理初始宽度，别把译文挤成窄条
        self.sidebar_slot = SidebarSlot(self)
        self.splitter.addWidget(self.sidebar_slot)
        self.splitter.setStretchFactor(2,0)
        self.splitter.setSizes([240,720,400])

    # ----------------------------------------
    # 条目
    # ----------------------------------------
    def _make_row(self,item):
        '''目录行：类型 token 存在 UserRole（颜色/色条/命中高亮都交给委托按当前配色画）

        注意两件事：
        1. **不要在这里 setForeground**。九千多条目录逐条设颜色要花几十秒，
           改配色/切主题时更是灾难；颜色由 TypeColorDelegate 在绘制时决定。
        2. 行文本必须与 item.display_name 完全一致（以前手写了前导空格，导致
           筛选、复制、命中高亮用的文本和显示文本对不上）；缩进交给委托的 rect 处理。
        '''
        row = QListWidgetItem(item.display_name,self.directory)
        row.setData(Qt.UserRole,item)
        row.setData(ROLE_TYPE_TOKEN,TYPE_STYLE.get(item.data_type,("text.secondary","•"))[0])
        row.setToolTip(item.full_key)
        return row

    def restyle_directory(self):
        '''配色/主题变了：目录颜色由委托现画，这里只需要重绘可见区域（零遍历）'''
        self.directory.viewport().update()

    def restyle_light(self):
        '''过渡动画中途的轻量重绘：只让可见区域按新配色重画，不重设 QSS、不重建树

        原文面板/消息区这类 QSS 上色的控件必须在这里单独处理：
        它们的底色和文字色是「设计时」写进样式表的，光 update() 不会变色，
        结果就是「中间的文本框比别的地方慢半拍」。
        这里改成每帧重设一次 QPalette（很便宜），让它们跟着过渡走。
        '''
        from ui.qt_tree import recolor_tree
        self.directory.viewport().update()
        self.tree.viewport().update()
        recolor_tree(self.tree,self.renderer.items)
        palette.apply_text_palette(self.origin,"surface.inset","text.primary")
        self.origin.viewport().update()
        self.heading.setStyleSheet(palette.qss("text.primary"))
        self.count_label.setStyleSheet(palette.qss("text.secondary"))
        if not self.tabs.isVisible():
            self.empty_hint.setStyleSheet(palette.qss("text.muted"))

    def apply_container_style(self):
        '''给自己的页面铺底色（具名选择器，不影响按钮/输入框的 Fluent 配色）'''
        name = f"benaPage_{self.section_key}"
        self.setObjectName(name)
        self.setStyleSheet(palette.qss_container("surface.window",object_name=name)
                           + palette.qss_text_view("surface.inset","text.primary",
                                                   "surface.border"))
        # 原文面板同样是「视口自绘」，调色板也设一份
        if getattr(self,"origin",None) is not None:
            palette.apply_text_palette(self.origin,"surface.inset","text.primary")

    def restyle(self,surfaces_changed=True):
        '''配色变了：列表/树底色、原文面板、节点颜色都重刷一遍

        关键：**不重建译文树**。以前这里是 show_translation() 重放整棵树上千个节点，
        改一次颜色要 570ms 起步（拖取色器和切预设时一顿一顿的）。
        现在只按新配色重写 ForegroundRole（recolor_tree），结构/展开/滚动/选中都不动。

        surfaces_changed=False 时（只改了文字类颜色）连 QSS 也不重设——
        重设样式表会触发整窗重建，拖色时那样做会很卡。
        '''
        from ui.qt_tree import recolor_tree, restyle_tree
        if surfaces_changed:
            self.directory.setStyleSheet(_card_qss())
            restyle_tree(self.tree)
        # 标题与计数行：只上文字色，底色透明（露出所在容器底色）
        self.heading.setStyleSheet(palette.qss("text.primary"))
        self.count_label.setStyleSheet(palette.qss("text.secondary"))
        self.origin.viewport().update()
        recolor_tree(self.tree,self.renderer.items)

    def add_item(self,item):
        '''只收集，不动列表控件（真正的插入在 ensure_loaded 里一次做完）'''
        self.items.append(item)
        self._refresh_count()

    def ensure_loaded(self):
        '''把收集到的条目一次性填进列表（带批量插入优化）'''
        if self.loaded:
            return
        self.loaded = True
        self.directory.setUpdatesEnabled(False)
        try:
            for item in self.items:
                self._make_row(item)
        finally:
            self.directory.setUpdatesEnabled(True)
        self.filtered = list(self.items)
        self._refresh_count()

    def _refresh_count(self):
        '''标题旁的计数：命中/总数 条，以及当前条目还剩多少处待译片段

        「N 处待译」只在当前选中的条目上有意义（那是唯一已经翻译过的条目），
        所以它不是筛选条件，而是给「这条还要不要继续补译」的提示。
        '''
        total = len(self.items)
        shown = len(self.filtered) if self.loaded else total
        text = f"{total} 条" if shown == total else f"{shown} / {total} 条"
        if self.current_pending:
            text += f"　·　{self.current_pending} 处待译"
        self.count_label.setText(text)

    def update_count(self):
        self._refresh_count()

    def pending_count(self,translation):
        '''这条译文里还有多少处没译出来（不用碰引擎，纯结构遍历）'''
        if translation is None:
            return 0
        try:
            from ai import config as config_module
            from ai.fragments import pending_fragments
            heuristic = bool(config_module.get("enable_heuristic_fragments",True))
            return len(pending_fragments(translation,heuristic=heuristic))
        except Exception:
            return 0

    def set_pending(self,count):
        self.current_pending = int(count or 0) or None
        self._refresh_count()

    def sort_key(self):
        '''排序下拉当前对应的 key 函数（默认顺序返回 None，保持数据原序）'''
        value = self.sort_box.currentData() if getattr(self,"sort_box",None) is not None else "default"
        if value == "name":
            return lambda item: str(getattr(item,"display_name",""))
        if value == "id":
            return lambda item: str(getattr(item,"data_key","")).casefold()
        return None

    def apply_filter(self,keep=None):
        '''按搜索框内容重建目录（含命中高亮），并处理「一条都没有」的空状态

        只重建列表控件、不碰译文树：筛选不改当前条目，用户还能继续读手上这条。

        keep: 重建后要恢复选中的 full_key。注意必须在**重建之前**把
              page.current.full_key 传进来——setCurrentRow(0) 会立刻改写 page.current，
              等到重建之后再去读就晚了（以前 clear_search 就是这么错的）。
        '''
        self.ensure_loaded()
        keywords = [word for word in self.search.text().strip().split(" ") if word]
        matched, hits = filter_items(self.items,keywords,keep=keep,
                                     sort_key=self.sort_key())
        self.directory.setUpdatesEnabled(False)
        try:
            self.directory.clear()
            for item in matched:
                row = self._make_row(item)
                spans = hits.get(item.full_key)
                if spans:
                    row.setData(ROLE_MATCH_SPANS,spans)
        finally:
            self.directory.setUpdatesEnabled(True)
        self.filtered = matched
        self._refresh_count()
        if self.directory.count() > 0:
            self._hide_empty_hint()
            if keep:
                restored = self.select_key(keep)
                if not restored:
                    keep = None
            if not keep:
                # 目标行不在筛选结果里（或本来就没选中）：显示第一条
                self.directory.setCurrentRow(0)
        else:
            self._show_empty_hint()

    # ----------------------------------------
    # 空状态
    # ----------------------------------------
    def _show_empty_hint(self):
        '''没有匹配结果：清空显示区并给出可读提示 + 一键清空搜索'''
        self.hide_hint()
        self.renderer.clear()
        self.origin.setPlainText("")
        self.current = None
        self.translation = None
        self.raw = None
        self.displaying = ""
        self.set_pending(0)
        self.empty_hint.setText(f"没有匹配「{self.search.text().strip()}」的条目"
                                f"（本页共 {len(self.items)} 条）")
        self.empty_hint.setVisible(True)
        self.clear_button.setVisible(True)
        self.tabs.setVisible(False)
        self.owner.on_item_changed(None)

    def _hide_empty_hint(self):
        self.empty_hint.setVisible(False)
        self.clear_button.setVisible(False)
        self.tabs.setVisible(True)

    def hide_hint(self):
        '''把空状态收起来（选中了别的条目/切页时调）'''
        self._hide_empty_hint()

    def clear_search(self):
        '''清空搜索并尽量回到清空前的选中项（而不是跳回第一行）'''
        if self.search.text() != "":
            # 必须在重建目录之前取：apply_filter 里的 setCurrentRow(0) 会改写 current
            previous = self.current.full_key if self.current is not None else None
            self.search.blockSignals(True)
            try:
                self.search.setText("")
            finally:
                self.search.blockSignals(False)
            # 屏蔽信号期间 textChanged 不会发出，防抖器记的旧文本就过期了：
            # 不同步的话「清空后再敲第一个字符」会走延迟路径，看着像没反应。
            self.debouncer.sync()
            self.apply_filter(keep=previous)
            return True
        return False

    def select_key(self,full_key):
        '''在目录里按 full_key 选中某一行；找不到返回 False'''
        for index in range(self.directory.count()):
            candidate = self.directory.item(index).data(Qt.UserRole)
            if candidate is not None and candidate.full_key == full_key:
                self.directory.setCurrentRow(index)
                return True
        return False

    def current_item(self):
        row = self.directory.currentItem()
        if row is None:
            return None
        return row.data(Qt.UserRole)

    def focus_search(self):
        self.search.setFocus()
        self.search.selectAll()

    def search_by(self,things):
        self.search.setText(str(things))
        self.apply_filter()

    # ----------------------------------------
    # 右键菜单
    # ----------------------------------------
    def context_menu(self,point):
        tree_item = self.tree.itemAt(point)
        if tree_item is None:
            return
        text = tree_item.text(0)
        if text == "":
            return
        from qfluentwidgets import Action, RoundMenu
        menu = RoundMenu(parent=self.tree)
        link = tree_item.data(0,ROLE_LINK)
        if link:
            for one in str(link).split(","):
                if one.startswith("prts."):
                    menu.addAction(Action(FluentIcon.LINK,f"打开 PRTS {one[5:]}",
                                          triggered=lambda _=False,page=one[5:]: self.owner.open_prts(page)))
                elif "." in one:
                    menu.addAction(Action(FluentIcon.LINK,f"转跳到 {one}",
                                          triggered=lambda _=False,target=one: self.owner.link_jump(self,target)))
                    menu.addAction(Action(FluentIcon.SEARCH,f"搜索 {one.split('.',1)[1]}",
                                          triggered=lambda _=False,key=one.split(".",1)[1]: self.search_by(key)))
                else:
                    menu.addAction(Action(FluentIcon.LINK,f"转跳到 {one}",
                                          triggered=lambda _=False,target=one: self.owner.link_jump(self,target)))
                    menu.addAction(Action(FluentIcon.SEARCH,f"搜索 {one}",
                                          triggered=lambda _=False,key=one: self.search_by(key)))
            menu.addSeparator()
        panel = self.owner.ai_panel
        if panel is not None:
            menu.addAction(Action(FluentIcon.ROBOT,"翻译这一行",
                                  triggered=lambda _=False,item=tree_item: panel.translate_node(item)))
            menu.addAction(Action(FluentIcon.CHAT,"解释这一行",
                                  triggered=lambda _=False,item=tree_item: panel.explain_node(item)))
            menu.addSeparator()
        menu.addAction(Action(FluentIcon.COPY,"复制整行",
                              triggered=lambda _=False,value=text: self.owner.copy(value)))
        for label,content in extract_copy_options(text):
            menu.addAction(Action(FluentIcon.COPY,f"复制 {label}",
                                  triggered=lambda _=False,value=content: self.owner.copy(value)))
        menu.addSeparator()
        menu.addAction(Action(FluentIcon.DOCUMENT,"复制本行及子项",
                              triggered=lambda _=False,item=tree_item: self.owner.copy(self.renderer.to_text(item))))
        menu.addAction(Action(FluentIcon.DOCUMENT,"复制全文",triggered=lambda _=False: self.owner.copy_all()))
        menu.exec(self.tree.viewport().mapToGlobal(point))

    # ----------------------------------------
    # 展示
    # ----------------------------------------
    def show_translation(self,struct,link_stacks=None):
        self.translation = struct
        self.renderer.show_translation(struct,link_stacks)
        self.tabs.setCurrentIndex(0)

    def show_raw(self,datas):
        self.translation = None
        self.renderer.show_raw(datas)
        self.tabs.setCurrentIndex(0)

    def show_origin(self,datas):
        self.raw = datas
        self.origin.setPlainText(raw_json_text(datas))

    def show_error_node(self,message):
        from PySide6.QtWidgets import QTreeWidgetItem
        self.renderer.clear()
        item = QTreeWidgetItem(self.tree.invisibleRootItem())
        item.setText(0,message)
        item.setForeground(0,QColor("#D13438"))
        self.translation = None

    def item_at_path(self,node_path):
        return self.renderer.item_at_path(node_path)


class FluentProtractor:
    '''Fluent 界面主类；对外方法与旧 tkinter 版保持一致'''

    def __init__(self):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        self.app.setApplicationName(APP_TITLE)

        self.config = bootstrap.load_config()
        self._load_colors()
        self._apply_theme()
        self.window = FluentWindow()
        self.window.setWindowTitle(APP_TITLE)
        self.window.resize(1360,840)
        if os.path.exists("./icon/icon.ico"):
            self.window.setWindowIcon(QIcon("./icon/icon.ico"))

        self.pages = {}
        self.page_order = []
        self.nav_sections = []
        self.item_counts = {}        # section_key -> 本次加载的条目数（导航显隐按它判断）
        self.settings_interface = None
        self.ai_interface = None
        self.active_page = None
        self.directory_index = 0
        self.link_stacks = []
        self.ai_panel = None
        self._sidebar_user_hidden = False
        self.color_animating = False
        self.closing = False
        self._last_info_bar = None      # 最近一条右下角提示（发新的之前先关掉它）
        # 条目译文：cache 让「切回去」瞬时呈现；worker 在后台算，算完再上屏
        self.translation_cache = {}
        self.item_workers = {}
        self.active_item_worker = None
        self._item_request_key = None

        self._build_ui()
        # 导航在这里就建好（所有数据页都注册进来，保证 switchTo 能用）；
        # 「本次没加载的类型」由 open() 里的 apply_nav_filter() 隐藏掉。
        self._build_nav()
        self._build_ai_panel()
        self._restore_geometry()
        self._apply_colors_to_widgets()
        self.apply_window_chrome()
        self._install_shortcuts()
        # 紧凑目录 / 字号是启动前就存好的偏好，建完界面立刻套上
        self.apply_directory_density()
        if abs(palette.font_scale() - 1.0) > 0.001:
            self.set_font_scale(palette.font_scale(),notify=False)

    # ----------------------------------------
    # 主题与配色
    # ----------------------------------------
    def _load_colors(self):
        '''从 config.json 读用户配色（预设 + 覆盖）'''
        colors = bootstrap.config_section("colors",{})
        preset = colors.get("preset") or "default"
        overrides = colors.get("overrides") if isinstance(colors.get("overrides"),dict) else {}
        palette.apply_overrides(overrides,preset=preset)

    def apply_colors(self,preset=None,overrides=None,save=True,animate=False,persist=None):
        '''改配色：立即生效（或平滑过渡）+ 写回 config.json + 重绘界面

        animate=True 时先把界面「渐变」到新配色（约 220ms），再落盘；
        拖取色器时不要开（每帧都会调进来，动画会被反复打断），切预设时开着很好看。

        persist 不填就跟随 save（兼容旧调用）：诊断脚本传 persist=False，
        只改显示、不写 config.json——否则跑一次出图就把用户的主题/配色改掉了。
        '''
        if persist is None:
            persist = save
        # persist=False 时连内存里的配置也不要动：否则脚本结束后内存与磁盘不一致
        colors = (bootstrap.config_section("colors",{}) if persist
                  else dict(bootstrap.config_section("colors",{}) or {}))
        if preset is not None:
            colors["preset"] = preset
        if overrides is not None:
            colors["overrides"] = overrides
        if not animate:
            if persist:
                bootstrap.config_update_section("colors",colors)
            palette.apply_overrides(colors.get("overrides") or {},preset=colors.get("preset"))
            self.repaint_colors()
            self.restyle_extra_pages()
            return
        # 目标配色只「算」出来，绝不顺手改当前状态：
        # 之前用 apply_overrides 算目标，它会把 palette 直接改成终点色，
        # 动画于是从终点起步（等于没有过渡，实测只有 2 个中间色）。
        target = palette.merge_overrides(colors.get("overrides") or {},colors.get("preset"))
        if persist:
            bootstrap.config_update_section("colors",colors)
        self.color_animating = True

        def _frame():
            try:
                self.repaint_colors(surfaces_changed=False,light=True)
            except Exception as error:
                print("[量角器]配色过渡重绘失败："+str(error))

        def _cancel():
            return bool(getattr(self,"closing",False))

        palette.animate_to(target,on_frame=_frame,cancel=_cancel)
        QTimer.singleShot(340,self._finish_color_animation)

    def _finish_color_animation(self):
        '''过渡结束：用最终配色做一次完整重刷（把 QSS 类的东西也校准）'''
        self.color_animating = False
        self.repaint_colors()

    def repaint_colors(self,surfaces_changed=True,light=False):
        '''配色变了之后，把已经渲染出来的内容按新颜色重画一遍

        light=True 是过渡动画中途用的轻量路径：
          只重绘可见区域（委托/树/目录/卡片都是「按 palette 现取色」画的），
          不重设任何 QSS（重设样式表会触发整窗重建，每帧都做必然卡顿）。
        过渡结束后再走一次完整路径（surfaces_changed=True）做收尾校准。
        另外：只重建「当前正在看的页」，其它页标脏、等切过去再重建。
        '''
        if light:
            current = self._current_page()
            for page in self.pages.values():
                if page is current:
                    page.restyle_light()
                else:
                    page.colors_dirty = True
            self.restyle_extra_pages(light=True)
            if self.ai_panel is not None:
                self.ai_panel.refresh_ai_cards()
            highlighter = getattr(self,"json_highlighter",None)
            if highlighter is not None:
                highlighter.refresh()
            return
        if surfaces_changed:
            self._apply_colors_to_widgets()
        self.apply_window_chrome()
        current = self._current_page()
        for page in self.pages.values():
            if page is current:
                page.restyle(surfaces_changed=surfaces_changed)
                if page.current is not None:
                    page.restyle_directory()
            else:
                page.colors_dirty = True
        highlighter = getattr(self,"json_highlighter",None)
        if highlighter is not None:
            highlighter.refresh()
        if self.ai_panel is not None:
            self.ai_panel.restyle()

    def apply_window_chrome(self):
        '''把「窗口外围」的底色也换成我们的配色

        FluentWindow 自己画窗口背景，默认是 Fluent 那套灰（#F0F4F9 / #202020），
        跟我们的 surface.window 不是一回事——于是页面是暖色、窗口边缘还是冷灰，
        一眼就能看出「两层皮」。它正好留了 setCustomBackgroundColor(light, dark)，
        这里把亮/暗两套值都喂进去，明暗主题各自取对应的一半。

        顺带关掉 Mica：那是 Windows 的桌面取样材质，会把我们指定的颜色盖掉，
        还会随壁纸变色。纯色底交给 palette 才谈得上「配色统一」。
        '''
        window = getattr(self,"window",None)
        if window is None:
            return
        setter = getattr(window,"setCustomBackgroundColor",None)
        if not callable(setter):
            return
        light = palette.raw("surface.window")[0]
        dark = palette.raw("surface.window")[1]
        try:
            setter(light,dark)
        except Exception as error:
            print("[量角器]设置窗口底色失败："+str(error))
            return
        # 开了 Mica 的话上面的颜色基本看不出来（那是桌面取样材质），这里关一次。
        # 想留着 Mica 就用 config.json 的 "window": {"mica": true}。
        if not getattr(self,"_mica_disabled",False):
            self._mica_disabled = True
            if not bool(bootstrap.config_get("window","mica",False)):
                try:
                    window.setMicaEffectEnabled(False)
                except Exception:
                    pass
        window.update()

    def _apply_theme(self,value=None):
        '''主题只交给 QFluentWidgets 管：留空/auto = 跟随系统，light/dark = 强制

        value 显式给出时用它（persist=False 的场景下配置里并没有写进去，
        再去读 config 会读回旧值，表现为"切了主题但没生效"——这个坑踩过）。
        '''
        if value is None:
            value = self.config.get("theme","auto")
        value = str(value or "auto").lower()
        try:
            from qfluentwidgets import Theme, setTheme
            theme = {"light" : Theme.LIGHT,"dark" : Theme.DARK}.get(value,Theme.AUTO)
            setTheme(theme)
        except Exception as error:
            print("[量器]主题设置失败："+str(error))
        palette.refresh()
        self._apply_accent()

    # ----------------------------------------
    # 主题色（QFluentWidgets 原生强调色）
    # ----------------------------------------
    def accent_color(self):
        '''当前强调色的十六进制值'''
        try:
            from qfluentwidgets import themeColor
            return themeColor().name()
        except Exception:
            return palette.NATIVE_ACCENT_DEFAULT

    def _content_qss(self):
        '''内容区（stackedWidget）的样式：容器铺底色 + 纯文字透明

        三个「别踩」：
        1. **别对 FluentWindow 本身 setStyleSheet**：那会把 Fluent 给窗口的整套样式
           （包含左侧导航面板）整个替换掉，表现为「深色下导航还是浅色、图标看不清」，
           顺带还会让 Qt 报 "Could not parse application stylesheet"；
        2. 别用宽泛的 `QWidget { … }`：会把按钮/输入框的 Fluent 配色一起盖掉；
        3. 底色只挂到具名控件（这里的 stackedWidget）上。
        '''
        window = palette.hex("surface.window")
        object_name = getattr(self,"stack_object_name","benaStack")
        text_only = ",".join(palette.QSS_TEXT_TYPES)
        return (f"QStackedWidget#{object_name} {{ background-color:{window}; }}"
                f"{text_only} {{ background:transparent; }}")

    def _page_qss(self):
        '''其它（非数据）页面的容器样式：铺底色 + 纯文字透明'''
        return palette.qss_container("surface.window")

    def refresh_nav(self):
        '''刷新左侧导航的文字颜色

        QFluentWidgets 的导航项在构造时就把文字色定下来了（亮/暗各一套），
        首次加载与切换主题时不会自动跟着我们的配色走，表现为
        「深色主题下选中的那一项文字是黑的」。这里按当前配色显式刷一遍。
        '''
        nav = getattr(self.window,"navigationInterface",None)
        if nav is None:
            return
        light_text = palette.raw("text.primary")[0]
        dark_text = palette.raw("text.primary")[1]
        try:
            from qfluentwidgets.components.navigation.navigation_widget import NavigationWidget
            for widget in nav.findChildren(NavigationWidget):
                try:
                    widget.setTextColor(light_text,dark_text)
                except Exception:
                    continue
        except Exception as error:
            print("[量角器]刷新导航配色失败："+str(error))
        for target in (nav,getattr(nav,"panel",None),getattr(nav,"panelLayout",None)):
            if target is not None and hasattr(target,"update"):
                target.update()

    def _apply_colors_to_widgets(self):
        '''把配色铺到「内容区 + 各页面 + 侧栏」上（绝不碰 FluentWindow 自身）'''
        stack = getattr(self.window,"stackedWidget",None)
        if stack is not None:
            stack.setObjectName(getattr(self,"stack_object_name","benaStack"))
            stack.setStyleSheet(self._content_qss())
        for page in getattr(self,"pages",{}).values():
            page.apply_container_style()
            # 顶部工具条：用具名选择器，别用宽泛的 QWidget 规则（会盖掉搜索框/按钮的配色）
            bar = getattr(page,"toolbar",None)
            if bar is not None:
                bar_name = f"benaBar_{page.section_key}"
                bar.setObjectName(bar_name)
                bar.setStyleSheet(palette.qss_container("surface.window",
                                                        object_name=bar_name))
        for extra in ("settings_interface","ai_interface"):
            widget = getattr(self,extra,None)
            if widget is not None:
                widget.setStyleSheet(self._page_qss())
        for name in ("settings_page","ai_page"):
            page = getattr(self,name,None)
            restyle = getattr(page,"restyle",None)
            if callable(restyle):
                restyle()
        if self.ai_panel is not None:
            self.ai_panel.restyle()
        self.restyle_extra_pages()
        self.refresh_nav()

    def restyle_extra_pages(self,light=False):
        '''设置页/AI 页的卡片底色不跟 QSS（Fluent 自己画），换配色后要显式重画

        light=True 是过渡动画中途用的：只 update（自绘卡片逐帧换色很便宜），
        不重设样式表——否则这些卡片会比别的地方慢半拍到动画结束才变色。
        '''
        method = "refresh_colors" if light else "restyle"
        for name in ("settings_page","ai_page"):
            page = getattr(self,name,None)
            call = getattr(page,method,None)
            if callable(call):
                call()

    def _apply_accent(self):
        '''启动时把上次存的强调色装回去（QFluentWidgets 原生机制）'''
        value = str(self.config.get("accent","") or "").strip()
        if not value:
            return
        try:
            from qfluentwidgets import setThemeColor
            setThemeColor(value,save=False,lazy=False)
        except Exception as error:
            print("[量角器]强调色设置失败："+str(error))

    def set_accent(self,value,lazy=True):
        '''改强调色：走 QFluentWidgets 自己的机制（按钮/选中态/焦点框都会跟着变）'''
        self.config["accent"] = value
        bootstrap.config_set(None,"accent",value)
        try:
            from qfluentwidgets import setThemeColor
            setThemeColor(value,save=False,lazy=lazy)
        except Exception as error:
            print("[量角器]强调色设置失败："+str(error))
        if not lazy:
            self.repaint_colors(surfaces_changed=False)

    def animate_chrome(self,on_done=None,light=None,dark=None):
        '''切主题时让「窗口背景 + 侧栏/内容区底色」也跟着渐变

        FluentWindow 的背景色也要每帧重设（它是自绘的，光 update 不会变色）。
        亮/暗两个目标值在**切主题之前**先算好：切完之后 is_dark() 就翻了，
        那时候再问 palette 拿到的已经是终点色，动画中间就会跳一下。
        '''
        window = self.window
        setter = getattr(window,"setCustomBackgroundColor",None)
        if not callable(setter) or light is None or dark is None:
            if on_done is not None:
                on_done()
            return
        start_light = palette.raw("surface.window")[0]
        start_dark = palette.raw("surface.window")[1]
        frames = 16
        state = {"step" : 0}

        def _tick():
            state["step"] += 1
            ratio = palette._ease(state["step"] / frames)
            setter(palette._blend(start_light,light,ratio),
                   palette._blend(start_dark,dark,ratio))
            window.update()
            if state["step"] >= frames:
                timer.stop()
                setter(light,dark)
                if on_done is not None:
                    on_done()

        timer = QTimer(window)
        timer.setInterval(16)
        timer.timeout.connect(_tick)
        timer.start()
        return timer

    def set_theme(self,value,smooth=True,persist=True):
        '''切主题：palette 与窗口外围一起渐变，最后再让 Fluent 换它自己那部分

        为什么这样排：Fluent 的 setTheme() 会重算全局样式表（实测 ~2s，卡住主线程），
        而它替换掉的正好是「导航、按钮、输入框」这些我们本来就不管的控件。
        所以先让我们画的东西（内容区、译文树、卡片、窗口背景）平滑过渡，
        过渡结束再切 Fluent 自身的主题——避免中途出现「一半新色一半旧色」。

        persist=False：只改变显示，不写 config.json、也不改内存里的配置
        （诊断脚本出图用；如果连内存都改，脚本结束时内存与磁盘就不一致了，
          下一次读配置会以为设置已经生效——这个坑踩过）。
        '''
        if persist:
            self.config["theme"] = value
            bootstrap.config_set(None,"theme",value)
        # 目标配色（切之前算好：切完之后 is_dark() 就翻了，取值会取反）
        overrides,preset = self._colors_target()
        target = palette.merge_overrides(overrides,preset)
        light,dark = target.get("surface.window",palette.TOKEN["surface.window"])
        if smooth and not getattr(self,"color_animating",False):
            self.color_animating = True
            window = self.window

            def _frame():
                window.update()

            def _cancel():
                return bool(getattr(self,"closing",False))

            def _apply():
                # Fluent 换自己的样式表，随后把一切都按最终配色校准一遍
                self._apply_theme(value)            # 里面会 palette.refresh()
                self._apply_colors_to_widgets()
                self.apply_window_chrome()
                self.restyle_extra_pages()
                self.color_animating = False
                self.repaint_colors()

            # palette 逐帧过渡（内容区/译文树/卡片都按 palette 现取色，自动跟着走）
            palette.animate_to(target,on_frame=_frame,cancel=_cancel)
            # 窗口背景是自绘的，得每帧显式重设
            self.animate_chrome(on_done=_apply,light=light,dark=dark)
        else:
            self._apply_theme(value)
            self.repaint_colors()
        self.notify("主题已切换",{"auto":"跟随系统","light":"浅色","dark":"深色"}.get(value,value))

    def _colors_target(self):
        '''当前 config 里的配色目标 (overrides, preset)'''
        colors = bootstrap.config_section("colors",{}) or {}
        overrides = colors.get("overrides") if isinstance(colors.get("overrides"),dict) else {}
        return overrides,colors.get("preset")

    def set_font_scale(self,value,notify=True):
        '''全局字号缩放：译文树委托、目录、原文面板一起变

        NodeDelegate 的折行高度是按 (文本, 宽度, 字体) 缓存的，字体一变就得清缓存，
        否则行高还是旧字号算出来的（会叠字/截断）。
        '''
        applied = palette.set_font_scale(value)
        from ui.qt_tree import NodeDelegate, apply_tree_font_scale
        NodeDelegate._HEIGHT_CACHE.clear()
        for page in self.pages.values():
            apply_tree_font_scale(page.tree,page.origin)
            if page.current is not None and page.translation is not None:
                page.show_translation(page.translation)
        if notify:
            self.notify("字号已调整",f"{int(applied * 100)}%")
        return applied

    def set_compact_directory(self,checked):
        '''目录紧凑模式（行高小一点，一屏看更多条目）'''
        self.config["compact_directory"] = bool(checked)
        bootstrap.config_set(None,"compact_directory",bool(checked))
        self.apply_directory_density()
        self.notify("目录密度已更新","紧凑" if checked else "标准")

    def apply_directory_density(self):
        '''把当前密度设置套到所有页面的目录列表上（启动时也要调一次）'''
        for page in self.pages.values():
            if getattr(page,"directory",None) is not None:
                page.directory.setStyleSheet(_card_qss())

    def reset_layout(self):
        '''把各页面的分栏比例恢复默认（并落盘）'''
        bootstrap.config_set(None,"splitters",{},save=False)
        for page in self.pages.values():
            page.splitter.setSizes([240,720,400])
            self._balance_sidebar_space(page)
        self.notify("分栏已恢复默认","列表 240 / 译文 720 / 侧栏 400")

    # ----------------------------------------
    # 快捷键
    # ----------------------------------------
    def _install_shortcuts(self):
        '''全局快捷键：搜索 / 清空 / 复制 / 字号

        Esc 与 Ctrl+C 只在数据页且焦点不在文本框里时接管，避免影响原文面板的复制。
        '''
        shortcuts = (
            ("Ctrl+F",self._shortcut_search),
            ("Ctrl+Shift+C",self.copy_all),
            ("Ctrl+=",lambda: self.step_font_scale(1)),
            ("Ctrl++",lambda: self.step_font_scale(1)),
            ("Ctrl+-",lambda: self.step_font_scale(-1)),
            ("Ctrl+0",lambda: self.set_font_scale(1.0)),
            ("Esc",self._shortcut_clear_search),
            ("F5",self.ask_reload),
        )
        for sequence,slot in shortcuts:
            try:
                action = QAction(self.window)
                action.setShortcut(QKeySequence(sequence))
                action.setShortcutContext(Qt.WindowShortcut)
                action.triggered.connect(lambda _=False,fn=slot: fn())
                self.window.addAction(action)
            except Exception as error:
                print(f"[量角器]快捷键 {sequence} 注册失败：{error}")

    def _shortcut_search(self):
        page = self._current_page()
        if page is not None:
            page.focus_search()

    def _shortcut_clear_search(self):
        '''Esc：清空当前页搜索（搜索本来就是空的就什么也不做）'''
        page = self._current_page()
        if page is not None:
            page.clear_search()

    def step_font_scale(self,direction):
        '''按档位加减字号（Ctrl+= / Ctrl+-）'''
        steps = [0.9,1.0,1.15,1.3,1.45]
        current = palette.font_scale()
        index = min(range(len(steps)),key=lambda i: abs(steps[i] - current))
        index = min(max(index + (1 if direction > 0 else -1),0),len(steps) - 1)
        return self.set_font_scale(steps[index])

    # ----------------------------------------
    # 界面
    # ----------------------------------------
    def _build_ui(self):
        sections = nav_sections()            # 基础类型 + 数据里实际存在的肉鸽季度
        if os.environ.get("BENA_UI_SINGLE_PAGE"):
            sections = sections[:1]          # 排查用：只建一个页面
        # 内容区（FluentWindow 的 stackedWidget）单独起个名字，方便只给它上底色
        self.stack_object_name = "benaStack"
        self.window.stackedWidget.setObjectName(self.stack_object_name)
        for title,section_key,icon in sections:
            data_type = DATA_TYPE_ALIASES.get(section_key,section_key)
            page = DataPage(title,section_key,data_type,self)
            self.pages[section_key] = page
            self.page_order.append(section_key)

        # 文件 / 工具 快捷入口
        self.window.navigationInterface.setExpandWidth(220)
        self.window.navigationInterface.setMinimumExpandWidth(900)

    def _build_nav(self):
        '''建左侧导航：把所有数据页都注册进去，并把底部（设置/AI）建好

        为什么全部注册、而不是只注册加载了的：FluentWindow.switchTo() 对
        「没注册过的页面」会直接抛 "index is illegal"，而 --id 跳转、链接转跳、
        诊断脚本都会在窗口显示前就去切页面。所以注册归注册，
        「本次没加载的类型」由 apply_nav_filter() 隐藏掉（只隐藏，仍可 switchTo）。
        '''
        sections = {key:(title,icon) for title,key,icon in nav_sections()}
        for section_key in self.page_order:
            title,icon = sections.get(section_key,(section_key,FluentIcon.TAG))
            page = self.pages[section_key]
            self.window.addSubInterface(page,icon,title,
                                        NavigationItemPosition.SCROLL if section_key.startswith("rogue")
                                        else NavigationItemPosition.TOP)
        # 底部：设置 / AI 助手（ask_reload 重建导航时复用）
        if self.settings_interface is None:
            self.settings_interface = self._make_settings_page()
            self.window.addSubInterface(self.settings_interface,FluentIcon.SETTING,"设置",
                                        NavigationItemPosition.BOTTOM)
        if self.ai_interface is None:
            self.ai_interface = self._make_ai_page()
            self.window.addSubInterface(self.ai_interface,FluentIcon.ROBOT,"AI 助手",
                                        NavigationItemPosition.BOTTOM)
        self.theme_interface = self.settings_interface
        self.colors_interface = self.settings_interface
        self.reload_interface = self.settings_interface
        self.window.navigationInterface.addSeparator(NavigationItemPosition.BOTTOM)
        self.window.stackedWidget.currentChanged.connect(self._on_page_changed)

    def _loaded_sections(self):
        '''本次真正加载了数据的页面

        · 肉鸽六季共用 data_type，必须按页判断（每季一张表）；
        · 普通类型看 page.items 就够了（目录是懒加载的，条目先收在 items 里）；
        · item_counts 是 start_with 记下的权威计数，有就以它为准。
        '''
        counts = getattr(self,"item_counts",None) or {}
        loaded = set()
        for key in self.page_order:
            if key in counts:
                if counts[key] > 0:
                    loaded.add(key)
                continue
            if self.pages[key].items:
                loaded.add(key)
        return loaded

    def apply_nav_filter(self):
        '''按加载项显隐左侧导航：没加载的类型只隐藏、不摘除（仍可被 switchTo）

        必须走 panel.items 注册表：导航项实际挂在 panel.scrollLayout 上
        （panel.vBoxLayout 里只有 topLayout / scrollArea / bottomLayout），
        遍历主布局会一个项都找不到——之前就是这么白忙一场的。
        '''
        loaded = self._loaded_sections()
        if not loaded:
            return                          # 还没加载任何数据：保持原样，别把导航清空
        panel = getattr(getattr(self.window,"navigationInterface",None),"panel",None)
        registry = getattr(panel,"items",None) or {}
        visible = []
        handled = set()
        for key,entry in registry.items():
            if key not in self.page_order:
                continue
            widget = getattr(entry,"widget",None)
            if widget is None:
                continue
            # 只按「这次真的加载到了数据」判断，不看 .cache 里记住的勾选：
            # 以前肉鸽用 remembered 判断，结果勾过 rogue_1 但这次没加载时，
            # 导航里留着「傀影肉鸽」却是空的（踩过）。现在每季各灌一份，计数是准的。
            show = key in loaded
            widget.setVisible(show)
            # 把判断结果记录在页面对象上：诊断脚本/后续逻辑直接读这个，
            # 不用去猜 qfluentwidgets 的导航控件树
            self.pages[key].nav_visible = show
            handled.add(key)
            if show:
                visible.append(key)

            # 把判断结果记录在页面对象上：诊断脚本/后续逻辑直接读这个，
            # 不用去猜 qfluentwidgets 的导航控件树
            self.pages[key].nav_visible = show
            handled.add(key)
            if show:
                visible.append(key)
        if not handled:
            # 拿不到注册表（换了 QFluentWidgets 版本）：退回「不过滤」，
            # 宁可不隐藏，也不能把导航弄坏
            print("[量角器]读不到导航注册表，跳过显隐过滤")
            return []
        self.nav_sections = [key for key in self.page_order if key in visible]
        if not self.nav_sections:
            # 加载项全被隐藏了：至少留一个，别让导航空着
            self.nav_sections = [key for key in self.page_order if key in loaded]
            for key in self.nav_sections:
                self.pages[key].nav_visible = True
                entry = registry.get(key)
                if entry is not None and getattr(entry,"widget",None) is not None:
                    entry.widget.setVisible(True)
        print(f"[量角器]导航显示：{self.nav_sections}")
        return self.nav_sections

    def _make_settings_page(self):
        '''设置页（外观 / 数据 / 配色 / 关于）：见 ui/qt_settings_page.py'''
        # 逐项取色页仍然是独立的 QWidget（35 个 token 的取色列表），
        # 设置页的「配色」分区里放一个入口按钮切过去。
        try:
            from ui.qt_colors_page import ColorsPage
            self.colors_page = ColorsPage(self)
            # 关键：逐项取色页没有自己的布局位置（不挂在任何 layout 里），
            # 父控件一显示它就会以默认几何盖在当前页上面（实测会把整个内容区盖住）。
            # 它不是导航项，只在设置页点「逐项颜色」时才挂到 stack 上显示。
            self.colors_page.setVisible(False)
        except Exception as error:
            print("[量角器]颜色页加载失败："+str(error))
            self.colors_page = None
        try:
            from ui.qt_settings_page import SettingsPage
            self.settings_page = SettingsPage(self)
            return self.settings_page
        except Exception as error:
            print("[量角器]设置页加载失败："+str(error))
            traceback.print_exc()
            self.settings_page = None
            return self._make_action_page(
                "设置","settings",
                "设置页没能加载，可以直接改 config.json。",
                "打开配置文件",self._open_config_file)

    def _make_ai_page(self):
        '''AI 助手页：配置 + 缓存统计：见 ui/qt_ai_page.py'''
        try:
            from ui.qt_ai_page import AIPage
            self.ai_page = AIPage(self)
            return self.ai_page
        except Exception as error:
            print("[量角器]AI 页加载失败："+str(error))
            traceback.print_exc()
            self.ai_page = None
            return self._make_action_page(
                "AI 助手","ai",
                "AI 设置页没能加载，可以用侧栏里的「AI 设置」按钮。",
                "打开 AI 设置",self.open_ai_settings)

    def _open_config_file(self):
        import os
        import bootstrap
        path = os.path.abspath(bootstrap.CONFIG_PATH)
        try:
            os.startfile(os.path.dirname(path))
        except Exception:
            QMessageBox.information(self.window,"配置文件位置",path)

    def _make_theme_page(self):
        '''兼容旧代码/诊断脚本：给出设置页并切到「外观」分区'''
        page = getattr(self,"settings_interface",None)
        settings_page = getattr(self,"settings_page",None)
        if settings_page is not None:
            settings_page.show_section("appearance")
        return page

    def _make_colors_page(self):
        '''兼容旧代码/诊断脚本：给出设置页并切到「配色」分区'''
        page = getattr(self,"settings_interface",None)
        settings_page = getattr(self,"settings_page",None)
        if settings_page is not None:
            settings_page.show_section("colors")
        return page

    def _make_theme_page(self):
        page = QWidget()
        page.setObjectName("theme")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36,28,36,28)
        layout.setSpacing(14)
        layout.addWidget(TitleLabel("外观",page))
        text = BodyLabel("选择界面明暗。跟随系统时会随 Windows 的浅色/深色设置自动切换。",page)
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addSpacing(6)
        row = QHBoxLayout()
        row.setSpacing(8)
        for value,label in [("auto","跟随系统"),("light","浅色"),("dark","深色")]:
            button = PushButton(label,page)
            button.setFixedWidth(140)
            button.setFixedHeight(36)
            button.clicked.connect(lambda _=False,chosen=value: self.set_theme(chosen))
            row.addWidget(button)
        row.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(1)
        return page

    def _make_action_page(self,title,key,description,button_text,callback):
        page = QWidget()
        page.setObjectName(key)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36,28,36,28)
        layout.setSpacing(14)
        heading = TitleLabel(title,page)
        layout.addWidget(heading)
        text = BodyLabel(description,page)
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addSpacing(6)
        button = PrimaryPushButton(button_text,page)
        button.setFixedWidth(200)
        button.setFixedHeight(36)
        button.clicked.connect(callback)
        layout.addWidget(button)
        layout.addStretch(1)
        return page

    def _build_ai_panel(self):
        try:
            from ui.qt_ai_sidebar import AISidebar
        except Exception as error:
            print("[量角器]AI 侧边栏不可用："+str(error))
            return
        # 侧栏只创建一个实例，切页时在「侧栏插槽」之间搬（见 _attach_sidebar）。
        # 不这么做的话只有第一个页面有侧栏，后面的选项卡点「AI 侧栏」是没反应的。
        first = self.pages[self.page_order[0]]
        self.ai_panel = AISidebar(self)
        self.ai_panel.setWindowFlags(Qt.Widget)
        self.ai_panel.setWindowFlag(Qt.Window,False)
        first.sidebar_slot.mount(self.ai_panel)
        visible = bootstrap.config_get("sidebar","visible",None)
        self._sidebar_user_hidden = bool(visible is False)
        self.ai_panel.setVisible(not self._sidebar_user_hidden)

    def _find_page_of_widget(self,widget):
        for key,page in self.pages.items():
            if page is widget:
                return page
        return None

    def _current_page(self):
        widget = self.window.stackedWidget.currentWidget()
        page = self._find_page_of_widget(widget)
        if page is not None:
            return page
        # 非数据页（AI 设置 / 重新加载）时，回到上一次的数据页
        return self.active_page

    def _on_page_changed(self,index):
        widget = self.window.stackedWidget.widget(index)
        page = self._find_page_of_widget(widget)
        if page is None:
            # 非数据页（颜色/外观/设置）：把侧栏收起来，别悬在别的页上
            if self.ai_panel is not None:
                self.ai_panel.setVisible(False)
                # 侧栏里还留着上一个数据页的片段卡片会让人误以为它属于当前页，
                # 所以顺带清空内容（回到「未选择条目」），而不是只藏起来。
                self.ai_panel.set_item(None,None,None)
            return
        self.active_page = page
        page.ensure_loaded()
        # 标题带上当前页名：多页/多窗口时一眼能看出在看哪一类数据
        self.set_busy("")
        if getattr(page,"colors_dirty",False):
            page.colors_dirty = False
            page.restyle()
            if page.current is not None:
                page.restyle_directory()
        self._attach_sidebar(page)
        panel = self.ai_panel
        if panel is not None and page.current is not None:
            panel.set_item(page.current,page.translation,page.raw)

    def _balance_sidebar_space(self,page):
        '''按「当前可用宽度」重新分配三栏

        之前的问题：打开侧栏时用固定像素去减，结果把目录挤到 400+ 而译文只剩一点；
        恢复宽度也存在 _sidebar_width 里，窗口一改大小就错位。
        现在统一按比例算，跟窗口宽度无关：
          收起：列表 20% + 译文 80%（侧栏 0）
          展开：列表 20% + 译文 50% + 侧栏 30%
        '''
        slot = getattr(page,"sidebar_slot",None)
        splitter = getattr(page,"splitter",None)
        if slot is None or splitter is None:
            return
        total = sum(splitter.sizes())
        if total <= 0:                      # 还没布局过，用视口宽度估一个
            total = max(self.window.width() - 120,600)
        panel = self.ai_panel
        shown = panel is not None and panel.isVisible()
        if shown:
            list_w = max(int(total * 0.20),160)
            side_w = max(int(total * 0.30),260)
            splitter.setSizes([list_w,max(total - list_w - side_w,240),side_w])
        else:
            list_w = max(int(total * 0.20),160)
            splitter.setSizes([list_w,total - list_w,0])
        slot.was_open = shown

    def _attach_sidebar(self,page):
        '''把侧栏搬到当前页的插槽里（任何页面都能用 AI 侧栏）'''
        panel = self.ai_panel
        if panel is None:
            return
        slot = getattr(page,"sidebar_slot",None)
        if slot is None:
            return
        if panel.parent() is not slot:
            for other in self.pages.values():
                other_slot = getattr(other,"sidebar_slot",None)
                if other_slot is not None and other_slot.sidebar is panel:
                    other_slot.take_sidebar()
            slot.mount(panel)
        # 侧栏的最小宽度只在它自己身上限制（插槽必须允许被拖到 0，否则收起时会留一条缝）
        saved = bootstrap.config_get("sidebar","width",None)
        minimum = 280
        try:
            minimum = max(int(saved),240) if saved else 280
        except (TypeError,ValueError):
            minimum = 280
        panel.setMinimumWidth(minimum)
        slot.setMinimumWidth(0)
        # 让「译文区」和「侧栏」一起分摊多余宽度；否则放大窗口时侧栏不会跟着变宽
        page.splitter.setStretchFactor(0,0)
        page.splitter.setStretchFactor(1,1)
        page.splitter.setStretchFactor(2,1)
        panel.setVisible(not self._sidebar_user_hidden)
        if not self._sidebar_user_hidden:
            self._balance_sidebar_space(page)
        if getattr(page,"ai_button",None) is not None:
            page.ai_button.setChecked(not self._sidebar_user_hidden)

    def _restore_geometry(self):
        size = self._wanted_size()
        self.window.resize(size.width(),size.height())
        # 窗口位置也跟着存（多显示器 / 大屏用户不用每次自己挪）
        window_cfg = bootstrap.config_get("window",None) or {}
        position = window_cfg.get("pos")
        if isinstance(position,list) and len(position) == 2:
            try:
                self.window.move(int(position[0]),int(position[1]))
            except Exception:
                pass
        # 恢复每个页面的分栏比例（只接受合法值，见 save_layout 的校验）
        for key,page in self.pages.items():
            sizes = bootstrap.config_get("splitters",key,None)
            if self._valid_sizes(sizes):
                page.splitter.setSizes([int(value) for value in sizes])
        if bool(window_cfg.get("maximized",False)):
            QTimer.singleShot(0,self.window.showMaximized)

    @staticmethod
    def _valid_sizes(sizes):
        '''分栏尺寸是否可信：必须是 3 段、都非负、总宽够大

        以前会把 [45,45,0] 这种「还没布局就被存下来」的垃圾值原样塞回去，
        结果窗口一开就把列表挤成一条缝。
        '''
        if not isinstance(sizes,list) or len(sizes) != 3:
            return False
        try:
            values = [int(value) for value in sizes]
        except (TypeError,ValueError):
            return False
        if values[2] < 0 or sum(values) < 400:
            return False
        if values[0] < 60 or values[1] < 60:
            return False
        return True

    def save_layout(self):
        # 最大化时记「还原后的大小」，否则下次启动会以最大化尺寸当普通尺寸
        maximized = bool(self.window.isMaximized())
        size = (self.window.normalSize() if maximized else self.window.size())
        bootstrap.config_set("window","size",[size.width(),size.height()],save=False)
        position = self.window.pos()
        bootstrap.config_set("window","pos",[position.x(),position.y()],save=False)
        bootstrap.config_set("window","maximized",maximized,save=False)
        splitters = {}
        for key,page in self.pages.items():
            if page.splitter.count() != 3:
                continue
            sizes = page.splitter.sizes()
            if self._valid_sizes(sizes):
                splitters[key] = sizes
        if splitters:
            bootstrap.config_set(None,"splitters",splitters,save=False)
        if self.ai_panel is not None:
            bootstrap.config_set("sidebar","visible",self.ai_panel.isVisible(),save=False)
            bootstrap.config_set("sidebar","width",self.ai_panel.width(),save=False)
            self.ai_panel.save_settings()
        bootstrap.save_config()

    # ----------------------------------------
    # 目录与条目
    # ----------------------------------------
    def load_directory(self,data_type,data_dict,section_key=None):
        '''把一张数据表灌进对应的页面

        section_key 给出时只灌那一页（六个肉鸽季度共用 data_type="rogue_item"，
        必须按页区分，否则六个季度会互相覆盖/混在一起）。
        重复调用是安全的：同一个页面先清空再重建，不会出现重复条目。
        '''
        if section_key is not None:
            target_pages = [self.pages[section_key]] if section_key in self.pages else []
        else:
            target_pages = [page for page in self.pages.values() if page.data_type == data_type]
        if not target_pages:
            return
        for page in target_pages:
            page.items = []
            page.filtered = []
            self._reset_page_rows(page)
        counts = getattr(self,"item_counts",None)
        if counts is None:
            counts = self.item_counts = {}
        added = 0
        for data_key,data_reference in data_dict.items():
            if getattr(data_reference,"hidden",False):
                continue
            item = ProtractorItem(self.directory_index,data_type,data_key,data_reference)
            self.directory_index += 1
            added += 1
            for page in target_pages:
                page.add_item(item)
        for page in target_pages:
            counts[page.section_key] = added

    def _reset_page_rows(self,page):
        '''把一页的目录控件清空（数据重灌时用；懒加载标记也跟着复位）'''
        page.loaded = False
        try:
            page.directory.clear()
        except Exception:
            pass
        page.update_count()

    def current_page(self):
        return self._current_page()

    def show_selected(self,page):
        '''目录里选中了某一条：译文有缓存就直接上屏，没有就丢给后台线程翻

        这样「切换条目」不再阻塞界面——译文模板动辄上千个节点，以前是同步翻的。
        '''
        item = page.current_item()
        if item is None or item is page.current:
            return
        page.current = item
        page.displaying = item.full_key
        self.link_stacks = []
        if not item.data_reference:
            page.set_pending(0)
            self.on_item_changed(item)
            return
        cached = self.translation_cache.get(item.full_key)
        if cached is not None:
            self._display_translation(page,item,cached[0],cached[1])
            return
        page.set_pending(0)
        self.on_item_changed(item)
        self.load_item_async(page,item)

    def load_item_async(self,page,item):
        '''后台翻译一个条目（同一时刻只跑一个，避免快速上下移动时堆积请求）'''
        if self._item_request_key is not None:
            self._cancel_item_worker()
        self._item_request_key = item.full_key
        worker = ItemTranslateWorker(item.full_key,item.data_type,item.data_reference,
                                     parent=self.window)
        self.active_item_worker = worker
        self.item_workers[item.full_key] = worker
        worker.finished_ok.connect(self._on_item_translated)
        worker.failed.connect(self._on_item_failed)
        worker.finished.connect(lambda key=item.full_key: self._cleanup_item_worker(key))
        self.set_busy(f"正在翻译 {item.full_key}…")
        worker.start()

    def _display_translation(self,page,item,translation,raw):
        if translation is None:
            if isinstance(raw,(dict,list)):
                page.show_raw(raw)
            page.show_origin(raw)
        else:
            page.show_translation(translation)
            page.show_origin(raw)
        page.set_pending(page.pending_count(translation))
        self.on_item_changed(item)

    def _on_item_translated(self,item_key,translation,raw):
        if item_key != self._item_request_key:
            return                           # 用户已经切走了，丢掉过期结果
        self.translation_cache[item_key] = (translation,raw)
        page = self._current_page()
        if page is None or page.current is None or page.current.full_key != item_key:
            return
        self.set_busy("")
        self._display_translation(page,page.current,translation,raw)

    def _on_item_failed(self,item_key,message):
        if item_key != self._item_request_key:
            return
        print(f"[量角器]翻译 {item_key} 失败：{message}")
        self.set_busy("")
        page = self._current_page()
        if page is None or page.current is None or page.current.full_key != item_key:
            return
        page.show_error_node(f"{item_key} 翻译失败：{message}")
        page.set_pending(0)
        self.notify("翻译失败",f"{item_key} 无法解析，可查看命令行的详细信息","error")
        self.on_item_changed(page.current)

    def _cleanup_item_worker(self,item_key):
        '''只在 finished 里清引用：线程还在跑时被 GC 会让整个进程 abort'''
        worker = self.item_workers.pop(item_key,None)
        if worker is not None and self.active_item_worker is worker:
            self.active_item_worker = None

    def _cancel_item_worker(self):
        worker = self.active_item_worker
        self._item_request_key = None
        self.active_item_worker = None
        if worker is None or getattr(self,"_closing",False):
            return
        try:
            worker.wait(5000)                # 已经在收尾时不再阻塞等待
        except Exception:
            pass

    def set_busy(self,text):
        '''顶栏状态：翻译中提示（空字符串表示清除，并带上当前页名）'''
        if text:
            self.window.setWindowTitle(f"{APP_TITLE} - {text}")
            return
        page = self._current_page()
        name = getattr(page,"title","") if page is not None else ""
        self.window.setWindowTitle(f"{APP_TITLE} - {name}" if name else APP_TITLE)

    def on_item_changed(self,item):
        '''条目切换后刷新 AI 侧栏

        注意：调用方可能是「非数据页」（例如筛选结果为空时），
        这时 _current_page() 会回退到上一次的数据页——如果那个页不是 item 所在的页，
        侧栏就会显示错配的内容。所以这里以 item 的 full_key 为准做一次校验。
        '''
        if self.ai_panel is None:
            return
        page = self._current_page()
        if page is None:
            self.ai_panel.set_item(item,None,None)
            return
        if item is not None and page.current is not None and item is not page.current:
            # item 不属于当前页：只更新「当前条目」信息，不搬那页的译文
            self.ai_panel.set_item(item,None,None)
            return
        self.ai_panel.set_item(item,page.translation,page.raw)

    # 条目 id → 去哪一页 / 用哪张表 / 用哪个翻译函数
    # （放在类里是为了让 display_by_id 与 link_jump 共用同一张表，别再各写一遍 if-elif）
    # 肉鸽六季的表是分开存的，所以不在这里写死，走 _resolve_rogue() 现查。
    ID_SOURCES = (
        ("buff","buff",bena.BUFF_TABLE,bena.BUFF_KEYS,anne.translate_whole_buff),
        ("buff_template","buff_template",bena.BUFF_TEMPLATE_DATA,bena.BUFF_TEMPLATE_KEYS,
         anne.translate_whole_buff_template),
        ("global_buff","global_buff",bena.GLOBAL_BUFF_DUMMY,bena.GLOBAL_BUFF_KEYS,
         anne.translate_whole_global_buff),
    )

    def _resolve_rogue(self,category,key):
        '''肉鸽物品：在六个季度里找 key，返回 (页名, 类型, key, 译文, 原文)

        每个季度一张表，所以得逐季查；找到哪季就回哪一页（页面标题才和内容对得上）。
        '''
        if category not in ("","rogue_item"):
            return None
        # 季度与条目 key 都从数据里来：新季度加了也不用改代码。
        # 先按 key 前缀直接定位季度（快），定位不到再逐季查（兼容键名没有季度前缀的情况）。
        seasons = list(bena.roguelike_seasons())
        guess = bena.roguelike_season_of(key)
        if guess in seasons:
            seasons = [guess] + [item for item in seasons if item != guess]
        for season in seasons:
            table = bena.roguelike_season_table(season)
            if key not in table:
                continue
            obj = table[key]
            raw = [obj.item_info,obj.item_data] if obj.has_effect else obj.item_info
            return season,"rogue_item",key,anne.translate_whole_rogue_item(obj),raw
        return None

    def _resolve_id(self,item_id):
        '''把 "类型.key" 解析成 (页名, 类型, key, 译文, 原文)；找不到返回 None

        category 为空时按 ID 逐个类型试（与旧行为的「不带前缀也能查」一致）。
        '''
        category = ""
        key = item_id
        if "." in item_id:
            category,key = item_id.split(".",1)
        for section,data_type,table,keys,translator in self.ID_SOURCES:
            if category not in ("",data_type):
                continue
            if key not in keys:
                continue
            obj = table[key]
            if hasattr(obj,"get_raw_data"):
                raw = f'"{obj.buff_key}" :' + obj.get_raw_data()
            else:
                raw = [obj.item_info,obj.item_data] if obj.has_effect else obj.item_info
            return section,data_type,key,translator(obj),raw
        return self._resolve_rogue(category,key)

    def display_by_id(self,item_id=""):
        '''按 "类型.key" 展示某条目（--id 参数与链接转跳都走这里）

        修掉两个老问题：
        1. 以前用 full_key.endswith("." + item_id) 找目录行，"buff_template.palsy[stack]"
           这类 key 里本来就有点的会误命中别的类型；
        2. 目标行不在当前页时把译文写到了当前页上（页面与内容对不上）。
        现在：先解析出「这条属于哪一页」，切过去，再按 full_key 精确匹配目录行。
        '''
        resolved = self._resolve_id(item_id)
        if resolved is None:
            return False
        section,data_type,key,translation,raw = resolved
        target_page = self.pages.get(section)
        if target_page is None:
            return False
        if section not in getattr(self,"nav_sections",[]):
            # 这种数据本次没加载（左侧导航里被隐藏了）：仍然可以切过去看（页面已注册），
            # 只提醒一句，让用户知道为什么导航里没有它。
            self.notify("这种数据没有加载",
                        f"{section} 不在本次加载项里，可在「设置 → 数据 → 选择加载内容」里加上",
                        "warn")
        self.window.switchTo(target_page)
        target_page.ensure_loaded()          # 懒加载：要用目录找行就得先把这一页填上
        tab = target_page.tabs.currentIndex()
        if not target_page.select_key(f"{data_type}.{key}"):
            # 目录里没有这一行（例如被隐藏的数据）：直接展示，不让界面停在空页
            target_page.current = ProtractorItem(-1,data_type,key,None)
            target_page.current.display_name = key
            target_page.displaying = target_page.current.full_key
            self.link_stacks = []
            self.translation_cache[target_page.current.full_key] = (translation,raw)
            target_page.show_translation(translation)
            target_page.show_origin(raw)
            target_page.set_pending(target_page.pending_count(translation))
            self.on_item_changed(target_page.current)
        # 精确选中目录行时，show_selected 已经把当前条目与侧栏都刷好了
        target_page.tabs.setCurrentIndex(tab)
        return True

    # ----------------------------------------
    # 链接 / 复制 / PRTS
    # ----------------------------------------
    def link_jump(self,page,link):
        '''点译文里的 <引用> 转跳：跨类型时会切到目标所在页，并按「页面 + 条目」记返回栈

        以前无论目标属于哪一页，都把译文写到当前页上（内容与页面错位），
        返回栈也只存 full_key、丢了页信息，跨类型跳转后就回不去了。
        '''
        resolved = self._resolve_id(link)
        if resolved is None:
            # 找不到对应条目：退回「在当前页搜索这个 key」
            self.search_by(link.split(".",1)[-1])
            return
        section,data_type,key,translation,raw = resolved
        target_page = self.pages.get(section) or page
        # 返回栈：重复跳到同一目标时回退到那一步，否则把「当前所在位置」压进去
        marker = f"{section}.{key}"
        if marker in self.link_stacks:
            index = self.link_stacks.index(marker)
            self.link_stacks = self.link_stacks[:index]
        elif page.current is not None:
            self.link_stacks.append(page.current.full_key)
        # 切页 + 精确选中目标行，整条链路（当前条目 / 侧栏 / AI 侧栏）都交给它刷新
        if not self.display_by_id(link):
            return
        # display_by_id 是「像刚打开一样」的直接展示（不带面包屑），
        # 所以这里按返回栈重放一次译文，把「> A > B」这一行补上
        self.link_stacks.append(marker)
        target_page = self.pages.get(section) or page
        if target_page.current is not None and target_page.translation is not None:
            target_page.show_translation(target_page.translation,self.link_stacks)

    def open_prts(self,page_name):
        import webbrowser
        webbrowser.open("https://prts.wiki/w/"+page_name)

    def copy(self,given_text):
        self.app.clipboard().setText(given_text)
        self.notify("已复制",given_text[:60])

    def copy_all(self):
        page = self._current_page()
        if page is not None:
            self.copy(page.renderer.to_text())

    def copy_current_line(self):
        page = self._current_page()
        if page is not None:
            item = page.tree.currentItem()
            if item is not None:
                self.copy(item.text(0))

    # ----------------------------------------
    # AI
    # ----------------------------------------
    def tree_item_at_path(self,node_path):
        page = self._current_page()
        if page is None:
            return None
        return page.item_at_path(node_path)

    def locate_node(self,node_path):
        '''在译文树里定位某一行：先展开所有祖先，再选中并滚动过去

        返回 False 表示当前译文树里没有这一行（例如 AI 应用之后整条被重新翻译过）。
        '''
        page = self._current_page()
        if page is None or node_path is None:
            return False
        tree_item = page.item_at_path(node_path)
        if tree_item is None:
            return False
        page.tabs.setCurrentIndex(0)
        parent = tree_item.parent()
        tree_item.setExpanded(True)
        while parent is not None:
            parent.setExpanded(True)
            parent = parent.parent()
        page.tree.setCurrentItem(tree_item)
        page.tree.scrollToItem(tree_item)
        return True

    def refresh_pending(self):
        '''AI 写回译文后刷新「N 处待译」计数'''
        page = self._current_page()
        if page is None:
            return
        page.set_pending(page.pending_count(page.translation))

    def apply_ai_translation(self,tree_item,translation,origin_text=None):
        '''把 AI 译文写回译文树的某个节点（只改显示，不动引擎数据）'''
        if tree_item is None:
            return
        page = self._current_page()
        node_path = tree_item.data(0,ROLE_NODE_PATH)
        if page is not None and node_path is not None:
            page.renderer.apply_ai(node_path,translation,origin_text)
            return
        if origin_text is None:
            origin_text = tree_item.data(0,ROLE_ORIGIN_TEXT) or tree_item.text(0)
        tree_item.setData(0,ROLE_ORIGIN_TEXT,origin_text)
        tree_item.setText(0,translation)
        tree_item.setData(0,ROLE_AI_STATE,"applied")
        tree_item.setForeground(0,ai_color())
        tree_item.setToolTip(0,f"原文：{origin_text}\n（AI 译文，来自侧边栏）")

    def toggle_sidebar(self):
        panel = self.ai_panel
        if panel is None:
            return
        page = self._current_page()
        visible = not panel.isVisible()
        self._sidebar_user_hidden = not visible
        if page is not None:
            self._attach_sidebar(page)          # 先把侧栏搬到当前页，再切显隐
        panel.setVisible(visible)
        if page is not None:
            self._balance_sidebar_space(page)

    def open_ai_settings(self):
        if self.ai_panel is None:
            self.notify("AI 功能不可用","AI 侧栏未能加载，请查看命令行输出","error")
            return
        self.ai_panel.open_settings()

    # ----------------------------------------
    # 顶部提示
    # ----------------------------------------
    def notify(self,title,content="",level="info",duration=2500):
        '''右下角提示条

        每次先关掉上一条：QFluentWidgets 的 InfoBarManager 在**同时存在两条**时会给
        新的一条挂一个 drop 动画，而那个动画只设了 duration、没设 endValue，
        一 start 就打印 `QPropertyAnimation::updateState (pos, InfoBar, ): starting an
        animation without end value`（库自身的 bug，见 info_bar.py:356）。
        我们只需要「一条提示」，先关旧的既避免了这个警告，也不会在角上堆一摞。
        '''
        try:
            previous = getattr(self,"_last_info_bar",None)
            if previous is not None:
                try:
                    previous.close()
                except Exception:
                    pass
                self._last_info_bar = None
            position = InfoBarPosition.BOTTOM_RIGHT
            if level == "error":
                bar = InfoBar.error(title,content,parent=self.window,position=position,duration=5000)
            elif level == "warn":
                bar = InfoBar.warning(title,content,parent=self.window,position=position,duration=4000)
            else:
                bar = InfoBar.success(title,content,parent=self.window,position=position,
                                      duration=duration)
            self._last_info_bar = bar
        except Exception:
            print(f"[量角器]{title}：{content}")

    # ----------------------------------------
    # 启动器通用接口
    # ----------------------------------------
    def prepare_data_dialog(self,missing=None):
        from ui.qt_loader import DataPrepareDialog
        dialog = DataPrepareDialog(self.window)
        ok = dialog.start()
        dialog.wait_worker()
        return ok,("" if ok else (dialog.error_message or "已取消"))

    def set_status(self,stage,current=0,total=0):
        if total and total > 0:
            percent = int(min(current / total,1.0) * 100)
            self.window.setWindowTitle(f"{APP_TITLE} - {stage} {percent}%")
        else:
            self.window.setWindowTitle(f"{APP_TITLE} - {stage}")
        self.app.processEvents()

    def close_loader(self):
        self.window.setWindowTitle(APP_TITLE)

    def show_error(self,title,message):
        QMessageBox.critical(self.window,title,message)

    def confirm_retry(self,title,message):
        '''返回 True 表示「重试」（下载支持断点续传，重试很有意义）'''
        box = QMessageBox(self.window)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(title)
        box.setText(title)
        box.setInformativeText(message + "\n\n下载支持断点续传，重试会接着上次的进度继续。")
        retry = box.addButton("重试",QMessageBox.AcceptRole)
        box.addButton("退出",QMessageBox.RejectRole)
        box.exec()
        return box.clickedButton() is retry

    def ask_reload(self):
        from ui.qt_selector import QtSelector
        selector = QtSelector(parent=self.window,current=None)
        loads = selector.exec()
        if not loads:
            return
        self._cancel_item_worker()
        for page in self.pages.values():
            page.items = []
            page.filtered = []
            page.loaded = False
            page.directory.clear()
            page.current = None
            page.translation = None
            page.renderer.clear()
            page.update_count()
        self.item_counts = {}
        self.directory_index = 0
        bootstrap.save_cache(loads)
        bootstrap.start_with(loads,self)
        # 加载项变了：左侧导航跟着显隐（只隐藏没加载的，不摘除，switchTo 依然可用）
        self.apply_nav_filter()
        first = self.nav_sections[0] if self.nav_sections else None
        if first is not None:
            self.window.switchTo(self.pages[first])
        self.notify("已重新加载","左侧导航已按加载项更新")

    def schedule_screenshot(self,path,attach=False,quit_after=False):
        def _shot():
            try:
                from ui.screenshots import capture_widget, capture_window_hwnd
                capture_widget(self.window,path)
                print("[量角器]截图已保存："+path)
                if attach:
                    attach_path = path.replace(".png","_window.png")
                    capture_window_hwnd(self.window.windowTitle(),attach_path)
                    print("[量角器]真窗截图已保存："+attach_path)
            except Exception as error:
                print("[量角器]截图失败："+str(error))
            finally:
                if quit_after:
                    self.window.close()
        QTimer.singleShot(1500,_shot)

    # ----------------------------------------
    def open(self):
        # 注意：这里不要 setWindowTitle(APP_TITLE)——那会把「标题带当前页名」
        # 的显示抹掉（FluentWindow 改标题还会顺手把自己缩到 sizeHint，见 HANDOVER §7.7）。
        # FluentWindow（无边框窗口）在显示前后会按 sizeHint 试图缩窗口，
        # 所以先把「想要的大小」和「布局至少要多大」都钉住，再显示。
        wanted = self._wanted_size()
        self.window.setMinimumSize(self.window.minimumSizeHint())
        current = self.window.size()
        if current.width() < wanted.width() or current.height() < wanted.height():
            self.window.resize(max(current.width(),wanted.width()),
                               max(current.height(),wanted.height()))
        # 数据已经在 start_with() 里灌好了，此刻才知道「该显示哪些类型」
        self.apply_nav_filter()
        first = self.nav_sections[0] if self.nav_sections else None
        if first:
            self.window.switchTo(self.pages[first])
            self.active_page = self.pages[first]
            self._attach_sidebar(self.pages[first])
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        # 首次显示后再刷一次配色：导航项的文字色、容器底色都是在窗口建好后才定型的
        QTimer.singleShot(0,self._first_paint_refresh)
        return self.app.exec()

    def _first_paint_refresh(self):
        '''第一次真正画出来之后的收尾刷新（导航文字色 / 侧栏底色 / 各页面容器）'''
        try:
            self._apply_colors_to_widgets()
            self.repaint_colors(surfaces_changed=True)
            self.refresh_nav()
        except Exception as error:
            print("[量角器]首次显示后的配色刷新失败："+str(error))

    def _wanted_size(self):
        from PySide6.QtCore import QSize
        window_cfg = bootstrap.config_get("window",None) or {}
        size = window_cfg.get("size")
        if isinstance(size,list) and len(size) == 2:
            return QSize(int(size[0]),int(size[1]))
        return QSize(1360,840)

    def close(self):
        # 先把还在跑的 AI 线程收干净，再退（否则 QThread 被回收时进程会直接 abort）
        self._closing = True
        self.closing = True
        if self.ai_panel is not None:
            try:
                self.ai_panel.shutdown()
            except Exception as error:
                print("[量角器]收尾 AI 线程时出错："+str(error))
        self._shutdown_item_workers()
        self.save_layout()
        self.window.close()

    def _shutdown_item_workers(self):
        '''退出前等所有条目翻译线程结束（含正在跑的那个）'''
        for worker in list(self.item_workers.values()):
            try:
                worker.wait(5000)
            except Exception:
                pass
        self.item_workers = {}
        self.active_item_worker = None
        self._item_request_key = None


def _mono_font():
    font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    font.setPointSize(10)
    return palette.scaled_font(font)


# 缺少 token 时的兜底写在 palette 里；这里只做界面
SIDEBAR_WIDTH_DEFAULT = 400


def _card_qss():
    '''统一的「卡片」外观：底色 + 细描边 + 圆角（列表、树、消息区都一样）

    选中/悬浮态也在这里定死：QFluentWidgets 的 ListWidget 给选中行留了很淡的底色，
    配上我们自己的目录底色几乎看不出来，找当前读到哪一行很费眼。
    「紧凑目录」开关只影响行内边距。
    '''
    try:
        compact = bool(bootstrap.config_get(None,"compact_directory",False))
    except Exception:
        compact = False
    padding = "1px 4px" if compact else "3px 6px"
    return (f"QListWidget, QListView {{ background-color:{palette.hex('surface.card')};"
            f" border:1px solid {palette.hex('surface.border')}; border-radius:6px; }}"
            f"QListWidget::item {{ padding:{padding}; }}"
            f"QListWidget::item:selected {{ background-color:{palette.hex('surface.selected')}; }}"
            f"QListWidget::item:hover {{ background-color:{palette.hex('surface.hover')}; }}")
