'''
AI 侧边栏（Fluent 风格）
选中条目后：
  - 列出「未翻译 / 翻译失败 / 纯英文标识」的片段，逐个点「译」向 AI 要译文，再点「应用」写回译文树
  - 底下可以就当前条目问简单问题（答复被限制得很短）
所有网络请求都在 QThread 里跑，界面不会卡。
'''
import os
import re
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QTextCharFormat
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from PySide6.QtWidgets import QMessageBox

import bootstrap
from ai import api, cache, fragments
from ai.treewalk import find_breadcrumb
from ui import palette
from ui.qt_tree import ROLE_NODE_PATH
from ui.qt_workers import AIAskWorker, AITranslateWorker
from ui.qt_widgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    LineEdit,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    StrongBodyLabel,
    ToolButton,
)

MAX_ROWS = 60


def _chat_split_qss():
    '''片段区/问答区之间的分隔条：跟着配色走的一条细线'''
    line = palette.hex("surface.border")
    hover = palette.hex("state.running")
    card = palette.hex("surface.window")
    return (f"QSplitter#benaChatSplit::handle:vertical {{ background:{card};"
            f" border-top:1px solid {line}; height:6px; margin:0px; }}"
            f"QSplitter#benaChatSplit::handle:vertical:hover {{"
            f" border-top:1px solid {hover}; }}")


# 状态 → 语义 token（颜色全部走 ui/palette.py）
STATE_TOKEN = {
    "idle" : "state.pending",
    "running" : "state.running",
    "ok" : "state.ok",
    "warn" : "state.pending",
    "error" : "state.error",
    "done" : "state.running",
}

# 消息标记：一眼分清谁在说话
TAG_ME = "[我] "
TAG_AI = "[AI] "


class FragmentCard(CardWidget):
    '''一个待译片段：原文 + 译 + 应用'''

    def __init__(self,candidate,group,sidebar,key=None):
        super().__init__(sidebar)
        self.candidate = candidate
        self.group = group
        self.sidebar = sidebar
        self.key = candidate if key is None else key   # 在 sidebar.rows 里的键
        self.ai_text = ""
        self.ai_applied = False      # 是否已经写回译文树（批量应用要跳过）
        self.translating = False
        self.state = "idle"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12,10,12,10)
        layout.setSpacing(6)

        self.title = StrongBodyLabel(candidate,self)
        self.title.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.title.setWordWrap(True)
        self.title.setStyleSheet(palette.qss("text.primary"))
        layout.addWidget(self.title)

        crumb = group[0].breadcrumb_text or ""
        # 面包屑太长会把这一行挤成一团：只留最后两段，超出截断
        parts = [part for part in crumb.split(" > ") if part]
        if len(parts) > 2:
            crumb = "… > " + " > ".join(parts[-2:])
        pieces = [crumb] if crumb else []
        if len(group) > 1:
            pieces.append(f"{len(group)} 处")
        reason = {"mark" : "引擎标记未译","heuristic" : "英文标识","manual" : "手动指定"}.get(
            group[0].reason,group[0].reason)
        pieces.append(reason)
        self.meta = CaptionLabel("　·　".join(pieces),self)
        self.meta.setWordWrap(True)
        self.meta.setStyleSheet(palette.qss("text.secondary"))
        layout.addWidget(self.meta)

        self.result = BodyLabel("",self)
        self.result.setWordWrap(True)
        self.result.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.result)

        row = QHBoxLayout()
        row.setSpacing(6)
        # 按钮短标签：侧栏被拖窄时也不至于把卡片撑爆
        self.translate_button = PushButton("翻译",self)
        self.translate_button.setToolTip("翻译这一条片段")
        self.translate_button.clicked.connect(lambda: sidebar.translate_group(self.key))
        row.addWidget(self.translate_button)
        self.apply_button = PrimaryPushButton("应用",self)
        self.apply_button.setToolTip("把译文写回译文树")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(lambda: sidebar.apply_group(self.key))
        row.addWidget(self.apply_button)
        self.locate_button = ToolButton(self)
        self.locate_button.setToolTip("在译文树里定位这一行")
        try:
            from qfluentwidgets import FluentIcon
            self.locate_button.setIcon(FluentIcon.ZOOM)
        except Exception:
            self.locate_button.setText("定位")
        self.locate_button.clicked.connect(lambda: sidebar.locate_group(self.key))
        row.addWidget(self.locate_button)
        row.addStretch(1)
        layout.addLayout(row)
        self.restyle()

    def minimumSizeHint(self):
        '''允许卡片被压到很窄：否则按钮行的最小宽度会把卡片撑出侧栏'''
        from PySide6.QtCore import QSize
        return QSize(120,60)

    # ----------------------------------------
    def set_state(self,state):
        '''切换卡片状态：左边竖条 + 结果文字的颜色都会跟着变'''
        self.state = state
        self.restyle()

    def set_result(self,text,state=None):
        self.result.setText(text)
        if state:
            self.set_state(state)
        else:
            self.restyle()

    def paintEvent(self,event):
        '''自己画卡片底色/描边/左侧状态条

        以前用 QSS：颜色过渡时每帧 setStyleSheet 会让整块侧栏重新解析样式表，
        几十张卡片一起做必然掉帧。自绘之后刷新只是 update()，逐帧换色也很轻。
        '''
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QColor, QPainter
        token = STATE_TOKEN.get(self.state,"text.primary")
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5,0.5,-0.5,-0.5)
        painter.setBrush(QColor(palette.hex("surface.card")))
        painter.setPen(QColor(palette.hex("surface.border")))
        painter.drawRoundedRect(rect,6,6)
        stripe = QRectF(rect.left() + 1,rect.top() + 1,3,rect.height() - 2)
        painter.setBrush(QColor(palette.hex(token)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(stripe,1.5,1.5)
        painter.end()

    def restyle(self):
        '''按当前状态上色（改配色/主题后会再调一次）'''
        token = STATE_TOKEN.get(self.state,"text.primary")
        self.title.setStyleSheet(palette.qss("text.primary"))
        self.result.setStyleSheet(palette.qss(token))
        self.update()

    def refresh_color(self):
        '''过渡动画期间的轻量重绘：底色/状态条是自绘的，update 即可'''
        self.update()


class AISidebar(QWidget):
    def __init__(self,protractor):
        parent = None
        window = getattr(protractor,"window",None)
        if window is not None:
            parent = window
        super().__init__(parent)
        self.protractor = protractor
        self.item = None
        self.translation = None
        self.fragments = []
        self.groups = {}
        self.manual_groups = {}      # 手动指定（右键「翻译这一行」）的片段，按 manual:: 前缀键存
        self.rows = {}
        self._unshown = []           # 超出 MAX_ROWS 还没建卡片的 (candidate, group)
        self._more_button = None
        self.workers = []
        self.active_stream = None
        self.test_worker = None
        self._streaming = False
        self._batch_running = False
        self._batch_stop = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,10,10,8)
        layout.setSpacing(8)
        self.setObjectName("aiSidebar")
        self.setStyleSheet(palette.qss_container("surface.window",object_name="aiSidebar"))

        # ---- 头部：当前条目的 AI 状态 ----
        self.header_card = CardWidget(self)
        header_card = self.header_card
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(12,8,12,8)
        header_layout.setSpacing(4)
        self.header = BodyLabel("未选择条目",header_card)
        self.header.setWordWrap(True)
        header_layout.addWidget(self.header)

        # 批量动作：整条补译 / 一次性应用（以前只能一条条点，30+ 片段时很折磨）
        batch_row = QHBoxLayout()
        batch_row.setSpacing(6)
        self.translate_all_button = PrimaryPushButton("全部翻译",header_card)
        self.translate_all_button.setToolTip("顺序翻译当前条目的所有待译片段（可随时停止）")
        self.translate_all_button.clicked.connect(self.translate_all)
        batch_row.addWidget(self.translate_all_button)
        self.apply_all_button = PushButton("全部应用",header_card)
        self.apply_all_button.setToolTip("把所有已生成的译文一次性写回译文树")
        self.apply_all_button.setEnabled(False)
        self.apply_all_button.clicked.connect(self.apply_all)
        batch_row.addWidget(self.apply_all_button)
        header_layout.addLayout(batch_row)

        button_row = QHBoxLayout()
        button_row.setSpacing(6)
        self.settings_button = PushButton("AI 设置",header_card)
        self.settings_button.clicked.connect(self.open_settings)
        button_row.addWidget(self.settings_button)
        self.export_item_button = ToolButton(header_card)
        self.export_item_button.setToolTip("把当前条目的译文导出为 Markdown（便于校对/提 PR）")
        try:
            from qfluentwidgets import FluentIcon
            self.export_item_button.setIcon(FluentIcon.DOCUMENT)
        except Exception:
            self.export_item_button.setText("导出条目")
        self.export_item_button.clicked.connect(self.export_item)
        batch_row.addWidget(self.export_item_button)
        self.export_button = ToolButton(header_card)
        self.export_button.setToolTip("导出 AI 译文缓存为 Markdown（方便提 PR 补字典）")
        try:
            from qfluentwidgets import FluentIcon
            self.export_button.setIcon(FluentIcon.SAVE)
        except Exception:
            self.export_button.setText("导出")
        self.export_button.clicked.connect(self.export_cache)
        button_row.addWidget(self.export_button)
        button_row.addStretch(1)
        header_layout.addLayout(button_row)
        layout.addWidget(header_card)

        # ---- 上半：片段列表（可拖动高度）----
        self.upper = QWidget(self)
        upper_layout = QVBoxLayout(self.upper)
        upper_layout.setContentsMargins(0,0,0,0)
        upper_layout.setSpacing(6)
        self.scroll = ScrollArea(self.upper)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setMinimumHeight(60)
        self.container = QWidget()
        # 关键：允许内容比「理想宽度」更窄，否则卡片会按自己的最小宽度把滚动区撑宽，
        # 表现为「按钮被挤出侧栏」。
        self.container.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred)
        self.container.setMinimumWidth(0)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0,0,0,0)
        self.container_layout.setSpacing(8)
        self.container_layout.addStretch(1)
        self.scroll.setWidget(self.container)
        upper_layout.addWidget(self.scroll,1)

        self.empty_label = CaptionLabel("（还没有选中条目）",self.upper)
        self.empty_label.setWordWrap(True)
        upper_layout.addWidget(self.empty_label)
        # 没有待译片段时滚动区会被收起，空状态提示会顶到头部卡片下面、把服务信息挤在最上面，
        # 看着比有片段时还高。加一根弹簧把它压到底部，头部的间距就稳定了。
        upper_layout.addStretch(1)

        # ---- 下半：简单问答（可拖动高度）----
        self.lower = QWidget(self)
        lower_layout = QVBoxLayout(self.lower)
        lower_layout.setContentsMargins(0,0,0,0)
        lower_layout.setSpacing(6)
        self.chat_area = PlainTextEdit(self.lower)
        self.chat_area.setReadOnly(True)
        self.chat_area.setPlaceholderText("可以就当前条目提问，回答会尽量简短。")
        self.chat_area.setMinimumHeight(60)
        lower_layout.addWidget(self.chat_area,1)
        ask_row = QHBoxLayout()
        ask_row.setSpacing(6)
        self.ask_entry = LineEdit(self.lower)
        self.ask_entry.setPlaceholderText("例如：这个 Buff 是做什么的？")
        self.ask_entry.returnPressed.connect(self.ask)
        ask_row.addWidget(self.ask_entry,1)
        self.ask_button = PrimaryPushButton("问",self.lower)
        self.ask_button.setFixedWidth(56)
        self.ask_button.clicked.connect(self.ask)
        ask_row.addWidget(self.ask_button)
        lower_layout.addLayout(ask_row)

        self.status = CaptionLabel("",self)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        # 片段区与问答区用可拖动分隔条接在一起：上下两块各自贴边，
        # 中间那条线可以拖（比例记在 config.json 的 sidebar.split）。
        self.chat_split = QSplitter(Qt.Vertical,self)
        self.chat_split.setObjectName("benaChatSplit")
        self.chat_split.setChildrenCollapsible(False)
        self.chat_split.addWidget(self.upper)
        self.chat_split.addWidget(self.lower)
        self.chat_split.setStretchFactor(0,1)
        self.chat_split.setStretchFactor(1,1)
        self.chat_split.setSizes(self._saved_chat_split() or [320,180])
        self.chat_split.setStyleSheet(_chat_split_qss())
        # 拖动分隔条会持续触发 splitterMoved；落盘用 400ms 防抖，别每像素写一次 config.json
        self._split_save_timer = QTimer(self)
        self._split_save_timer.setSingleShot(True)
        self._split_save_timer.setInterval(400)
        self._split_save_timer.timeout.connect(self.save_settings)
        self.chat_split.splitterMoved.connect(lambda *_: self._split_save_timer.start())
        layout.addWidget(self.chat_split,1)

        self.refresh_config_state()
        self.ask_entry.setEnabled(False)
        self.ask_button.setEnabled(False)
        self.restyle()

    # ----------------------------------------
    def _saved_chat_split(self):
        '''读回上次拖的分隔位置（无效值就返回 None，用默认比例）'''
        value = bootstrap.config_get("sidebar","split",None)
        if isinstance(value,list) and len(value) == 2:
            try:
                sizes = [int(item) for item in value]
            except (TypeError,ValueError):
                return None
            if min(sizes) > 0 and sum(sizes) >= 120:
                return sizes
        return None

    # ----------------------------------------
    # 配色：主题/自定义配色变化后由主窗口调用
    # ----------------------------------------
    def restyle(self):
        self.setObjectName("aiSidebar")
        self.setStyleSheet(palette.qss_container("surface.window",object_name="aiSidebar"))
        # 片段列表的滚动区视口默认是白底（深色下会是一大块白），给它透明，露出侧栏底色
        self.scroll.setStyleSheet(
            "QScrollArea { background:transparent; border:none; }"
            "QScrollArea > QWidget, QScrollArea > QWidget > QWidget { background:transparent; }")
        self.container.setStyleSheet("background:transparent;")
        if getattr(self,"chat_split",None) is not None:
            self.chat_split.setStyleSheet(_chat_split_qss())
        # 聊天区：controls + viewport 都要上色
        self.chat_area.setStyleSheet(
            palette.qss_text_view("surface.inset","text.primary","surface.border"))
        palette.apply_text_palette(self.chat_area,"surface.inset","text.primary")
        if getattr(self,"header_card",None) is not None:
            self.header_card.setStyleSheet(
                f"CardWidget {{ background-color:{palette.hex('surface.card')};"
                f" border:1px solid {palette.hex('surface.border')}; border-radius:6px; }}")
        for row in self.rows.values():
            row.restyle()
        self.status.setStyleSheet(
            palette.qss(getattr(self,"status_token","text.muted")))

    def refresh_ai_cards(self):
        '''过渡动画中途的轻量重绘：只更新片段卡片与侧栏底色

        不能每帧都调 restyle()：那会给整块侧栏重设样式表并重建卡片，
        每帧一次必然卡（颜色过渡期间一帧只有 16ms）。
        聊天区是 QSS 上色的，每帧重设一次 QPalette 让它的底色/文字色跟着走。
        '''
        self.update()
        self.container.update()
        self.scroll.viewport().update()
        palette.apply_text_palette(self.chat_area,"surface.inset","text.primary")
        self.chat_area.viewport().update()
        self.status.setStyleSheet(palette.qss(getattr(self,"status_token","text.muted")))
        for row in self.rows.values():
            row.refresh_color()

    def set_status(self,text,token="text.muted"):
        '''底部状态行：按语义上色（就绪/进行中/成功/失败）'''
        self.status_token = token
        self.status.setText(text)
        self.status.setStyleSheet(palette.qss(token))

    # ----------------------------------------
    # 配置状态
    # ----------------------------------------
    def refresh_config_state(self):
        from ai import config as config_module
        config = config_module.load()
        if api.is_ready(config):
            # 只显示模型名，完整地址放悬浮提示里（整行又长又会换行，很难读）
            model = str(config.get("model","")).strip() or "未命名模型"
            self.header.setText(f"AI 服务：{model}")
            self.header.setToolTip(api.describe_provider(config))
            self.header.setStyleSheet(palette.qss("text.secondary"))
            self.settings_button.setText("AI 设置")
        else:
            missing = "、".join(api.missing_fields(config)) or "base_url / model"
            self.header.setText(f"尚未配置 AI 服务（缺少 {missing}）")
            self.header.setToolTip("点击右侧按钮填写服务地址与模型名称")
            self.header.setStyleSheet(palette.qss("state.error"))
            self.settings_button.setText("去设置")
        self.refresh_rows_enabled()

    def _enabled(self):
        return api.is_ready()

    def refresh_rows_enabled(self):
        enabled = self._enabled()
        for row in self.rows.values():
            if not row.translating:
                row.translate_button.setEnabled(enabled)
        self.ask_entry.setEnabled(enabled)
        self.ask_button.setEnabled(enabled)

    # ----------------------------------------
    # 选中条目
    # ----------------------------------------
    def set_item(self,item,translation,raw=None):
        '''切换到某个条目

        单一出口：卡片、空状态提示、底部状态行都在这里一次算清，
        避免中途 return 造成「卡片还在、却同时显示空状态」这种不同步。
        '''
        self.stop_all()
        self._batch_running = False
        self._batch_stop = False
        self.item = item
        self.translation = translation
        self._clear_rows()
        self.chat_area.clear()
        self.set_status("")
        empty_text = ""
        status_text = ""
        status_token = "text.muted"

        if item is None:
            self.header.setText("未选择条目")
            empty_text = "（未选择条目）"
        else:
            self.refresh_config_state()
            display = self.display_name()
            if translation is None:
                empty_text = f"「{display}」没有可翻译的内容（或翻译失败）。"
            else:
                from ai import config as config_module
                heuristic = bool(config_module.get("enable_heuristic_fragments",True))
                collected = fragments.collect_fragments(translation,heuristic=heuristic)
                self.fragments = [f for f in collected if f.needs_translation]
                self.groups = fragments.group_by_candidate(self.fragments)
                if not self.fragments:
                    empty_text = f"「{display}」没有未翻译的片段。"
                else:
                    shown = 0
                    for candidate,group in self.groups.items():
                        if shown >= MAX_ROWS:
                            self._unshown.append((candidate,group))
                            continue
                        self._add_row(candidate,group)
                        shown += 1
                    hidden = len(self._unshown)
                    auto = bool(config_module.get("auto_translate_on_select",False))
                    status_text = (f"共 {len(self.fragments)} 处待译片段"
                                   f"（{len(self.groups)} 个不同片段"
                                   + (f"，先显示前 {shown} 个" if hidden > 0 else "")
                                   + "）"
                                   + ("，已自动开始翻译" if auto
                                      else "，可点「全部翻译」批量处理"))
                    status_token = "state.pending"
                    if hidden > 0:
                        # 以前 60 条之后的片段只计数、看不到也点不到，这里给个入口
                        self._add_more_button(hidden)
                    self.refresh_batch_buttons()

        # ---- 统一收尾：空状态与状态行互斥 ----
        show_empty = bool(empty_text) or item is None
        self.empty_label.setText(empty_text or "（未选择条目）")
        self.empty_label.setVisible(show_empty)
        self.scroll.setVisible(not show_empty)
        if status_text:
            self.set_status(status_text,status_token)
        # 批量按钮的状态一律在这里收口：没有待译片段时（rows 为空）它会自动变灰，
        # 否则会残留上一个条目的「全部翻译（N）」，看着像还能点。
        self.refresh_batch_buttons()

        # 自动翻译第一条（配置开了才做）
        if not show_empty and self.rows and self._enabled():
            from ai import config as config_module
            if bool(config_module.get("auto_translate_on_select",False)):
                first = next(iter(self.rows.values()),None)
                if first is not None:
                    self.translate_group(first.candidate)

    def display_name(self):
        '''给界面用的短名称（不带 [类型 xxx] 这种内部标记）'''
        if self.item is None:
            return "当前条目"
        name = getattr(self.item,"display_name","") or self.item.data_key
        return str(name)

    def item_description(self):
        if self.item is None:
            return "（未选择条目）"
        return api.item_description(self.item.data_type,self.item.data_key,self.item.display_name)

    # ----------------------------------------
    # 片段行
    # ----------------------------------------
    def _clear_rows(self):
        while self.container_layout.count() > 1:
            entry = self.container_layout.takeAt(0)
            widget = entry.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.rows = {}
        self.fragments = []
        self.groups = {}
        self.manual_groups = {}
        self._unshown = []
        self._more_button = None

    def _add_more_button(self,hidden):
        '''「再看 N 个片段」：以前 60 条之后的片段完全没有入口'''
        button = PushButton(f"再看 {hidden} 个片段",self.container)
        button.clicked.connect(self.show_more_rows)
        self.container_layout.insertWidget(self.container_layout.count() - 1,button)
        self._more_button = button

    def show_more_rows(self):
        '''把剩下的片段卡片一次性补齐'''
        pending = list(self._unshown)
        self._unshown = []
        if self._more_button is not None:
            self.container_layout.removeWidget(self._more_button)
            self._more_button.deleteLater()
            self._more_button = None
        for candidate,group in pending:
            if candidate in self.rows:
                continue
            self._add_row(candidate,group)
        self.set_status(f"已显示全部 {len(self.rows)} 个片段","state.pending")
        self.refresh_batch_buttons()

    def _add_row(self,candidate,group,key=None):
        '''加一张片段卡片；key 缺省就是候选文本（手动指定的片段用 manual:: 前缀）'''
        key = candidate if key is None else key
        card = FragmentCard(candidate,group,self,key)
        card.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Maximum)
        self.container_layout.insertWidget(self.container_layout.count() - 1,card)
        self.rows[key] = card
        if not self._enabled():
            card.translate_button.setEnabled(False)
        return card

    # ----------------------------------------
    # 翻译
    # ----------------------------------------
    # ---- 行键：自动收集的片段用候选文本，手动指定的加前缀另开一行 ----
    MANUAL_PREFIX = "manual::"

    @classmethod
    def manual_key(cls,candidate):
        return cls.MANUAL_PREFIX + str(candidate)

    def group_of(self,key):
        '''按行键取回片段组（自动收集的走 groups，手动指定的走 manual_groups）'''
        if str(key).startswith(self.MANUAL_PREFIX):
            return self.manual_groups.get(key)
        return self.groups.get(key)

    def translate_group(self,candidate):
        row = self.rows.get(candidate)
        if row is None or row.translating:
            return
        if not self._enabled():
            QMessageBox.information(self.window(),"尚未配置","请先在 AI 设置里填写服务地址与模型名称。")
            return
        row.translating = True
        row.translate_button.setEnabled(False)
        row.apply_button.setEnabled(False)
        row.set_result("…")
        worker = AITranslateWorker(row.group,self.item_description(),
                                   self.item.data_key if self.item else None,
                                   parent=self.window())
        row.worker = worker
        worker.delta.connect(lambda text,c=candidate: self._on_delta(c,text))
        worker.finished_ok.connect(lambda text,c=candidate: self._on_done(c,text))
        worker.failed.connect(lambda message,c=candidate: self._on_failed(c,message))
        worker.finished.connect(lambda c=candidate: self._cleanup_worker(c))
        self.workers.append(worker)
        worker.start()

    def _on_delta(self,candidate,text):
        row = self.rows.get(candidate)
        if row is None:
            return
        row.ai_text += text
        row.set_result(row.ai_text,"running")

    def _on_done(self,candidate,text):
        row = self.rows.get(candidate)
        if row is None:
            self._advance_batch()
            return
        row.translating = False
        row.translate_button.setEnabled(True)
        if text:
            row.ai_text = text
            row.set_result(text,"ok")
            row.apply_button.setEnabled(True)
            if not self._batch_running:
                self.set_status("译文已生成，可应用到译文树。","state.ok")
        else:
            row.set_result("（模型没有返回内容）","warn")
        self.refresh_batch_buttons()
        self._advance_batch()

    def _on_failed(self,candidate,message):
        row = self.rows.get(candidate)
        if row is None:
            self._advance_batch()
            return
        row.translating = False
        row.translate_button.setEnabled(True)
        if message != "已取消":
            row.set_result("出错了：" + message,"error")
            self.set_status("翻译失败：" + message,"state.error")
        else:
            row.set_result("（已取消）")
        self.refresh_batch_buttons()
        self._advance_batch()

    def _cleanup_worker(self,candidate):
        row = self.rows.get(candidate)
        if row is not None and getattr(row,"worker",None) is not None:
            worker = row.worker
            row.worker = None
            if worker in self.workers:
                self.workers.remove(worker)

    # ----------------------------------------
    # 批量补译 / 批量应用
    # ----------------------------------------
    def refresh_batch_buttons(self):
        '''按当前状态更新两个批量按钮（没配置/没片段/已全部完成时置灰）'''
        ready = self._enabled() and bool(self.rows)
        pending = [key for key,row in self.rows.items()
                   if not row.translating and not row.ai_text]
        self.translate_all_button.setEnabled(ready and bool(pending) and not self._batch_running)
        self.translate_all_button.setText(f"全部翻译（{len(pending)}）" if pending else "全部翻译")
        self.apply_all_button.setEnabled(
            bool([row for row in self.rows.values() if row.ai_text and not row.ai_applied]))

    def translate_all(self):
        '''顺序翻译当前条目的所有待译片段

        顺序执行（一次一个请求）而不是并发：既不会冲击服务端的限流，
        也方便随时点「停止」——批量功能里最难处理的其实是「中途叫停」。
        '''
        if self._batch_running:
            self._batch_stop = True
            self.set_status("正在停止…（等当前这条结束）","state.pending")
            return
        if not self._enabled():
            QMessageBox.information(self.window(),"尚未配置","请先在 AI 设置里填写服务地址与模型名称。")
            return
        if not self.rows:
            return
        self._batch_running = True
        self._batch_stop = False
        self.translate_all_button.setText("停止")
        self._pump_batch()

    def _pump_batch(self):
        '''找下一条还没译的片段继续翻；没有就结束批量'''
        if self._batch_stop:
            self._finish_batch(stopped=True)
            return
        next_key = None
        for key,row in self.rows.items():
            if not row.translating and not row.ai_text:
                next_key = key
                break
        if next_key is None:
            self._finish_batch()
            return
        done = len(self.rows) - len([1 for row in self.rows.values()
                                     if not row.translating and not row.ai_text])
        self.set_status(f"批量翻译中：{done} / {len(self.rows)}","state.running")
        self.translate_group(next_key)

    def _advance_batch(self):
        if not self._batch_running:
            return
        # 让当前这次翻译的事件处理先跑完，再继续下一条
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0,self._pump_batch)

    def _finish_batch(self,stopped=False):
        self._batch_running = False
        self._batch_stop = False
        ok = len([1 for row in self.rows.values() if row.ai_text])
        total = len(self.rows)
        if stopped:
            self.set_status(f"已停止：已完成 {ok} / {total}","state.pending")
        else:
            self.set_status(f"批量翻译完成：{ok} / {total} 条已生成译文，"
                            "可点「全部应用」写回译文树","state.ok")
        self.refresh_batch_buttons()

    def apply_all(self):
        '''把所有已生成的译文一次性写回译文树'''
        keys = [key for key,row in self.rows.items() if row.ai_text and not row.ai_applied]
        if not keys:
            return
        applied = 0
        for key in keys:
            if self.apply_group(key,quiet=True):
                applied += 1
        self.refresh_batch_buttons()
        self.set_status(f"已应用 {applied} 处片段（仅改变显示内容）","state.ok")

    # ----------------------------------------
    # 应用回译文树
    # ----------------------------------------
    def apply_group(self,key,quiet=False):
        row = self.rows.get(key)
        if row is None or not row.ai_text:
            return False
        if self.translation is None or self.protractor is None:
            return False
        applied = 0
        for fragment in row.group:
            if not api.apply_fragment(self.translation,fragment,row.ai_text):
                continue
            applied += 1
            node = api.find_node(self.translation,fragment.node_path)
            tree_item = self.protractor.tree_item_at_path(fragment.node_path)
            if tree_item is not None and node is not None:
                self.protractor.apply_ai_translation(tree_item,node.get("main",""),
                                                     origin_text=node.get("ai_origin"))
        row.apply_button.setEnabled(False)
        row.ai_applied = True
        row.set_result(row.ai_text,"ok")
        # 写回后「N 处待译」要跟着变，否则界面上还挂着已经译完的数量
        refresh = getattr(self.protractor,"refresh_pending",None)
        if callable(refresh):
            refresh()
        if not quiet:
            self.set_status(f"已应用 {applied} 处（仅改变显示内容）","state.ok")
        return True

    def locate_group(self,key):
        '''在译文树里定位这个片段对应的行（先展开祖先，再滚动过去）'''
        row = self.rows.get(key)
        if row is None or not row.group or self.protractor is None:
            return
        node_path = row.group[0].node_path
        locate = getattr(self.protractor,"locate_node",None)
        if callable(locate) and locate(node_path):
            self.set_status("已在译文树中定位到该行","state.running")
        else:
            self.set_status("这一行不在当前译文树里（可能已被重新翻译）","state.pending")

    # ----------------------------------------
    # 简单问答
    # ----------------------------------------
    def ask(self):
        question = self.ask_entry.text().strip()
        if question == "":
            return
        if not self._enabled():
            QMessageBox.information(self.window(),"尚未配置","请先在 AI 设置里填写服务地址与模型名称。")
            return
        self.ask_entry.clear()
        self.append_me(question)
        self.ask_button.setEnabled(False)
        self._streaming = True
        worker = AIAskWorker(question,self.item_description(),self.translation,
                             parent=self.window())
        self.active_stream = worker
        worker.request_started.connect(self.start_answer)
        worker.delta.connect(self._on_ask_delta)
        worker.finished_ok.connect(self._on_ask_done)
        worker.failed.connect(self._on_ask_failed)
        self.workers.append(worker)
        worker.start()

    def _insert_tagged(self,tag,text,tag_color=None):
        '''往消息区写一段带标记的文字（[我] / [AI]）'''
        cursor = self.chat_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        if tag:
            fmt = QTextCharFormat()
            fmt.setFontWeight(QFont.Weight.Bold)
            if tag_color:
                fmt.setForeground(QColor(tag_color))
            cursor.insertText(tag,fmt)
        cursor.insertText(text)
        self.chat_area.setTextCursor(cursor)
        self.chat_area.ensureCursorVisible()

    def append_me(self,text,note=""):
        '''记录用户说的话'''
        self._insert_tagged(TAG_ME,text + (f"　（{note}）" if note else ""),palette.qcolor("chat.me"))
        self._insert_tagged("","\n")

    def start_answer(self):
        '''AI 开始回答：先打上 [AI] 标记，回答内容会接着它流式出现'''
        self._insert_tagged(TAG_AI,"",palette.qcolor("chat.ai"))

    def append_answer(self,text):
        '''把 AI 的一段回答追加在 [AI] 后面'''
        self._insert_tagged("",text)

    def append_note(self,text,color=None):
        '''在回答后面补一条提示（取消/出错）'''
        cursor = self.chat_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(text,fmt)
        self.chat_area.setTextCursor(cursor)
        self.chat_area.ensureCursorVisible()

    def _on_ask_delta(self,text):
        self.append_answer(text)

    def _on_ask_done(self,text):
        self.append_answer("\n\n")
        self.ask_button.setEnabled(True)
        self._streaming = False
        self.active_stream = None

    def _on_ask_failed(self,message):
        if message == "已取消":
            self.append_note("（已取消）\n\n",palette.qcolor("state.pending"))
        else:
            self.append_note(f"（出错了：{message}）\n\n",palette.qcolor("state.error"))
        self.ask_button.setEnabled(True)
        self._streaming = False
        self.active_stream = None

    # ----------------------------------------
    # 右键菜单：翻译 / 解释某一行
    # ----------------------------------------
    def translate_node(self,tree_item):
        node_path = tree_item.data(0,ROLE_NODE_PATH)
        if self.translation is None or node_path is None:
            return
        node = api.find_node(self.translation,node_path)
        if node is None:
            return
        from ai.fragments import Fragment, _split_key_value, _split_marked
        text = node.get("main","")
        content,note = _split_marked(text)
        _key,value = _split_key_value(content)
        candidate = (value or content).strip().strip('"')
        if candidate == "":
            return
        fragment = Fragment(node_path=node_path,text=text,kind="text",
                            reason=note or "manual",candidate=candidate,
                            breadcrumb=find_breadcrumb(self.translation,node_path),
                            needs_translation=True)
        group = [fragment]
        # 手动指定的片段单独存：它不一定属于「自动收集到的待译片段」，
        # 混进 self.groups 会把同名候选的自动分组覆盖掉。
        key = self.manual_key(candidate)
        self.manual_groups[key] = group
        if key not in self.rows:
            self._add_row(candidate,group,key)
        self.empty_label.hide()
        self.translate_group(key)

    def explain_node(self,tree_item):
        node_path = tree_item.data(0,ROLE_NODE_PATH)
        line = tree_item.text(0)
        question = self.ask_entry.text().strip() or "这一行在做什么？"
        self.ask_entry.clear()
        if not self._enabled():
            QMessageBox.information(self.window(),"尚未配置","请先在 AI 设置里填写服务地址与模型名称。")
            return
        self.append_me(question,note=f"针对：{line}")
        worker = AIAskWorker(question,self.item_description(),self.translation,
                             node_path=node_path,line=line,parent=self.window())
        self.active_stream = worker
        worker.request_started.connect(self.start_answer)
        worker.delta.connect(self._on_ask_delta)
        worker.finished_ok.connect(self._on_ask_done)
        worker.failed.connect(self._on_ask_failed)
        self.workers.append(worker)
        worker.start()

    # ----------------------------------------
    # 其它
    # ----------------------------------------
    def export_cache(self):
        try:
            path = cache.export_markdown()
        except Exception as error:
            QMessageBox.information(self.window(),"导出失败",str(error))
            return
        self.set_status("已导出：" + path,"state.ok")
        try:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.success("已导出 AI 译文缓存",path,parent=self.window(),
                            position=InfoBarPosition.BOTTOM_RIGHT,duration=4000)
        except Exception:
            pass

    def export_item(self):
        '''把当前条目的译文导出成 Markdown（含 AI 已应用的标注）

        与「导出缓存」不同：这是整条机制的译文快照，适合贴进文档/讨论；
        只写 .bena_cache/ 下，**绝不**碰 translation/*.json。
        '''
        if self.translation is None or self.protractor is None:
            self.set_status("当前条目没有可导出的译文","state.pending")
            return
        page = self.protractor.current_page() if callable(
            getattr(self.protractor,"current_page",None)) else None
        title = self.display_name()
        item_key = getattr(self.item,"full_key",None) or getattr(self.item,"data_key","") or "item"
        lines = [f"# {title}","",
                 f"- 条目：`{item_key}`",
                 f"- 类型：`{getattr(self.item,'data_type','')}`",
                 f"- 导出时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
                 "",
                 "> 由《贝娜的量角器》导出。AI 补译只影响显示文本，原文始终保留在译文结构里。",
                 "",
                 "```text"]
        if page is not None:
            lines.append(page.renderer.to_text())
        else:
            lines.append(api.translation_snapshot(self.translation))
        lines.append("```")
        text = "\n".join(lines) + "\n"
        try:
            folder = os.path.join(".bena_cache","ai","export")
            os.makedirs(folder,exist_ok=True)
            safe = re.sub(r'[^\w\u4e00-\u9fff.\-]+',"_",str(title))[:60] or "item"
            path = os.path.join(folder,f"item_{safe}_{time.strftime('%Y%m%d_%H%M%S')}.md")
            with open(path,"w",encoding="UTF-8") as file:
                file.write(text)
        except OSError as error:
            QMessageBox.information(self.window(),"导出失败",str(error))
            return
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
        except Exception:
            pass
        self.set_status("已导出（并复制到剪贴板）：" + path,"state.ok")

    def open_settings(self):
        from ui.qt_ai_settings import AISettingsDialog
        dialog = AISettingsDialog(self.window(),on_test=self.run_test)
        if dialog.exec():
            self.refresh_config_state()
            self.set_status("设置已保存，点「翻译」试试。","state.running")

    def run_test(self,config,done_callback):
        '''测试连接：用设置里刚填的参数真跑一次

        注意：worker 必须留一个强引用（挂到 self 上），否则函数一返回就被 GC，
        而 QThread 析构时若还在运行，Qt 会直接 abort 掉整个进程。
        '''
        from ai import config as config_module
        from ai import registry
        missing = config_module.missing_fields(config)
        if missing:
            done_callback(False,"还没填 " + "、".join(missing) + "。")
            return
        self.stop_test()
        registry.reset()
        try:
            registry.get_provider(config,force_new=True)
        except Exception as error:
            done_callback(False,str(error))
            return
        worker = AIAskWorker("这一行在做什么？","测试条目",
                             {"main" : "测试：类：TestBuff"},
                             parent=self.window())
        self.test_worker = worker

        def _done(text):
            done_callback(True,text[:60] or "（连接成功，但模型没返回内容）")

        def _failed(message):
            done_callback(False,message)

        def _cleanup():
            # 一定要等 finished（本轮真正结束）再放引用，否则线程还在跑就被 GC
            if self.test_worker is worker:
                self.test_worker = None

        worker.finished_ok.connect(_done)
        worker.failed.connect(_failed)
        worker.finished.connect(_cleanup)
        worker.start()

    def stop_test(self):
        '''取消并等测试线程收尾，避免线程还在跑就被回收'''
        worker = getattr(self,"test_worker",None)
        if worker is None:
            return
        self.test_worker = None
        try:
            worker.cancel()
        except Exception:
            pass
        worker.wait(10000)

    def save_settings(self):
        '''记住「片段区 / 问答区」的分隔位置（拖分隔条时也会调）'''
        split = getattr(self,"chat_split",None)
        if split is None:
            return
        sizes = split.sizes()
        if len(sizes) == 2 and min(sizes) > 0:
            bootstrap.config_set("sidebar","split",[int(sizes[0]),int(sizes[1])])

    def shutdown(self):
        '''侧栏/窗口关掉之前统一收尾：所有线程先停再放'''
        self.stop_test()
        self.stop_all()
        for worker in list(self.workers):
            try:
                worker.wait(10000)
            except Exception:
                pass
        self.workers = []

    def stop_all(self):
        for worker in list(self.workers):
            try:
                worker.cancel()
            except Exception:
                pass
        self.workers = []
