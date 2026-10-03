'''
AI 设置对话框

用的是普通 QDialog 自己排版，而不是 QFluentWidgets 的 Dialog：
后者是给「一句提示 + 两个按钮」用的，塞进长表单会把按钮挤到中间、内容被裁掉。
控件仍然全部用 Fluent 的输入框/按钮，外观保持一致。
'''
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import ComboBox, DoubleSpinBox, SpinBox

from ai import cache, config as config_module, registry
from ui import palette
from ui.qt_widgets import (
    BodyLabel,
    CaptionLabel,
    CheckBox,
    LineEdit,
    PasswordLineEdit,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    StrongBodyLabel,
    TitleLabel,
)


class AISettingsDialog(QDialog):
    def __init__(self,parent=None,on_test=None):
        super().__init__(parent)
        self.setWindowTitle("AI 翻译设置")
        self.setMinimumWidth(700)
        self.resize(760,780)
        # 文字控件一律透明底，避免在对话框底色上多出一层
        self.setStyleSheet(palette.qss_container("surface.window"))
        self.on_test = on_test
        self._testing = False
        config = config_module.load()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24,20,24,16)
        outer.setSpacing(10)
        outer.addWidget(TitleLabel("AI 翻译设置",self))
        intro = BodyLabel(
            "用于把条目里尚未翻译的片段译成中文，以及回答关于当前条目的简单问题。"
            "支持所有 OpenAI 兼容的服务；使用本地模型时把地址填成 "
            "http://127.0.0.1:11434/v1/ ，API Key 可以留空。",self)
        intro.setWordWrap(True)
        intro.setStyleSheet(palette.qss("text.secondary"))
        outer.addWidget(intro)

        # ---- 表单（放在可滚动区里，窗口再矮也不会挤坏）----
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        form_host = QWidget()
        form = QGridLayout(form_host)
        form.setContentsMargins(0,0,8,0)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)
        form.setColumnStretch(1,1)
        row = 0

        form.addWidget(StrongBodyLabel("服务类型",form_host),row,0)
        self.provider_box = ComboBox(form_host)
        for value,label in registry.PROVIDER_CHOICES:
            self.provider_box.addItem(label,userData=value)
        self._select(self.provider_box,config.get("provider"))
        form.addWidget(self.provider_box,row,1)
        row += 1

        form.addWidget(StrongBodyLabel("服务地址",form_host),row,0)
        self.base_url = LineEdit(form_host)
        self.base_url.setPlaceholderText("例如 https://api.deepseek.com/v1")
        self.base_url.setText(str(config.get("base_url","")))
        form.addWidget(self.base_url,row,1)
        row += 1

        form.addWidget(StrongBodyLabel("模型名称",form_host),row,0)
        self.model = LineEdit(form_host)
        self.model.setPlaceholderText("例如 deepseek-chat、qwen2.5:7b")
        self.model.setText(str(config.get("model","")))
        form.addWidget(self.model,row,1)
        row += 1

        form.addWidget(StrongBodyLabel("API Key",form_host),row,0)
        key_row = QHBoxLayout()
        key_row.setSpacing(8)
        self.api_key = PasswordLineEdit(form_host)
        self.api_key.setPlaceholderText("本地模型可留空")
        self.api_key.setText(str(config.get("api_key","")))
        key_row.addWidget(self.api_key,1)
        self.show_key = PushButton("显示",form_host)
        self.show_key.setCheckable(True)
        self.show_key.setFixedWidth(64)
        self.show_key.toggled.connect(self._toggle_key)
        key_row.addWidget(self.show_key)
        form.addLayout(key_row,row,1)
        row += 1

        form.addWidget(StrongBodyLabel("随机度",form_host),row,0)
        self.temperature = DoubleSpinBox(form_host)
        self.temperature.setRange(0.0,2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setToolTip("越低越稳定，翻译建议保持较低")
        self.temperature.setValue(float(config.get("temperature",0.2)))
        form.addWidget(self.temperature,row,1)
        row += 1

        form.addWidget(StrongBodyLabel("最长回复",form_host),row,0)
        self.max_tokens = SpinBox(form_host)
        self.max_tokens.setRange(32,8192)
        self.max_tokens.setToolTip("单次回复的最大长度")
        self.max_tokens.setValue(int(config.get("max_tokens",512)))
        form.addWidget(self.max_tokens,row,1)
        row += 1

        form.addWidget(StrongBodyLabel("思考强度",form_host),row,0)
        self.effort = ComboBox(form_host)
        for value,label in [("","不指定"),("low","低（更短更快）"),
                            ("medium","中"),("high","高（更慢更详细）")]:
            self.effort.addItem(label,userData=value)
        self.effort.setToolTip("支持该参数的服务会据此调整；不支持时自动忽略")
        self._select(self.effort,config.get("reasoning_effort","low"))
        form.addWidget(self.effort,row,1)
        row += 1

        form.addWidget(StrongBodyLabel("请求超时",form_host),row,0)
        self.timeout = SpinBox(form_host)
        self.timeout.setRange(5,600)
        self.timeout.setSuffix(" 秒")
        self.timeout.setValue(int(config.get("request_timeout",60)))
        form.addWidget(self.timeout,row,1)
        row += 1

        form.addWidget(StrongBodyLabel("上下文上限",form_host),row,0)
        self.budget = SpinBox(form_host)
        self.budget.setRange(1000,200000)
        self.budget.setSingleStep(1000)
        self.budget.setSuffix(" 字符")
        self.budget.setToolTip("发送给模型的译文与原文内容上限")
        self.budget.setValue(int(config.get("context_char_budget",12000)))
        form.addWidget(self.budget,row,1)
        row += 1

        self.heuristic = CheckBox("同时列出尚未收录的英文标识（例如技能名、状态名）",form_host)
        self.heuristic.setChecked(bool(config.get("enable_heuristic_fragments",True)))
        form.addWidget(self.heuristic,row,0,1,2)
        row += 1

        self.auto_translate = CheckBox("打开条目时自动翻译第一条（默认关闭，需手动点击翻译）",
                                       form_host)
        self.auto_translate.setChecked(bool(config.get("auto_translate_on_select",False)))
        form.addWidget(self.auto_translate,row,0,1,2)
        row += 1

        form.addWidget(StrongBodyLabel("系统提示词（留空使用内置）",form_host),row,0,1,2)
        row += 1
        self.system_prompt = PlainTextEdit(form_host)
        self.system_prompt.setPlainText(str(config.get("system_prompt","")))
        self.system_prompt.setPlaceholderText("一般不需要填写")
        self.system_prompt.setFixedHeight(76)
        form.addWidget(self.system_prompt,row,0,1,2)
        row += 1

        scroll.setWidget(form_host)
        outer.addWidget(scroll,1)

        # ---- 翻译记录 ----
        stats = cache.stats()
        cache_row = QHBoxLayout()
        cache_row.setSpacing(8)
        self.cache_label = CaptionLabel(f"已保存的翻译记录：{stats['count']} 条",self)
        self.cache_label.setToolTip(stats["file"])
        cache_row.addWidget(self.cache_label)
        cache_row.addStretch(1)
        self.test_button = PushButton("测试连接",self)
        self.test_button.clicked.connect(self.test_connection)
        cache_row.addWidget(self.test_button)
        self.export_button = PushButton("导出翻译记录",self)
        self.export_button.setToolTip("导出为 Markdown 表格，便于校对或分享")
        self.export_button.clicked.connect(self.export_cache)
        cache_row.addWidget(self.export_button)
        outer.addLayout(cache_row)

        self.status = CaptionLabel("",self)
        self.status.setWordWrap(True)
        self.status.setStyleSheet(palette.qss("text.muted"))
        outer.addWidget(self.status)

        # ---- 底部按钮 ----
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.cancel_button = PushButton("取消",self)
        self.cancel_button.setFixedWidth(110)
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_button)
        self.yesButton = PrimaryPushButton("保存",self)
        self.yesButton.setFixedWidth(130)
        self.yesButton.clicked.connect(self._on_accept)
        buttons.addWidget(self.yesButton)
        outer.addLayout(buttons)

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

    def _on_accept(self):
        config = self.collect()
        if not config.get("base_url") or not config.get("model"):
            self.status.setStyleSheet(palette.qss("state.error"))
            self.status.setText("请先填写服务地址与模型名称。")
            return
        config_module.save(config)
        registry.reset()
        self.accept()

    def export_cache(self):
        try:
            path = cache.export_markdown()
        except Exception as error:
            self.status.setStyleSheet(palette.qss("state.error"))
            self.status.setText("导出失败：" + str(error))
            return
        self.status.setStyleSheet(palette.qss("state.ok"))
        self.status.setText("已导出到：" + path)

    def test_connection(self):
        config = self.collect()
        missing = config_module.missing_fields(config)
        if missing:
            self.status.setStyleSheet(palette.qss("state.error"))
            self.status.setText("请先填写：" + "、".join(missing))
            return
        if self.on_test is None:
            self.status.setText("当前环境不支持测试连接。")
            return
        self._testing = True
        self.status.setStyleSheet(palette.qss("state.running"))
        self.status.setText("正在测试…（未填写 API Key 时，在线服务通常会返回 401）")
        self.test_button.setEnabled(False)
        self.on_test(config,self._on_test_done)

    def _on_test_done(self,ok,message):
        self._testing = False
        self.test_button.setEnabled(True)
        self.status.setStyleSheet(palette.qss("state.ok" if ok else "state.error"))
        self.status.setText(("连接正常：" if ok else "测试失败：") + message)

    def done(self,result):
        '''关闭前先把还在跑的测试线程收掉，别让 QThread 被回收'''
        stop = getattr(self,"stop_test",None)
        if callable(stop):
            stop()
        super().done(result)
