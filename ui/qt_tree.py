'''
译文树 / 原文树（Qt 控件层）
真正的数据构建在 ui/treemodel.py（不依赖 Qt，可单测）；这里只负责画出来。
配色尽量跟着主题走，这样亮色/暗色主题下都可读。
'''
import os
import sys

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextLayout, QTextOption
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)

from ui import palette
from ui.treemodel import (  # noqa: F401  (对外继续暴露这些名字)
    KIND_AI,
    KIND_ERROR,
    KIND_LINK,
    KIND_NOTE,
    build_lines,
    build_raw,
    extract_copy_options,
    filter_items,
    match_spans,
    merge_spans,
    raw_json_text,
    raw_text,
)

ROLE_LINK = Qt.UserRole + 1
ROLE_NODE_PATH = Qt.UserRole + 2
ROLE_AI_STATE = Qt.UserRole + 3      # "none" / "pending" / "applied"
ROLE_ORIGIN_TEXT = Qt.UserRole + 4   # 被 AI 替换前的原文
ROLE_VISUAL = Qt.UserRole + 5        # (文本, spans, depth)：绘制层要的语义信息
ROLE_MATCH_SPANS = Qt.UserRole + 6   # 目录行的「搜索命中」区间 [(start, end, role), ...]


def format_ranges(text,spans,base_color,role_color=None):
    '''把语义段翻成 QTextLayout 的 FormatRange（一行里多段不同颜色的正解）

    直接用 layout.draw(painter, pos, ranges)：Qt 自己处理换行与逐段着色，
    不用手工算 x 偏移，也就不会出现「两层文字叠在一起」的糊字。
    译文树（NodeDelegate）与目录（TypeColorDelegate）共用这一份实现。

    role_color: 可选回调 role -> QColor；返回 None 时退回主色，
                「搜索命中」这类需要特殊处理（比如加下划线）的场合可以用它。
    '''
    if not spans:
        return []
    ranges = []
    for start,end,role in sorted(spans):
        start = max(0,min(start,len(text)))
        end = max(start,min(end,len(text)))
        if start >= end:
            continue
        color = role_color(role) if role_color is not None else span_color(role)
        fmt = QTextCharFormat()
        fmt.setForeground(color or base_color)
        ranges.append(QTextLayout.FormatRange())
        ranges[-1].start = start
        ranges[-1].length = end - start
        ranges[-1].format = fmt
    return ranges


def link_color():
    return palette.qcolor("value.reference")


def ai_color():
    return palette.qcolor("state.ok")


def depth_color(depth):
    '''层级灰阶：越深越浅，靠明度做结构分级'''
    token = {0 : "text.depth1",1 : "text.depth2",2 : "text.depth3"}.get(depth,"text.depth4")
    return palette.qcolor(token)


def kind_color(kind):
    if kind == KIND_LINK:
        return palette.qcolor("value.reference")
    if kind == KIND_NOTE:
        return palette.qcolor("text.muted")
    if kind == KIND_AI:
        return palette.qcolor("state.ok")
    if kind == KIND_ERROR:
        return palette.qcolor("state.error")
    return None


def span_color(role):
    '''span 的语义角色 → 颜色；未知角色返回 None（保持主色）'''
    return palette.qcolor(role) if palette.is_valid(role) else None


def depth_font(base_font,depth):
    '''第 1 层加粗，做出「主题/细节」的差别（字号缩放由调用方给好 base_font）'''
    if depth > 0 or base_font is None:
        return base_font
    font = type(base_font)(base_font)
    font.setBold(True)
    return font


def apply_tree_font_scale(tree,origin=None):
    '''把当前字号比例应用到译文树（委托字体）与原文面板

    字号变了必须把 NodeDelegate 的折行高度缓存清掉，否则行高还是旧字号算出来的。
    '''
    font = palette.scaled_font(tree.font())
    tree.setFont(font)
    delegate = tree.itemDelegate()
    if delegate is not None:
        delegate._HEIGHT_CACHE.clear()
    if origin is not None:
        origin.setFont(palette.scaled_font(origin.font()))
    tree.viewport().update()


class NodeDelegate(QStyledItemDelegate):
    '''按列宽折行显示整段文本（默认委托会用 … 截断，读机制的时候很难受）

    性能：折行高度算一次就缓存，键是 (文本, 列宽, 字号)；滚动时不再反复测文本。
    '''

    _HEIGHT_CACHE = {}
    _CACHE_LIMIT = 4000

    def _measure(self,text,font,width):
        key = (text,width,font.key())
        cached = self._HEIGHT_CACHE.get(key)
        if cached is not None:
            return cached
        layout = QTextLayout(text,font)
        wrap = QTextOption()
        wrap.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        layout.setTextOption(wrap)
        layout.beginLayout()
        height = 0.0
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(width)
            height += line.height()
        layout.endLayout()
        if len(self._HEIGHT_CACHE) > self._CACHE_LIMIT:
            self._HEIGHT_CACHE.clear()
        self._HEIGHT_CACHE[key] = height
        return height

    def sizeHint(self,option,index):
        text = index.data(Qt.DisplayRole)
        if not text:
            return super().sizeHint(option,index)
        width = option.rect.width()
        if width <= 0:
            width = self.parent().columnWidth(0) if self.parent() else 400
        width = max(width,80)
        height = self._measure(str(text),option.font,width)
        return QSize(int(width),int(height) + 4)

    def paint(self,painter,option,index):
        text = index.data(Qt.DisplayRole)
        if text is None:
            text = ""
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt,index)
        style = opt.widget.style() if opt.widget else QApplication.style()
        opt.text = ""
        try:
            style.drawControl(QStyle.CE_ItemViewItem,opt,painter,opt.widget)

            font = index.data(Qt.FontRole)
            if not font:
                font = opt.font
            visual = index.data(ROLE_VISUAL) or {}
            spans = visual.get("spans") or []
            depth = int(visual.get("depth") or 0)
            font = depth_font(font,depth)

            base_color = to_color(index.data(Qt.ForegroundRole))
            if base_color is None:
                base_color = depth_color(depth)
            if base_color is None:
                base_color = opt.palette.text().color()

            content = option.rect.adjusted(2,1,-4,-1)
            width = max(float(content.width()),80.0)
            layout = QTextLayout(str(text),font)
            wrap = QTextOption()
            wrap.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            layout.setTextOption(wrap)
            layout.beginLayout()
            y = 0.0
            while True:
                line = layout.createLine()
                if not line.isValid():
                    break
                line.setLineWidth(width)
                line.setPosition(QPointF(content.left(),content.top() + y))
                y += line.height()
            layout.endLayout()

            painter.save()
            painter.setClipRect(option.rect)
            painter.setPen(base_color)
            layout.draw(painter,QPointF(0.0,0.0),self._format_ranges(text,spans,base_color))
            # 状态角标：AI 已译（译） / 待译（?）
            state = index.data(ROLE_AI_STATE)
            if state in ("pending","applied"):
                painter.setPen(ai_color() if state == "applied"
                               else palette.qcolor("state.pending"))
                painter.drawText(option.rect.adjusted(0,1,-4,-1),
                                 Qt.AlignTop | Qt.AlignRight,
                                 "译" if state == "applied" else "?")
            painter.restore()
        except Exception as error:  # 绘图层出错不该把整个界面带走
            print("[量角器]节点绘制失败："+str(error))
            try:
                painter.restore()
            except Exception:
                pass

    @staticmethod
    def _format_ranges(text,spans,base_color):
        '''把语义段翻成 QTextLayout 的 FormatRange（实现见模块级 format_ranges）'''
        return format_ranges(text,spans,base_color)


_TREE_WIDGET_OK = None


def tree_widget_supported():
    '''QFluentWidgets 的 TreeWidget 在某些 PySide6/Qt 组合下一显示就崩，
    所以第一次去子进程里探一次并缓存结果（见 tools/probe_treewidget.py）。'''
    global _TREE_WIDGET_OK
    if _TREE_WIDGET_OK is not None:
        return _TREE_WIDGET_OK
    if os.environ.get("BENA_FLUENT_TREE") == "1":
        _TREE_WIDGET_OK = True
        return True
    if os.environ.get("BENA_FLUENT_TREE") == "0":
        _TREE_WIDGET_OK = False
        return False
    try:
        sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from tools.probe_treewidget import run_probe
        _TREE_WIDGET_OK = bool(run_probe())
    except Exception as error:
        print("[量角器]TreeWidget 探测不可用，改用原生 QTreeWidget："+str(error))
        _TREE_WIDGET_OK = False
    return _TREE_WIDGET_OK


def make_tree(parent=None):
    '''译文树控件：优先 Fluent 的 TreeWidget，不可用就退回原生 QTreeWidget

    两者外观差别很小（都是白底圆角 + Fluent 滚动条），但原生版在本机稳定得多。
    '''
    tree = None
    if tree_widget_supported():
        try:
            from qfluentwidgets import TreeWidget
            tree = TreeWidget(parent)
        except Exception:
            tree = None
    if tree is None:
        from PySide6.QtWidgets import QTreeWidget
        tree = QTreeWidget(parent)
    tree = configure_tree(tree)
    # 背景统一到「卡片底色」，避免一个页面里出现好几层不同的白/灰
    try:
        tree.setStyleSheet(_tree_qss())
    except Exception:
        pass
    return tree


def _tree_qss():
    '''树的底色描边 + 展开箭头（Fluent 自带的箭头在深色主题下几乎看不见，自己画）'''
    border = palette.hex("surface.border")
    card = palette.hex("surface.card")
    plus = _arrow_icon(expanded=False)
    minus = _arrow_icon(expanded=True)
    return (f"QTreeWidget, QTreeView {{ background-color:{card};"
            f" border:1px solid {border}; border-radius:6px; }}"
            "QTreeWidget::item { padding:2px 4px; }"
            "QTreeView::branch:has-children:!has-siblings:closed,"
            "QTreeView::branch:closed:has-children:has-siblings {"
            f" image:url({plus}); }}"
            "QTreeView::branch:open:has-children:!has-siblings,"
            "QTreeView::branch:open:has-children:has-siblings {"
            f" image:url({minus}); }}")


_ARROW_CACHE = {}


def _arrow_icon(expanded):
    '''画一个跟着主题走的三角箭头，返回可直接塞进 QSS 的路径（正斜杠，Windows 也认）'''
    key = (expanded,palette.hex("text.secondary"))
    cached = _ARROW_CACHE.get(key)
    if cached:
        return cached.replace("\\","/")
    color = palette.hex("text.secondary")
    if expanded:
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" '
               'viewBox="0 0 12 12"><path d="M2.5 4.2 L6 7.8 L9.5 4.2" fill="none" '
               f'stroke="{color}" stroke-width="1.4" stroke-linecap="round" '
               'stroke-linejoin="round"/></svg>')
        name = "arrow_open.svg"
    else:
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" '
               'viewBox="0 0 12 12"><path d="M4.2 2.5 L7.8 6 L4.2 9.5" fill="none" '
               f'stroke="{color}" stroke-width="1.4" stroke-linecap="round" '
               'stroke-linejoin="round"/></svg>')
        name = "arrow_closed.svg"
    try:
        folder = os.path.join(os.getcwd(),".bena_cache","ui")
        os.makedirs(folder,exist_ok=True)
        path = os.path.join(folder,name)
        with open(path,"w",encoding="utf-8") as file:
            file.write(svg)
        _ARROW_CACHE[key] = path
        return path.replace("\\","/")
    except OSError:
        return ""


def make_list(parent=None):
    '''同理：优先 Fluent 的 ListWidget'''
    try:
        from qfluentwidgets import ListWidget
        return ListWidget(parent)
    except Exception:
        from PySide6.QtWidgets import QListWidget
        return QListWidget(parent)


def configure_tree(tree):
    tree.setColumnCount(1)
    tree.setHeaderHidden(True)
    tree.setWordWrap(True)
    tree.setUniformRowHeights(False)
    tree.setExpandsOnDoubleClick(True)
    tree.setSelectionMode(QAbstractItemView.SingleSelection)
    tree.setContextMenuPolicy(Qt.CustomContextMenu)
    tree.setItemDelegate(NodeDelegate(tree))
    # 表头是隐藏的，QHeaderView.Stretch 不会生效，列宽会停在旧值上（文字被截、右边留白）。
    # 所以直接跟随视口宽度，并把横向滚动条关掉——长句本来就靠折行显示。
    tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    # 逐像素滚动：默认按行滚动时，一个高行会整块跳，看着也顿
    tree.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    _bind_column_width(tree)
    if hasattr(tree,"setBorderVisible"):
        tree.setBorderVisible(True)
    return tree


def _bind_column_width(tree):
    '''让第 0 列始终等于视口宽度'''
    def _apply():
        try:
            tree.setColumnWidth(0,max(tree.viewport().width() - 2,80))
        except Exception:
            pass

    original_resize = tree.resizeEvent

    def resizeEvent(event):
        _apply()
        if original_resize is not None:
            original_resize(event)

    tree.resizeEvent = resizeEvent
    try:
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0,_apply)
    except Exception:
        _apply()


def restyle_tree(tree):
    '''配色/主题变化后重刷树的底色描边'''
    try:
        tree.setStyleSheet(_tree_qss())
        tree.viewport().update()
    except Exception:
        pass


def recolor_tree(tree,items):
    '''配色变化后在原位重刷节点颜色（**不重建树**）

    以前改一次颜色要 show_translation() 重放整棵树：上千个节点重新 new + setText +
    插入，实测 570ms 起步，拖色和切预设时肉眼可见地一顿。
    颜色本来就只存在 ForegroundRole 与委托里，所以只需要按新的 palette 重写颜色，
    结构、展开状态、滚动位置、选中行全部原地不动。

    items: {node_path: QTreeWidgetItem}（TreeRenderer.items）
    '''
    if not items:
        return
    try:
        tree.setUpdatesEnabled(False)
        for item in items.values():
            visual = item.data(0,ROLE_VISUAL) or {}
            kind = None
            if visual.get("kind"):
                kind = visual["kind"]
            elif item.data(0,ROLE_AI_STATE) == "applied":
                kind = KIND_AI
            elif item.data(0,ROLE_LINK):
                kind = KIND_LINK
            if kind in (KIND_LINK,KIND_AI,KIND_NOTE,KIND_ERROR):
                item.setForeground(0,kind_color(kind))
            else:
                item.setForeground(0,depth_color(int(visual.get("depth") or 0)))
    finally:
        tree.setUpdatesEnabled(True)
    tree.viewport().update()


class TreeRenderer:
    '''某一棵树的状态容器（node_path ↔ QTreeWidgetItem 映射、结构体映射）

    译文渲染逻辑写成组合而不是继承，这样 QFluentWidgets 的 TreeWidget
    （shiboken 类型，改不了 __class__）与普通 QTreeWidget 都能用同一套逻辑。
    '''

    def __init__(self):
        self.tree = None
        self.items = {}      # node_path -> QTreeWidgetItem
        self.structs = {}    # node_path -> 译文结构体
        self._expanded_flags = []   # 插入期间攒下的 (item, 是否展开)，插完统一应用

    def bind(self,tree):
        self.tree = tree
        return self

    # ----------------------------------------
    # 查询
    # ----------------------------------------
    def item_at_path(self,node_path):
        return self.items.get(node_path,None)

    def struct_at(self,tree_item):
        return self.structs.get(tree_item.data(0,ROLE_NODE_PATH),None)

    def node_path_of(self,tree_item):
        return tree_item.data(0,ROLE_NODE_PATH)

    # ----------------------------------------
    # 渲染
    # ----------------------------------------
    def clear(self):
        self.tree.clear()
        self.items = {}
        self.structs = {}
        self._expanded_flags = []

    def show_translation(self,struct,link_stacks=None):
        from PySide6.QtWidgets import QTreeWidgetItem
        self.clear()
        root = self.tree.invisibleRootItem()
        if link_stacks:
            crumb = QTreeWidgetItem(root)
            crumb.setText(0,"> " + " > ".join(link_stacks))
            crumb.setForeground(0,palette.qcolor("text.faint"))
            crumb.setFlags(Qt.ItemIsEnabled)
        specs = build_lines(struct)
        # 上千行时逐行插入会反复触发重排/重绘（很卡），先关刷新、插完再开
        self.tree.setUpdatesEnabled(False)
        try:
            for spec in specs:
                self._add(spec,root)
        finally:
            self.tree.setUpdatesEnabled(True)
        self._apply_expanded()

    def show_raw(self,datas):
        self.clear()
        root = self.tree.invisibleRootItem()
        specs = build_raw(datas)
        self.tree.setUpdatesEnabled(False)
        try:
            for spec in specs:
                self._add(spec,root)
        finally:
            self.tree.setUpdatesEnabled(True)
        self._apply_expanded()

    def _apply_expanded(self):
        '''插入结束后再统一展开

        以前是每插完一个节点就 setExpanded()，节点多的时候会产生大量冗余的展开动作
        （QTreeWidgetItem 每次展开都要重算可见行）。折叠状态是显示属性，与结构无关，
        放到插入之后一次性应用即可，结果完全一致。
        '''
        if not self._expanded_flags:
            return
        self.tree.setUpdatesEnabled(False)
        try:
            for item,expanded in self._expanded_flags:
                item.setExpanded(expanded)
        finally:
            self.tree.setUpdatesEnabled(True)
        self._expanded_flags = []

    def _add(self,spec,master):
        from PySide6.QtWidgets import QTreeWidgetItem
        item = QTreeWidgetItem(master)
        item.setText(0,spec.text)
        item.setData(0,ROLE_LINK,spec.link or "")
        item.setData(0,ROLE_NODE_PATH,spec.node_path)
        item.setData(0,ROLE_AI_STATE,"applied" if spec.kind == KIND_AI else "none")
        # 绘制层要的语义信息：整体主色由 kind 决定，段内细节由 spans 决定，depth 决定灰阶
        item.setData(0,ROLE_VISUAL,{"text" : spec.text,
                                    "spans" : list(spec.spans or []),
                                    "depth" : int(spec.depth or 0),
                                    "kind" : spec.kind})
        if spec.ai_origin:
            item.setData(0,ROLE_ORIGIN_TEXT,spec.ai_origin)
        flags = item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if spec.kind == KIND_NOTE:
            flags &= ~Qt.ItemIsSelectable
            item.setForeground(0,kind_color(KIND_NOTE))
        elif spec.kind == KIND_LINK:
            item.setForeground(0,kind_color(KIND_LINK))
            item.setToolTip(0,f"可转跳：{spec.link}")
        elif spec.kind == KIND_AI:
            item.setForeground(0,kind_color(KIND_AI))
            item.setToolTip(0,"AI 译文（原文见侧边栏，或右键用 AI 重新翻译）")
        elif spec.kind == KIND_ERROR:
            item.setForeground(0,kind_color(KIND_ERROR))
        else:
            # 普通节点：建的时候就写死层级色，切主题/改配色时重建即可立刻生效
            # （不依赖绘制时的主题，避免「重画用的还是旧主题色」这类时序问题）
            item.setForeground(0,depth_color(spec.depth))
        item.setFlags(flags)
        self.items[spec.node_path] = item
        self.structs[spec.node_path] = spec.node
        for child in spec.children:
            # 注意：这里必须递归插完，子节点不会因为父节点还折叠着而丢掉
            self._add(child,item)
        if spec.children:
            # 展开时机统一推后（见 _apply_expanded）
            self._expanded_flags.append((item,bool(spec.expanded)))

    def apply_ai(self,node_path,text,origin=None):
        '''把一行标成「AI 已译」（颜色 + 角标 + 悬浮原文）'''
        item = self.items.get(node_path)
        if item is None:
            return None
        item.setText(0,text)
        item.setData(0,ROLE_AI_STATE,"applied")
        item.setForeground(0,kind_color(KIND_AI))
        item.setData(0,ROLE_VISUAL,{"text" : text,
                                    "spans" : [],
                                    "depth" : int((item.data(0,ROLE_VISUAL) or {}).get("depth") or 0)})
        if origin:
            item.setData(0,ROLE_ORIGIN_TEXT,origin)
            item.setToolTip(0,f"原文：{origin}\n（AI 译文，来自侧边栏）")
        return item

    def select_path(self,node_path):
        item = self.items.get(node_path)
        if item is not None:
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)
        return item

    def to_text(self,only_selected=None):
        lines = []

        def walk(item,depth):
            lines.append("    " * depth + item.text(0))
            for index in range(item.childCount()):
                walk(item.child(index),depth + 1)

        if only_selected is not None:
            walk(only_selected,0)
        else:
            for index in range(self.tree.topLevelItemCount()):
                walk(self.tree.topLevelItem(index),0)
        return "\n".join(lines)


def to_color(value):
    '''把模型里拿到的 ForegroundRole 安全地转成 QColor（拿不到就返回 None）'''
    if value is None:
        return None
    if isinstance(value,QColor):
        return value
    try:
        color = QColor(value)
    except (TypeError,ValueError):
        return None
    if not color.isValid():
        return None
    return color
