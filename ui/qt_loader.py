'''
Qt 数据准备对话框
分发版第一次启动时，用户需要自己下载游戏数据（约 70MB+），这里给出明确进度与失败原因。
下载在 QThread 里跑，对话框自己的事件循环负责刷新进度，所以窗口不会假死、可以取消。
'''
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from downloader import human_size


class DownloadWorker(QThread):
    progress = Signal(str,int,int)   # 阶段文本 / 当前字节 / 总字节
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.cancel_event = None

    def cancel(self):
        if self.cancel_event is not None:
            self.cancel_event.set()

    def run(self):
        import threading

        import bootstrap
        self.cancel_event = threading.Event()

        def report(stage,current=0,total=0):
            self.progress.emit(str(stage),int(current or 0),int(total or 0))

        try:
            bootstrap.download_data(report,self.cancel_event)
            self.finished_ok.emit()
        except Exception as error:
            if self.cancel_event.is_set():
                self.failed.emit("已取消")
            else:
                self.failed.emit(f"{type(error).__name__}: {error}")


class DataPrepareDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("准备游戏数据")
        self.setWindowFlag(Qt.WindowCloseButtonHint,False)
        self.setMinimumWidth(520)
        self.worker = None
        self.error_message = None
        self.cancelled = False

        layout = QVBoxLayout(self)
        self.title = QLabel("正在准备《明日方舟》游戏数据…")
        self.title.setWordWrap(True)
        layout.addWidget(self.title)
        self.detail = QLabel("首次运行需要下载约 70MB+ 的数据，请保持网络畅通。\n"
                             "中断也没关系：下载支持断点续传，重开程序会接着下。\n"
                             "如果速度很慢或一直失败，请尝试开启代理（俗称梯子）后重试。")
        self.detail.setWordWrap(True)
        self.detail.setObjectName("Hint")
        layout.addWidget(self.detail)
        self.bar = QProgressBar()
        self.bar.setRange(0,100)
        self.bar.setValue(0)
        layout.addWidget(self.bar)
        self.note = QLabel("")
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.cancel_button = QPushButton("取消下载")
        self.cancel_button.clicked.connect(self.cancel)
        layout.addWidget(self.cancel_button)

    # ----------------------------------------
    def start(self):
        '''开始下载；返回是否成功'''
        self.error_message = None
        self.cancelled = False
        self.worker = DownloadWorker(self)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished_ok.connect(self.accept)
        self.worker.failed.connect(self._on_failed)
        self.cancel_button.setEnabled(True)
        self.worker.start()
        self.exec()
        return self.error_message is None and not self.cancelled

    def cancel(self):
        self.cancelled = True
        self.title.setText("正在取消…（等当前数据块结束）")
        if self.worker is not None:
            self.worker.cancel()

    def update_progress(self,stage,current=0,total=0):
        self.title.setText(stage)
        if total and total > 0:
            percent = int(min(current / total,1.0) * 100)
            self.bar.setRange(0,100)
            self.bar.setValue(percent)
            self.note.setText(f"{human_size(current)} / {human_size(total)}")
        else:
            self.bar.setRange(0,0)
            self.note.setText("")

    def _on_failed(self,message):
        self.error_message = message
        self.reject()

    def wait_worker(self):
        if self.worker is not None:
            self.worker.wait(60000)
            self.worker = None
