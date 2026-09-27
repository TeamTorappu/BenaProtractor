'''
AI 助手页：模型接口配置 + 缓存统计（设置卡片风格）

以前这些配置藏在侧栏弹出的对话框里（ui/qt_ai_settings.py），行窄、滚动长；
现在改成「左侧导航 → AI 助手」里的分组卡片，侧栏的「AI 设置」按钮仍然可用（切到本页）。

约定（与 AI.md 一致）：
- 支持任何 OpenAI 兼容接口，本地模型可以不填 Key；
- 结果只写 .bena_cache/ai/，**永远不**自动改 translation/*.json。
'''
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from ai import cache, config as config_module, registry
from ui import palette
from ui.qt_widgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    DoubleSpinBox,
    FluentIcon,
    LineEdit,
    PasswordLineEdit,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SettingsCard,
    SettingsGroup,
    SettingsPushCard,
    SettingsSwitchCard,
    SpinBox,
    TitleLabel,
    bena_card_style,
)


class _FieldCard(SettingsCard):
    '''一行「标题 + 说明 + 右侧输入控件」的设置卡片'''

    def __init__(self,icon,title,content,control,parent=None):
        super().__init__(icon,title,content,parent)
        self.control = control
        if control is not None:
            control.setParent(self)
            self.hBoxLayout.addWidget(control,0,Qt.AlignRight)
            self.hBoxLayout.addSpacing(16)
        bena_card_style(self)


class AIPage(QWidget):
    def __init__(self,owner):
        super().__init__(owner.window)
        self.setObjectName("ai")
        self.owner = owner
        self._loading = False
        config = config_module.load()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(36,24,36,20)
        outer.setSpacing(12)
        outer.addWidget(TitleLabel("AI 助手",self))
        intro = BodyLabel(
            "AI 只做一件事：把引擎没翻出来的片段补成中文，并回答关于当前条目的简单问题。"
            "数值与机制判定永远来自游戏数据，不交给模型。",self)
        intro.setWordWrap(True)
        intro.setStyleSheet(palette.qss("text.secondary"))
        outer.addWidget(intro)

        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0,4,10,4)
        layout.setSpacing(16)

        # ---- 服务 ----
        service = SettingsGroup("服务",host)
        layout.addWidget(service)

        self.provider_box = ComboBox(service)
        for value,label in registry.PROVIDER_CHOICES:
            self.provider_box.addItem(label,userData=value)
        self.provider_box.setMinimumWidth(220)
        self._select(self.provider_box,config.get("provider"))
        service.addSettingCard(_FieldCard(FluentIcon.ROBOT,"服务类型",
                                          "任何 OpenAI 兼容接口都可以。",
                                          self.provider_box,service))

        self.base_url = LineEdit(service)
        self.base_url.setPlaceholderText("例如 https://api.deepseek.com/v1")
        self.base_url.setText(str(config.get("base_url","")))
        self.base_url.setMinimumWidth(320)
        service.addSettingCard(_FieldCard(FluentIcon.GLOBE,"服务地址",
                                          "本地模型填 http://127.0.0.1:11434/v1/",
                                          self.base_url,service))

        self.model = LineEdit(service)
        self.model.setPlaceholderText("例如 deepseek-chat、qwen2.5:7b")
        self.model.setText(str(config.get("model","")))
        self.model.setMinimumWidth(320)
        service.addSettingCard(_FieldCard(FluentIcon.TAG,"模型名称","",
                                          self.model,service))

        key_host = QWidget(service)
        key_row = QHBoxLayout(key_host)
        key_row.setContentsMargins(0,0,0,0)
        key_row.setSpacing(6)
        self.api_key = PasswordLineEdit(key_host)
        self.api_key.setPlaceholderText("本地模型可留空")
        self.api_key.setText(str(config.get("api_key","")))
        self.api_key.setMinimumWidth(260)
        key_row.addWidget(self.api_key)
        self.show_key = PushButton("显示",key_host)
        self.show_key.setCheckable(True)
        self.show_key.setFixedWidth(64)
        self.show_key.toggled.connect(self._toggle_key)
        key_row.addWidget(self.show_key)
        service.addSettingCard(_FieldCard(FluentIcon.FINGERPRINT,"API Key",
                                          "也可以放在环境变量 BENA_AI_KEY 里",
                                          key_host,service))

        # ---- 生成参数 ----
        params = SettingsGroup("生成参数",host)
        layout.addWidget(params)

        self.temperature = DoubleSpinBox(params)
        self.temperature.setRange(0.0,2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(float(config.get("temperature",0.2)))
        params.addSettingCard(_FieldCard(FluentIcon.EDIT,"随机度",
                                         "越低越稳定，翻译建议保持较低",
                                         self.temperature,params))

        self.max_tokens = SpinBox(params)
        self.max_tokens.setRange(32,8192)
        self.max_tokens.setValue(int(config.get("max_tokens",512)))
        params.addSettingCard(_FieldCard(FluentIcon.DOCUMENT,"最长回复","单次回复的最大长度",
                                         self.max_tokens,params))

        self.effort = ComboBox(params)
        for value,label in (("","不指定"),("low","低（更短更快）"),
                            ("medium","中"),("high","高（更慢更详细）")):
            self.effort.addItem(label,userData=value)
        self.effort.setMinimumWidth(180)
        self._select(self.effort,config.get("reasoning_effort","low"))
        params.addSettingCard(_FieldCard(FluentIcon.SPEED_HIGH,"思考强度",
                                         "不支持该参数的服务会自动忽略",
                                         self.effort,params))

        self.timeout = SpinBox(params)
        self.timeout.setRange(5,600)
        self.timeout.setSuffix(" 秒")
        self.timeout.setValue(int(config.get("request_timeout",60)))
        params.addSettingCard(_FieldCard(FluentIcon.HISTORY,"请求超时","",
                                         self.timeout,params))

        self.budget = SpinBox(params)
        self.budget.setRange(1000,200000)
        self.budget.setSingleStep(1000)
        self.budget.setSuffix(" 字符")
        self.budget.setValue(int(config.get("context_char_budget",12000)))
        params.addSettingCard(_FieldCard(FluentIcon.LIBRARY,"上下文上限",
                                         "发送给模型的译文内容上限",
                                         self.budget,params))

        # ---- 行为开关 ----
        behaviour = SettingsGroup("行为",host)
        layout.addWidget(behaviour)

        self.heuristic = SettingsSwitchCard(
            FluentIcon.SEARCH,"列出英文标识",
            "把「一个中文字都没有、又含字母」的行也列进待译片段",None,behaviour)
        bena_card_style(self.heuristic)
        self.heuristic.setValue(bool(config.get("enable_heuristic_fragments",True)))
        behaviour.addSettingCard(self.heuristic)

        self.auto_translate = SettingsSwitchCard(
            FluentIcon.ROBOT,"选中即自动翻译",
            "打开条目时自动开始翻译第一个片段（默认关闭）",None,behaviour)
        bena_card_style(self.auto_translate)
        self.auto_translate.setValue(bool(config.get("auto_translate_on_select",False)))
        behaviour.addSettingCard(self.auto_translate)

        self.system_prompt = PlainTextEdit(host)
        self.system_prompt.setPlainText(str(config.get("system_prompt","")))
        self.system_prompt.setPlaceholderText("一般不需要填写；留空使用内置提示词")
        self.system_prompt.setFixedHeight(90)
        prompt_card = SettingsCard(FluentIcon.CODE,"系统提示词","留空使用内置",host)
        bena_card_style(prompt_card)
        behaviour.addSettingCard(prompt_card)
        layout.addWidget(self.system_prompt)

        # ---- 缓存与操作 ----
        actions = SettingsGroup("翻译记录",host)
        layout.addWidget(actions)
        self.cache_card = SettingsCard(FluentIcon.SAVE,"缓存","正在统计…",actions)
        bena_card_style(self.cache_card)
        actions.addSettingCard(self.cache_card)

        self.export_card = SettingsPushCard("导出",FluentIcon.SAVE,"导出翻译记录",
                                            "导出为 Markdown 表格，便于校对或提 PR",actions)
        bena_card_style(self.export_card)
        self.export_card.clicked.connect(self.export_cache)
        actions.addSettingCard(self.export_card)
        layout.addStretch(1)

        scroll.setWidget(host)
        outer.addWidget(scroll,1)

        # ---- 底部操作行 ----
        buttons = QHBoxLayout()
        self.status = BodyLabel("",self)
        self.status.setWordWrap(True)
        self.status.setStyleSheet(palette.qss("text.muted"))
        buttons.addWidget(self.status,1)
        self.test_button = PushButton("测试连接",self)
        self.test_button.clicked.connect(self.test_connection)
        buttons.addWidget(self.test_button)
        self.save_button = PrimaryPushButton("保存",self)
        self.save_button.setFixedWidth(130)
        self.save_button.clicked.connect(self.save)
        buttons.addWidget(self.save_button)
        outer.addLayout(buttons)

        self.refresh_cache_state()

    # ----------------------------------------
    @staticmethod
    def _select(combo,value):
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                return

    def _toggle_key(self,checked):
        self.api_key.setEchoMode(LineEdit.Normal if checked else LineEdit.Password)

    def collect(self):
        config = config_module.load()
        config["provider"] = self.provider_box.currentData()
        config["base_url"] = self.base_url.text().strip()
        config["model"] = self.model.text().strip()
        config["api_key"] = self.api_key.text().strip()
        config["temperature"] = float(self.temperature.value())
        config["max_tokens"] = int(self.max_tokens.value())
        config["reasoning_effort"] = self.effort.currentData()
        config["request_timeout"] = int(self.timeout.value())
        config["context_char_budget"] = int(self.budget.value())
        config["enable_heuristic_fragments"] = bool(self.heuristic.isChecked())
        config["auto_translate_on_select"] = bool(self.auto_translate.isChecked())
        config["system_prompt"] = self.system_prompt.toPlainText().strip()
        return config

    def save(self):
        config = self.collect()
        if not config.get("base_url") or not config.get("model"):
            self.set_status("请先填写服务地址与模型名称。","state.error")
            return False
        config_module.save(config)
        registry.reset()
        self.set_status("设置已保存，回到条目里点「全部翻译」试试。","state.ok")
        # 侧栏也要跟着刷新（它缓存了配置说明文字）
        panel = getattr(self.owner,"ai_panel",None)
        if panel is not None:
            try:
                panel.refresh_config_state()
            except Exception:
                pass
        self.owner.notify("AI 设置已保存",config.get("model",""))
        return True

    def test_connection(self):
        panel = getattr(self.owner,"ai_panel",None)
        if panel is None:
            self.set_status("AI 侧栏没能加载，无法测试连接。","state.error")
            return
        config = self.collect()
        missing = config_module.missing_fields(config)
        if missing:
            self.set_status("请先填写：" + "、".join(missing),"state.error")
            return
        self.set_status("正在测试…（未填 API Key 时在线服务通常会返回 401）","state.running")
        self.test_button.setEnabled(False)

        def done(ok,message):
            self.test_button.setEnabled(True)
            self.set_status(("连接正常：" if ok else "测试失败：") + message,
                            "state.ok" if ok else "state.error")

        panel.run_test(config,done)

    def export_cache(self):
        try:
            path = cache.export_markdown()
        except Exception as error:
            self.set_status("导出失败：" + str(error),"state.error")
            return
        self.set_status("已导出到：" + path,"state.ok")

    def refresh_cache_state(self):
        try:
            stats = cache.stats()
        except Exception:
            return
        self.cache_card.setTitle(f"已保存 {stats['count']} 条翻译记录")
        self.cache_card.setContent(str(stats["file"]))

    def set_status(self,text,token="text.muted"):
        self.status.setText(text)
        self.status.setStyleSheet(palette.qss(token))

    def restyle(self):
        for card in self.findChildren(SettingsCard):
            bena_card_style(card)
        self.status.setStyleSheet(palette.qss("text.muted"))

    def refresh_colors(self):
        '''过渡动画每一帧调用：卡片是自绘的，逐帧 update 即可（不重设样式表）'''
        for card in self.findChildren(SettingsCard):
            card.update()
