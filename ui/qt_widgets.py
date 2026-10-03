'''
UI 兼容层：统一「控件构造」的写法
QFluentWidgets 的标签/按钮只接受 (parent)，而 Qt 原生控件习惯 (text, parent)，
两边混着用很容易写出只在某一边成立的代码。这里统一成 (text, parent)：

    from ui.qt_widgets import BodyLabel, PushButton, CaptionLabel, ...
    label = BodyLabel("文字", parent)

没装 QFluentWidgets 时自动退回原生 Qt 控件（原生本来就是 (text, parent)）。

另外这里还提供「卡片底色跟着 palette 走」的适配层，见文件末尾的 bena_card_style：
Fluent 的 SettingCard / CardWidget 自己在 paintEvent 里写死白色，
QSS 改不动它们（实测会被合成成 #d3b8f1 这种混色，见 tools/probe_widget_paint.py）。
'''
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter

try:
    from qfluentwidgets import (  # noqa: F401
        BodyLabel as _BodyLabel,
        CaptionLabel as _CaptionLabel,
        CardWidget as _CardWidget,
        CheckBox as _CheckBox,
        ComboBox as _ComboBox,
        Dialog as _Dialog,
        DoubleSpinBox as _DoubleSpinBox,
        FluentIcon as _FluentIcon,
        FluentWindow as _FluentWindow,
        InfoBar as _InfoBar,
        InfoBarPosition as _InfoBarPosition,
        LargeTitleLabel as _LargeTitleLabel,
        LineEdit as _LineEdit,
        ListWidget as _ListWidget,
        MessageBox as _MessageBox,
        NavigationItemPosition as _NavigationItemPosition,
        PasswordLineEdit as _PasswordLineEdit,
        PlainTextEdit as _PlainTextEdit,
        PrimaryPushButton as _PrimaryPushButton,
        PushButton as _PushButton,
        ScrollArea as _ScrollArea,
        SearchLineEdit as _SearchLineEdit,
        SegmentedWidget as _SegmentedWidget,
        SettingCard as _SettingCard,
        SettingCardGroup as _SettingCardGroup,
        Slider as _Slider,
        SpinBox as _SpinBox,
        StrongBodyLabel as _StrongBodyLabel,
        SubtitleLabel as _SubtitleLabel,
        SwitchButton as _SwitchButton,
        TitleLabel as _TitleLabel,
        ToolButton as _ToolButton,
        PushSettingCard as _PushSettingCard,
        SwitchSettingCard as _SwitchSettingCard,
        ComboBoxSettingCard as _ComboBoxSettingCard,
        ExpandGroupSettingCard as _ExpandGroupSettingCard,
    )
    FLUENT = True
except ImportError:      # pragma: no cover - 只在没装 Fluent 时走
    from PySide6.QtWidgets import (
        QCheckBox as _CheckBox,
        QComboBox as _ComboBox,
        QDialog as _Dialog,
        QFrame as _CardWidget,
        QFrame as _SettingCard,
        QLabel as _BodyLabel,
        QLabel as _CaptionLabel,
        QLabel as _LargeTitleLabel,
        QLabel as _StrongBodyLabel,
        QLabel as _SubtitleLabel,
        QLabel as _TitleLabel,
        QLineEdit as _LineEdit,
        QLineEdit as _PasswordLineEdit,
        QListWidget as _ListWidget,
        QMessageBox as _MessageBox,
        QPlainTextEdit as _PlainTextEdit,
        QPushButton as _PrimaryPushButton,
        QPushButton as _PushButton,
        QScrollArea as _ScrollArea,
        QWidget,
    )
    _SettingCardGroup = None
    _PushSettingCard = None
    _SwitchSettingCard = None
    _ComboBoxSettingCard = None
    _ExpandGroupSettingCard = None
    _Slider = None
    from PySide6.QtWidgets import QDoubleSpinBox as _DoubleSpinBox
    from PySide6.QtWidgets import QSpinBox as _SpinBox

    class _StubSwitchButton(_CheckBox):
        '''没有 Fluent 时的退化开关：就是普通勾选框'''

        def __init__(self,parent=None):
            super().__init__(parent)
            self.checkedChanged = self.toggled

        def setChecked(self,value):
            super().setChecked(bool(value))

    _SwitchButton = _StubSwitchButton

    class _StubSearchLineEdit(_LineEdit):
        def setPlaceholderText(self,text):
            super().setPlaceholderText(text)

    class _StubSegmentedWidget(QWidget):
        '''没有 Fluent 时的退化实现：能加项、能切当前项，不画东西'''

        def __init__(self,parent=None):
            super().__init__(parent)
            self._items = {}

        def addItem(self,key,text=None,onClick=None):
            self._items[key] = (text,onClick)

        def setCurrentItem(self,key):
            self._current = key

        def currentItem(self):
            return getattr(self,"_current",None)

    _SearchLineEdit = _StubSearchLineEdit
    _SegmentedWidget = _StubSegmentedWidget
    _ToolButton = _PushButton
    _FluentIcon = None
    _FluentWindow = None
    _InfoBar = None
    _InfoBarPosition = None
    _NavigationItemPosition = None
    FLUENT = False


def _adaptive(base):
    '''生成一个 (text, parent=None) 签名的子类'''

    class _Widget(base):
        def __init__(self,text="",parent=None):
            try:
                base.__init__(self,parent)
            except TypeError:
                base.__init__(self)
                if parent is not None:
                    self.setParent(parent)
            if text:
                try:
                    self.setText(text)
                except (AttributeError,TypeError):
                    # ToolButton 之类没有 setText，忽略即可
                    pass

    _Widget.__name__ = base.__name__
    _Widget.__qualname__ = base.__name__
    return _Widget


BodyLabel = _adaptive(_BodyLabel)
StrongBodyLabel = _adaptive(_StrongBodyLabel)
CaptionLabel = _adaptive(_CaptionLabel)
SubtitleLabel = _adaptive(_SubtitleLabel)
TitleLabel = _adaptive(_TitleLabel)
LargeTitleLabel = _adaptive(_LargeTitleLabel)
PushButton = _adaptive(_PushButton)
PrimaryPushButton = _adaptive(_PrimaryPushButton)
ToolButton = _adaptive(_ToolButton)
CheckBox = _adaptive(_CheckBox)
SearchLineEdit = _adaptive(_SearchLineEdit)
LineEdit = _adaptive(_LineEdit)
PasswordLineEdit = _adaptive(_PasswordLineEdit)

# 这些本来就只接受 parent，直接透传
ListWidget = _ListWidget
PlainTextEdit = _PlainTextEdit
ScrollArea = _ScrollArea
CardWidget = _CardWidget
SegmentedWidget = _SegmentedWidget
Dialog = _Dialog
MessageBox = _MessageBox
InfoBar = _InfoBar
InfoBarPosition = _InfoBarPosition
FluentIcon = _FluentIcon
FluentWindow = _FluentWindow
NavigationItemPosition = _NavigationItemPosition
ComboBox = _ComboBox
SwitchButton = _SwitchButton
Slider = _Slider
SpinBox = _SpinBox
DoubleSpinBox = _DoubleSpinBox


# ----------------------------------------
# 卡片配色适配层
# ----------------------------------------
def _card_paint(self,event):
    '''按当前的 surface token 画卡片底色/描边（不依赖任何写死的颜色）'''
    from ui import palette
    painter = QPainter(self)
    painter.setRenderHints(QPainter.Antialiasing)
    surface = getattr(self,"_bena_surface","surface.card")
    border_token = getattr(self,"_bena_border","surface.border")
    border = palette.hex(border_token)
    hovered = bool(getattr(self,"_bena_hovered",False) and self.isEnabled()
                   and self.underMouse())
    painter.setBrush(QColor(palette.hex("surface.hover" if hovered else surface)))
    painter.setPen(QColor(border))
    painter.drawRoundedRect(self.rect().adjusted(1,1,-1,-1),6,6)


def _card_enter(self,event):
    self._bena_hovered = True
    self.update()
    super(_CardSurfaceMixin,self).enterEvent(event)


def _card_leave(self,event):
    self._bena_hovered = False
    self.update()
    super(_CardSurfaceMixin,self).leaveEvent(event)


class _CardSurfaceMixin:
    '''给 Fluent 卡片换上「跟着 palette 走」的底色

    为什么必须重写 paintEvent：SettingCard / CardWidget 自己在 paintEvent 里
    用写死的白色画圆角矩形，QSS 只是被合成上去（实测目标色 #7A2BD6 会变成 #d3b8f1），
    所以 QSS 这条路在本机是走不通的（见 tools/probe_widget_paint.py 的实测结论）。
    '''

    _bena_surface = "surface.card"
    _bena_border = "surface.border"
    _bena_hovered = False

    def paintEvent(self,event):
        _card_paint(self,event)

    def enterEvent(self,event):
        _card_enter(self,event)

    def leaveEvent(self,event):
        _card_leave(self,event)


def bena_card_style(widget,surface="surface.card",border="surface.border"):
    '''让一个卡片控件的底色/描边跟着 ui/palette.py 走

    用法（配色变化后重新调一次即可，不需要重建控件）：
        bena_card_style(card,"surface.card")
    对 Fluent 的卡片走「重写 paintEvent」，其它控件退回 QSS。
    '''
    if widget is None:
        return widget
    if not FLUENT or not isinstance(widget,_CardSurfaceMixin):
        from ui import palette as _palette
        widget.setStyleSheet(f"background-color:{_palette.hex(surface)};"
                             f" border:1px solid {_palette.hex(border)};"
                             " border-radius:6px;")
        return widget
    widget._bena_surface = surface
    widget._bena_border = border
    widget.update()
    return widget


def _card_class(base,name):
    '''生成一个「底色跟 palette 走」的卡片类（没有 Fluent 时原样返回）'''
    if base is None:
        return None
    if not FLUENT:
        return base
    return type(name,(_CardSurfaceMixin,base),{})


SettingsCard = _card_class(_SettingCard,"SettingsCard")
SettingsGroup = _SettingCardGroup
SettingsPushCard = _card_class(_PushSettingCard,"SettingsPushCard")
SettingsSwitchCard = _card_class(_SwitchSettingCard,"SettingsSwitchCard")
SettingsComboCard = _card_class(_ComboBoxSettingCard,"SettingsComboCard")
SettingsExpandCard = _ExpandGroupSettingCard
SurfaceCard = _card_class(_CardWidget,"SurfaceCard")


__all__ = [
    "FLUENT","BodyLabel","StrongBodyLabel","CaptionLabel","SubtitleLabel",
    "TitleLabel","LargeTitleLabel","PushButton",
    "PrimaryPushButton","ToolButton","CheckBox","SearchLineEdit","LineEdit",
    "PasswordLineEdit","ListWidget","PlainTextEdit","ScrollArea","CardWidget",
    "SegmentedWidget","Dialog","MessageBox","InfoBar","InfoBarPosition",
    "FluentIcon","FluentWindow","NavigationItemPosition","ComboBox","SwitchButton","Slider",
    "SpinBox","DoubleSpinBox",
    "SettingsCard","SettingsGroup","SettingsPushCard","SettingsSwitchCard",
    "SettingsComboCard","SettingsExpandCard","SurfaceCard","bena_card_style",
]
