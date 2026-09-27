'''
Qt 版「选择要加载的内容」对话框
与旧 tkinter 版行为一致：勾选要加载的数据、可以记住选择、点「贝娜！部署！」
'''
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

import bootstrap


class QtSelector(QDialog):
    def __init__(self,parent=None,current=None):
        super().__init__(parent)
        self.setWindowTitle("选择要加载的内容")
        self.result_loads = None
        checked = list(current) if current else list(bootstrap.DEFAULT_LOAD)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("选择需要加载的数据内容（可多选）："))
        self.boxes = []
        # 用 all_load_types()：基础类型 + 数据里实际存在的肉鸽季度（新季度自动出现）
        for load_type,title in bootstrap.all_load_types().items():
            box = QCheckBox(title)
            box.setChecked(load_type in checked)
            box.setProperty("load_type",load_type)
            layout.addWidget(box)
            self.boxes.append(box)
        self.remember = QCheckBox("记住本次选择")
        self.remember.setChecked(True)
        layout.addWidget(self.remember)
        layout.addSpacing(6)

        buttons = QDialogButtonBox()
        self.deploy_button = buttons.addButton("开始加载",QDialogButtonBox.AcceptRole)
        buttons.addButton("取消",QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.confirm)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def confirm(self):
        loads = [box.property("load_type") for box in self.boxes if box.isChecked()]
        if self.remember.isChecked():
            bootstrap.save_cache(loads)
        self.result_loads = loads
        self.accept()

    def exec(self):
        '''返回 loads 列表；用户取消时返回 None'''
        accepted = super().exec()
        if accepted == QDialog.Accepted:
            return self.result_loads
        return None
