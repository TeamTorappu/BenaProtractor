'''
搜索输入的小工具：防抖合并

目录最大有上万条（Buff 模板 8447 条 + 全局 749 + 6 个肉鸽季度），每敲一个字就重建一次
列表控件会明显卡顿。这里把连续输入合并成一次重建：
  - 从「空」变「非空」时立即执行，保证按下第一个字母就有反应；
  - 清空输入同样立即执行，避免「删完了列表还停在上一次结果」；
  - 其余连续输入在 delay 毫秒内合并，只跑最后一次。

判断只看「当前文本是否为空」，不看历史状态：`_on_text_changed` 的 text 一进来就写回
self._text，外部用 setText/clear 直接改动输入框也不会把状态搞乱。
'''
from PySide6.QtCore import QTimer


class SearchDebouncer:
    '''把 line_edit.textChanged 合并成「最多每 delay 毫秒一次」的 apply 调用'''

    def __init__(self,line_edit,apply_callback,delay=200):
        self.line_edit = line_edit
        self.apply_callback = apply_callback
        self.delay = int(delay)
        self._text = line_edit.text()
        self.timer = QTimer(line_edit)
        self.timer.setSingleShot(True)
        self.timer.setInterval(self.delay)
        self.timer.timeout.connect(self.flush)
        line_edit.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self,text):
        text = text or ""
        was_empty = self._text == ""
        self._text = text
        if text == "" or was_empty:
            # 第一个字符 / 清空：立即执行，别让用户觉得没反应
            self.timer.stop()
            self.apply_callback()
            return
        self.timer.start()

    def flush(self):
        '''立刻执行挂起的重建（外部主动触发时用，例如按回车的场景）'''
        self.timer.stop()
        self.apply_callback()

    def sync(self):
        '''把记录的文本与输入框对齐

        调用方 blockSignals 之后直接 setText 时信号不会发出，防抖器记的旧文本就过期了；
        必须显式同步，否则下一次输入会被误判成「连续输入」而走延迟路径。
        '''
        self._text = self.line_edit.text()

    def stop(self):
        self.timer.stop()
