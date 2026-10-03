'''
《贝娜的量角器》入口
具体流程都在 ui/launcher.py：解析参数 → 选界面后端 → 初始化引擎 → 选择加载项 → 开窗
用法：
    python main.py                 默认 Qt 界面
    python main.py --ui tk         使用旧的 tkinter 界面（备用）
    python main.py --yes           跳过加载选择，直接用记住的选择
'''
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0,_ROOT)

from ui.launcher import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
