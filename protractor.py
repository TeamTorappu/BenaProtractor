'''
量角器（兼容入口）
旧的 protractor.py 里直接 import 会创建 tkinter 主窗口，现在这件事交给 ui.launcher。
这里只保留同名的 re-export，保证 `from protractor import PROTRACTOR` 这类老写法不会直接报错。
'''
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0,_ROOT)

from ui.tk_ui import Protractor, Displayview  # noqa: E402

# 当前挂着的界面实例（由 ui.launcher 在选定后端后赋值）
PROTRACTOR = None


def bind(ui):
    '''把一个界面实例登记为全局单例'''
    global PROTRACTOR
    PROTRACTOR = ui
    return PROTRACTOR


__all__ = ["Protractor", "Displayview", "PROTRACTOR", "bind"]
