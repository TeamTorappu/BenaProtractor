'''
外观 → 颜色：让用户自己调配色
- 预设一键切换（默认 / 明日方舟 / 高对比）
- 每个语义 token 一个取色按钮，改完立刻生效并写进 config.json
- 顶部有「试色板」：直接用真实语义色画几行示例，改完马上能看到效果

颜色分级本身的定义在 ui/palette.py，这里只负责编辑与预览。
'''
import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
try:
    from qfluentwidgets import ColorPickerButton
except ImportError:      # 没装 Fluent 时给个占位，颜色页会走降级分支
    ColorPickerButton = None

from qfluentwidgets import ComboBox, MessageBox

from ui import palette
from ui.qt_widgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    CheckBox,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    StrongBodyLabel,
    TitleLabel,
    ToolButton,
)
# 试色板用的示例（正好覆盖各级语义）
SWATCH = [
    ("text.depth1","Buff 名称（第 1 层）"),
    ("text.depth2","　└ 第 2 层：键值行"),
    ("text.depth3","　　└ 第 3 层：更细的细节"),
    ("text.depth4","　　　└ 第 4 层：最细的细节"),
    ("value.key","持续时间 : "),
    ("value.number","10"),
    ("value.unit"," 秒"),
    ("value.placeholder","[stun]"),
    ("value.reference","<palsy[stack]>"),
    ("state.pending","? 待翻译"),
    ("state.ok","译 已应用"),
    ("state.error","翻译失败"),
    ("chat.me","[我] 这个问题"),
    ("chat.ai","[AI] 这是回答"),
]

# 值得给用户调的 token 的显示名
TOKEN_LABEL = {
    "surface.window" : "页面底色",
    "surface.card" : "卡片/列表底色",
    "surface.inset" : "内嵌区底色（消息区）",
    "surface.border" : "描边/分隔线",
    "surface.hover" : "列表悬浮行",
    "surface.selected" : "列表选中行",
    "text.depth1" : "第 1 层文字",
    "text.depth2" : "第 2 层文字",
    "text.depth3" : "第 3 层文字",
    "text.depth4" : "第 4 层文字",
    "text.secondary" : "次级文字",
    "text.muted" : "备注/注释",
    "type.buff" : "常见 Buff",
    "type.template" : "Buff 模板",
    "type.global" : "全局 Buff",
    "type.relic" : "肉鸽物品",
    "value.text" : "文本值",
    "value.key" : "键名",
    "value.number" : "数字",
    "value.placeholder" : "黑板占位符 [x]",
    "value.reference" : "Buff 引用 <x>",
    "value.unit" : "单位（秒/层…）",
    "state.pending" : "待翻译",
    "state.running" : "翻译中",
    "state.ok" : "成功/已应用",
    "state.error" : "失败",
    "chat.me" : "[我]",
    "chat.ai" : "[AI]",
    "search.hit" : "搜索命中",
    "json.key" : "原文 键名",
    "json.string" : "原文 字符串",
    "json.number" : "原文 数字",
    "json.bool" : "原文 true/false",
    "json.punct" : "原文 括号逗号",
}


class ColorsPage(QWidget):
    def __init__(self,owner):
        super().__init__(owner.window)
        self.setObjectName("colors")
        self.owner = owner
        self.pickers = {}
        self._loading = False
        self._pending_overrides = None
        self._commit_timer = QTimer(self)
        self._commit_timer.setSingleShot(True)
        self._commit_timer.setInterval(400)
        self._commit_timer.timeout.connect(self._commit)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(36,24,36,20)
        outer.setSpacing(12)
        outer.addWidget(TitleLabel("颜色",self))
        outer.addWidget(BodyLabel(
            "界面上的每种颜色都对应一个用途：层级深浅、数据类型、数值与占位符、翻译状态。"
            "改动立即生效并自动保存。",self))

        # ---- 主题色（全局强调色）----
        accent_card = CardWidget(self)
        accent_layout = QHBoxLayout(accent_card)
        accent_layout.setContentsMargins(14,10,14,10)
        accent_layout.setSpacing(12)
        accent_card.setStyleSheet(
            f"CardWidget {{ background-color:{palette.hex('surface.card')};"
            f" border:1px solid {palette.hex('surface.border')}; border-radius:6px; }}")
        accent_text = QVBoxLayout()
        accent_text.setSpacing(2)
        accent_text.addWidget(StrongBodyLabel("主题色",accent_card))
        accent_hint = CaptionLabel("用于按钮、选中项、焦点框与搜索框高亮。",accent_card)
        accent_hint.setWordWrap(True)
        accent_text.addWidget(accent_hint)
        accent_layout.addLayout(accent_text,1)
        # 只保留一个色块控件（ColorPickerButton 本身就是色块，之前旁边那个重复了）
        self.accent_picker = ColorPickerButton(QColor(self.owner.accent_color()),
                                              "选择主题色",accent_card)
        self.accent_picker.colorChanged.connect(self._on_accent)
        accent_layout.addWidget(self.accent_picker)
        self.accent_reset = PushButton("恢复默认色",accent_card)
        self.accent_reset.clicked.connect(
            lambda: self._on_accent(QColor(palette.NATIVE_ACCENT_DEFAULT)))
        accent_layout.addWidget(self.accent_reset)
        outer.addWidget(accent_card)

        # ---- 配色方案 ----
        scheme_card = CardWidget(self)
        scheme_card.setStyleSheet(
            f"CardWidget {{ background-color:{palette.hex('surface.card')};"
            f" border:1px solid {palette.hex('surface.border')}; border-radius:6px; }}")
        scheme_layout = QVBoxLayout(scheme_card)
        scheme_layout.setContentsMargins(14,10,14,10)
        scheme_layout.setSpacing(8)
        scheme_row = QHBoxLayout()
        scheme_row.setSpacing(10)
        scheme_text = QVBoxLayout()
        scheme_text.setSpacing(2)
        scheme_text.addWidget(StrongBodyLabel("配色方案",scheme_card))
        self.scheme_hint = CaptionLabel("选择一套预设，逐项微调后会自动标记为「自定义」。",
                                        scheme_card)
        self.scheme_hint.setWordWrap(True)
        scheme_text.addWidget(self.scheme_hint)
        scheme_row.addLayout(scheme_text,1)
        self.preset_box = ComboBox(scheme_card)
        for name in palette.preset_names():
            self.preset_box.addItem(palette.preset_label(name),userData=name)
        self.preset_box.setMinimumWidth(220)
        self.preset_box.currentIndexChanged.connect(self._on_preset)
        scheme_row.addWidget(self.preset_box)
        self.reset_button = PushButton("恢复默认",scheme_card)
        self.reset_button.clicked.connect(self.reset_colors)
        scheme_row.addWidget(self.reset_button)
        self.export_button = PushButton("复制为配置",scheme_card)
        self.export_button.setToolTip("把当前配色复制成 config.json 里的写法，方便备份或分享")
        self.export_button.clicked.connect(self.export_colors)
        scheme_row.addWidget(self.export_button)
        self.open_button = ToolButton(scheme_card)
        try:
            from qfluentwidgets import FluentIcon
            self.open_button.setIcon(FluentIcon.FOLDER)
        except Exception:
            self.open_button.setText("配置")
        self.open_button.setToolTip("打开配置文件所在位置")
        self.open_button.clicked.connect(self.open_config)
        scheme_row.addWidget(self.open_button)
        scheme_layout.addLayout(scheme_row)
        outer.addWidget(scheme_card)

        # ---- 预览 ----
        outer.addWidget(StrongBodyLabel("预览",self))
        self.swatch = PlainTextEdit(self)
        self.swatch.setReadOnly(True)
        self.swatch.setFixedHeight(170)
        # 真实场景里这些颜色是画在「卡片底」上的，试色板也得铺同样的底，否则浅色看不见
        font = QFont("Microsoft YaHei UI",10)
        self.swatch.setFont(font)
        outer.addWidget(self.swatch)

        # ---- 取色列表 ----
        outer.addWidget(StrongBodyLabel("逐项颜色",self))
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0,0,8,0)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(6)
        row = 0
        for group,tokens in palette.themed_tokens().items():
            label = CaptionLabel(group,container)
            label.setStyleSheet(palette.qss("text.secondary"))
            grid.addWidget(label,row,0,1,2)
            row += 1
            for token in tokens:
                name = TOKEN_LABEL.get(token,token)
                grid.addWidget(BodyLabel(name,container),row,0)
                if ColorPickerButton is None:
                    grid.addWidget(CaptionLabel(palette.hex(token),container),row,1)
                    row += 1
                    continue
                picker = ColorPickerButton(QColor(palette.hex(token)),"",container)
                picker.setFixedWidth(64)
                picker.colorChanged.connect(lambda color,t=token: self._on_pick(t,color))
                grid.addWidget(picker,row,1)
                self.pickers[token] = picker
                row += 1
        grid.setColumnStretch(0,1)
        scroll.setWidget(container)
        outer.addWidget(scroll,1)

        self.hint = CaptionLabel("所有改动都会自动保存，下次启动继续生效。",self)
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet(palette.qss("text.muted"))
        outer.addWidget(self.hint)

        self.reload_from_config()

    # ----------------------------------------
    def reload_from_config(self):
        '''按当前生效的配色刷新取色按钮与试色板'''
        self._loading = True
        try:
            colors = self.owner.config.get("colors") or {}
            preset = colors.get("preset") or "default"
            overrides = colors.get("overrides") or {}
            if overrides and self.preset_box.findData("custom") < 0:
                self.preset_box.addItem("自定义",userData="custom")
            target = "custom" if (overrides and preset == "default") else preset
            for index in range(self.preset_box.count()):
                if self.preset_box.itemData(index) == target:
                    self.preset_box.setCurrentIndex(index)
                    break
            for token,picker in self.pickers.items():
                picker.setColor(QColor(palette.hex(token)))
        finally:
            self._loading = False
        self._render_swatch()

    def _render_swatch(self):
        self.swatch.setPlainText("")
        self.swatch.setStyleSheet(
            f"background-color:{palette.hex('surface.card')};"
            f"border:1px solid {palette.hex('surface.border')};"
            "border-radius:6px;")
        cursor = self.swatch.textCursor()
        from PySide6.QtGui import QTextCharFormat
        for token,text in SWATCH:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(palette.hex(token)))
            cursor.insertText(text + "\n",fmt)
        self.swatch.setTextCursor(cursor)

    # ----------------------------------------
    # 主题色（全局强调色）
    # ----------------------------------------
    def _on_accent(self,color):
        '''改主题色：ColorPickerButton 自己就是色块，不需要额外的预览控件'''
        if self._loading:
            return
        self.owner.set_accent(color.name())

    # ----------------------------------------
    def _overrides(self):
        colors = self.owner.config.get("colors") or {}
        value = colors.get("overrides")
        return dict(value) if isinstance(value,dict) else {}

    def _on_pick(self,token,color):
        '''拖动取色器时的实时预览：只重画界面，不落盘、不弹提示（否则又卡又吵）'''
        if self._loading:
            return
        overrides = self._overrides()
        overrides[token] = color.name()
        self._pending_overrides = overrides
        self._schedule_commit()
        # 只更新 palette 与界面，不动 config，也不弹 InfoBar
        palette.apply_overrides(overrides,preset=None)
        self.owner.repaint_colors(surfaces_changed=(token.startswith("surface.")))
        self._render_swatch()
        self._mark_custom()

    def _mark_custom(self):
        '''改过单项后，预设名已经不准了：标成「自定义」

        注意别用 setCurrentIndex —— 那会把下拉菜单弹出来，留下一个关不掉的顶层小窗口。
        '''
        self.preset_box.blockSignals(True)
        try:
            menu = getattr(self.preset_box,"dropMenu",None)
            if menu is not None and hasattr(menu,"close"):
                try:
                    menu.close()
                except Exception:
                    pass
            if self.preset_box.findData("custom") < 0:
                self.preset_box.addItem("自定义",userData="custom")
            index = self.preset_box.findData("custom")
            if index >= 0:
                self.preset_box.setCurrentIndex(index)
        finally:
            self.preset_box.blockSignals(False)

    def _schedule_commit(self):
        '''停下 400ms 再写配置，避免拖色时反复落盘'''
        self._commit_timer.start()

    def _commit(self):
        '''把预览中的配色真正写进 config.json'''
        if self._pending_overrides is None:
            return
        overrides = self._pending_overrides
        self._pending_overrides = None
        self.owner.config.setdefault("colors",{})["overrides"] = overrides
        self.owner.apply_colors(overrides=overrides)

    def leaveEvent(self,event):
        '''鼠标离开颜色页时立刻落盘'''
        self._commit()
        super().leaveEvent(event if event is not None else None)

    def _on_preset(self,index):
        if self._loading:
            return
        name = self.preset_box.itemData(index) or "default"
        if name == "custom":
            return
        self.owner.config.setdefault("colors",{})["overrides"] = {}
        self._pending_overrides = None
        # 切预设走平滑过渡：整块界面渐变到新配色，比「啪」一下换掉舒服得多
        self.owner.apply_colors(preset=name,overrides={},animate=True)
        for token,picker in self.pickers.items():
            picker.setColor(QColor(palette.hex(token)))
        self._render_swatch()
        self.owner.notify("配色已切换",palette.preset_label(name))

    def reset_colors(self):
        self.owner.config.setdefault("colors",{})["overrides"] = {}
        self.owner.apply_colors(preset="default",overrides={},animate=True)
        self.reload_from_config()
        self.owner.notify("配色已恢复默认")

    def export_colors(self):
        '''把当前生效配色打印到提示行，方便直接复制进 config.json'''
        pairs = palette.export_overrides()
        if not pairs:
            self.hint.setText("当前使用的是默认配色，没有需要复制的自定义项。")
            return
        text = ", ".join(f'"{token}": ["{light}", "{dark}"]'
                         for token,(light,dark) in pairs.items())
        self.hint.setText("配色已复制到剪贴板，可粘贴进 config.json 备份或分享。")
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
        except Exception:
            pass

    def open_config(self):
        import bootstrap
        path = os.path.abspath(bootstrap.CONFIG_PATH)
        try:
            os.startfile(path)          # Windows
        except Exception:
            MessageBox("配置文件位置",path,self.owner.window).exec()
