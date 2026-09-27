'''
设置页（Fluent 设置卡片风格）

布局参考了常见 Windows 11 / 绘世启动器那种「左导航 + 分组行卡片」的组织方式：
    SegmentedWidget 切「外观 / 数据 / 配色 / 关于」，每组内是一行一张的 SettingCard。
卡片的底色由 ui/qt_widgets.bena_card_style 接管（Fluent 自己画死的白色在深色主题下很突兀，
而且 QSS 改不动，见 tools/probe_widget_paint.py 的实测结论）。

约束：
- 颜色仍然只来自 ui/palette.py，这里不写任何十六进制；
- 配置读写走 bootstrap（config.json），不引入 QFluentWidgets 自己的 qconfig。
'''
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from ui import palette
from ui.qt_widgets import (
    BodyLabel,
    ComboBox,
    FluentIcon,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SegmentedWidget,
    SettingsCard,
    SettingsComboCard,
    SettingsGroup,
    SettingsPushCard,
    SettingsSwitchCard,
    Slider,
    StrongBodyLabel,
    TitleLabel,
    bena_card_style,
)

ABOUT_TEXT = (
    "《贝娜的量角器》是《明日方舟》的机制与藏品翻译分析工具："
    "把游戏数据里的 Node 伪代码与藏品效果翻译成可读的中文结构。\n\n"
    "· 本工具是纯分析/翻译工具，不包含任何编辑功能，也不支持私服相关项目。\n"
    "· 译文里的数值大多为默认数据，实际数值可能受关卡黑板参数制约。\n"
    "· Node 与藏品机制的翻译仍需大量人力，欢迎提交 PR 帮助完善（见 README）。"
)

# 字号缩放的档位（与 palette.font_scale 对应）
FONT_SCALE_CHOICES = [("小 90%",0.9),("标准 100%",1.0),("大 115%",1.15),("更大 130%",1.3)]


def make_row_card(title,content,control,parent=None,icon=None):
    '''一行设置卡片：左边标题+说明，右边任意控件（组合框/滑块/按钮）'''
    card = SettingsCard(icon or FluentIcon.SETTING,title,content,parent)
    if control is not None:
        card.hBoxLayout.addWidget(control,0,Qt.AlignRight)
        card.hBoxLayout.addSpacing(16)
    bena_card_style(card)
    return card


class SettingsPage(QWidget):
    '''「设置」页：外观 / 数据 / 配色 / 关于'''

    def __init__(self,owner):
        super().__init__(owner.window)
        self.setObjectName("settings")
        self.owner = owner
        self.cards = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(36,24,36,20)
        outer.setSpacing(12)
        heading = TitleLabel("设置",self)
        outer.addWidget(heading)
        hint = BodyLabel("界面外观、数据来源、配色与关于信息都在这里。改动会立即保存。",self)
        hint.setWordWrap(True)
        hint.setStyleSheet(palette.qss("text.secondary"))
        outer.addWidget(hint)

        self.pivot = SegmentedWidget(self)
        # 注意：Pivot 的 addItem(onClick=...) 只在**用户点击**时触发，
        # 程序里 setCurrentItem() 不会调它（切页会不同步）。
        # 所以统一听 currentItemChanged，点击与代码切换都走同一条路。
        self.pivot.addItem("appearance","外观")
        self.pivot.addItem("data","数据")
        self.pivot.addItem("colors","配色")
        self.pivot.addItem("about","关于")
        self.pivot.setCurrentItem("appearance")
        self.pivot.currentItemChanged.connect(self._on_section_changed)
        pivot_row = QHBoxLayout()
        pivot_row.addWidget(self.pivot)
        pivot_row.addStretch(1)
        outer.addLayout(pivot_row)

        from PySide6.QtWidgets import QStackedWidget
        self.stack = QStackedWidget(self)
        self.stack.addWidget(self._build_appearance())
        self.stack.addWidget(self._build_data())
        self.stack.addWidget(self._build_colors())
        self.stack.addWidget(self._build_about())
        outer.addWidget(self.stack,1)

        self.reload()

    SECTIONS = ("appearance","data","colors","about")

    def _on_section_changed(self,route_key):
        if route_key in self.SECTIONS:
            self.stack.setCurrentIndex(self.SECTIONS.index(route_key))

    def show_section(self,route_key):
        '''切到某个分区（别的页面/诊断脚本调）'''
        self.pivot.setCurrentItem(route_key)
        self._on_section_changed(route_key)

    # ----------------------------------------
    # 外观
    # ----------------------------------------
    def _build_appearance(self):
        page,layout = self._scroll_page()

        group = SettingsGroup("界面",page)
        layout.addWidget(group)

        self.theme_box = ComboBox(group)
        for value,label in (("auto","跟随系统"),("light","浅色"),("dark","深色")):
            self.theme_box.addItem(label,userData=value)
        self.theme_box.setMinimumWidth(160)
        self.theme_box.currentIndexChanged.connect(self._on_theme)
        group.addSettingCard(make_row_card(
            "主题","跟随系统时会随 Windows 的浅色/深色设置自动切换。",
            self.theme_box,group,FluentIcon.CONSTRACT))

        self.font_scale_box = ComboBox(group)
        for label,value in FONT_SCALE_CHOICES:
            self.font_scale_box.addItem(label,userData=value)
        self.font_scale_box.setMinimumWidth(160)
        self.font_scale_box.currentIndexChanged.connect(self._on_font_scale)
        group.addSettingCard(make_row_card(
            "译文字号","影响译文树、目录与原文面板的字号（Ctrl+= / Ctrl+- 也能调）。",
            self.font_scale_box,group,FluentIcon.FONT))

        self.density_switch = self._switch(group,self._on_density)
        group.addSettingCard(self.density_switch)
        self._set_card_text(self.density_switch,
                            "紧凑目录","减小目录行高，一屏能看到更多条目。")

        layout.addStretch(1)
        return page

    # ----------------------------------------
    # 数据
    # ----------------------------------------
    def _build_data(self):
        page,layout = self._scroll_page()

        group = SettingsGroup("游戏数据",page)
        layout.addWidget(group)

        self.data_status = SettingsCard(FluentIcon.FOLDER,"数据状态","正在检查…",group)
        bena_card_style(self.data_status)
        group.addSettingCard(self.data_status)

        self.load_card = SettingsPushCard("选择加载内容",FluentIcon.SYNC,
                                          "加载项","勾选要加载的数据类型；改动只影响本次运行。",
                                          group)
        bena_card_style(self.load_card)
        self.load_card.clicked.connect(lambda: self.owner.ask_reload())
        group.addSettingCard(self.load_card)

        self.download_card = SettingsPushCard("检查并下载",FluentIcon.CLOUD,
                                              "下载游戏数据",
                                              "数据缺失时用于重新下载（支持断点续传）。",
                                              group)
        bena_card_style(self.download_card)
        self.download_card.clicked.connect(lambda: self.owner.prepare_data_dialog(None))
        group.addSettingCard(self.download_card)

        window_group = SettingsGroup("窗口",page)
        layout.addWidget(window_group)
        self.reset_layout_card = SettingsPushCard("恢复默认分栏",FluentIcon.ZOOM,
                                                  "分栏与窗口","把各页面的列表/译文/侧栏比例恢复为默认值。",
                                                  window_group)
        bena_card_style(self.reset_layout_card)
        self.reset_layout_card.clicked.connect(self._reset_layout)
        window_group.addSettingCard(self.reset_layout_card)

        self.config_card = SettingsPushCard("打开配置文件",FluentIcon.FOLDER,
                                            "配置文件","config.json 里可以手写配色、窗口尺寸等。",
                                            window_group)
        bena_card_style(self.config_card)
        self.config_card.clicked.connect(self._open_config)
        window_group.addSettingCard(self.config_card)

        layout.addStretch(1)
        return page

    # ----------------------------------------
    # 配色
    # ----------------------------------------
    def _build_colors(self):
        page,layout = self._scroll_page()

        group = SettingsGroup("配色方案",page)
        layout.addWidget(group)

        self.preset_box = ComboBox(group)
        for name in palette.preset_names():
            self.preset_box.addItem(palette.preset_label(name),userData=name)
        self.preset_box.setMinimumWidth(200)
        self.preset_box.currentIndexChanged.connect(self._on_preset)
        group.addSettingCard(make_row_card(
            "配色方案","11 套预设一键切换；逐项微调在下面的「逐项颜色」里。",
            self.preset_box,group,FluentIcon.PALETTE))

        self.open_colors_card = SettingsPushCard("打开逐项颜色",FluentIcon.BRUSH,
                                                 "逐项颜色",
                                                 "每个语义颜色都能单独取色（35 个 token）。",
                                                 group)
        bena_card_style(self.open_colors_card)
        self.open_colors_card.clicked.connect(self._open_colors_page)
        group.addSettingCard(self.open_colors_card)

        layout.addStretch(1)
        return page

    # ----------------------------------------
    # 关于
    # ----------------------------------------
    def _build_about(self):
        page,layout = self._scroll_page()
        group = SettingsGroup("关于",page)
        layout.addWidget(group)

        about = BodyLabel(ABOUT_TEXT,group)
        about.setWordWrap(True)
        about.setStyleSheet(palette.qss("text.secondary"))
        card = SettingsCard(FluentIcon.INFO,"《贝娜的量角器》","",group)
        bena_card_style(card)
        card.hBoxLayout.addSpacing(8)
        group.addSettingCard(card)
        layout.addWidget(about)

        version = SettingsCard(FluentIcon.TAG,"版本",self._version_text(),group)
        bena_card_style(version)
        group.addSettingCard(version)
        layout.addStretch(1)
        return page

    def _version_text(self):
        import sys
        core = ".".join(str(part) for part in sys.version_info[:3])
        return f"Python {core}"

    # ----------------------------------------
    # 小工具
    # ----------------------------------------
    def _scroll_page(self):
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0,4,10,4)
        layout.setSpacing(16)
        # 注意：弹簧必须加在**末尾**。加在最前面会把整组内容顶到页面底部，
        # 上面留一大片空白（第一版就写反了）。
        scroll.setWidget(host)
        return scroll,layout

    def _switch(self,parent,callback):
        card = SettingsSwitchCard(FluentIcon.SETTING,"开关","",None,parent)
        bena_card_style(card)
        card.checkedChanged.connect(callback)
        return card

    @staticmethod
    def _set_card_text(card,title,content):
        card.setTitle(title)
        card.setContent(content)

    def _add_group_card(self,layout,card):
        layout.addWidget(card)
        return card

    # ----------------------------------------
    # 同步状态
    # ----------------------------------------
    def reload(self):
        '''按当前 config / 运行状态刷新各控件的值（避免回写时触发信号）'''
        self._loading = True
        try:
            theme = str(self.owner.config.get("theme","auto") or "auto")
            self._select(self.theme_box,theme)
            self._select(self.font_scale_box,float(palette.font_scale()))
            self.density_switch.setValue(bool(self.owner.config.get("compact_directory",False)))
            colors = self.owner.config.get("colors") or {}
            self._select(self.preset_box,colors.get("preset") or "default")
            self._refresh_data_status()
        finally:
            self._loading = False

    def restyle(self):
        '''配色变化后重刷所有卡片底色（Fluent 卡片不跟 QSS，必须显式重画）'''
        for card in self.findChildren(SettingsCard):
            bena_card_style(card)

    def refresh_colors(self):
        '''过渡动画每一帧调用：Fluent 卡片是自绘的，逐帧换色很便宜（只 update）'''
        for card in self.findChildren(SettingsCard):
            card.update()

    @staticmethod
    def _select(combo,value):
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                return
        if isinstance(value,float):
            for index in range(combo.count()):
                if abs(float(combo.itemData(index)) - value) < 0.001:
                    combo.setCurrentIndex(index)
                    return

    def _refresh_data_status(self):
        try:
            import downloader
            missing = downloader.missing_files()
        except Exception as error:
            missing = [f"无法检查（{error}）"]
        if missing:
            self.data_status.setTitle("数据状态：不完整")
            self.data_status.setContent("缺少 " + "、".join(str(name) for name in missing[:4]))
        else:
            self.data_status.setTitle("数据状态：就绪")
            self.data_status.setContent("游戏数据已下载完整，可以直接分析。")

    # ----------------------------------------
    # 交互
    # ----------------------------------------
    def _on_theme(self,index):
        if getattr(self,"_loading",False):
            return
        value = self.theme_box.itemData(index)
        if value:
            self.owner.set_theme(value)

    def _on_font_scale(self,index):
        if getattr(self,"_loading",False):
            return
        value = self.font_scale_box.itemData(index)
        if value:
            self.owner.set_font_scale(float(value))

    def _on_density(self,checked):
        if getattr(self,"_loading",False):
            return
        self.owner.set_compact_directory(bool(checked))

    def _on_preset(self,index):
        if getattr(self,"_loading",False):
            return
        name = self.preset_box.itemData(index)
        if name:
            self.owner.apply_colors(preset=name,overrides={},animate=True)

    def _reset_layout(self):
        self.owner.reset_layout()

    def _open_colors_page(self):
        page = getattr(self.owner,"colors_page",None)
        if page is not None:
            self.owner.window.switchTo(page)

    def _open_config(self):
        self.owner._open_config_file()
