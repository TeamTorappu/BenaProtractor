'''
原文面板的 JSON 语法高亮
颜色全部走 ui/palette.py，所以亮/暗主题和用户自定义配色都会自动生效。
挂载方式：highlighter = JsonHighlighter(origin.document())，主题变化后调 rehighlight()。
'''
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

from ui import palette

KEY_RE = r'"(?:\\.|[^"\\])*"(?=\s*:)'
STRING_RE = r'"(?:\\.|[^"\\])*"'
NUMBER_RE = r'(?<![\w"])-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?'
BOOL_RE = r'\b(?:true|false|null)\b'
PUNCT_RE = r'[\{\}\[\],:]'


def _format(token,bold=False,italic=False):
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(palette.hex(token)))
    if bold:
        fmt.setFontWeight(QFont.Weight.DemiBold)
    fmt.setFontItalic(italic)
    return fmt


class JsonHighlighter(QSyntaxHighlighter):
    '''只认 JSON 的几种形态，够用就好（原文面板显示的就是 json.dumps 的结果）'''

    def __init__(self,document,enabled=True):
        super().__init__(document)
        self.enabled = enabled
        self._rebuild()

    def _rebuild(self):
        import re
        self.rules = [
            (re.compile(KEY_RE),_format("json.key",bold=True)),
            (re.compile(STRING_RE),_format("json.string")),
            (re.compile(NUMBER_RE),_format("json.number")),
            (re.compile(BOOL_RE),_format("json.bool")),
            (re.compile(PUNCT_RE),_format("json.punct")),
        ]

    def refresh(self):
        '''主题/配色变化后重新取色并重绘'''
        self._rebuild()
        self.rehighlight()

    def highlightBlock(self,text):
        if not self.enabled or not text:
            return
        for pattern,fmt in self.rules:
            for match in pattern.finditer(text):
                start,end = match.span()
                # 键名（后面跟冒号）优先于「字符串」规则：先命中的先上色，后面的覆盖
                self.setFormat(start,end - start,fmt)
