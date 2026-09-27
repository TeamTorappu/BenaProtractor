'''
UI 自查截图工具
- capture_widget：纯 Qt 渲染，不依赖窗口被真实显示（可离屏）
- capture_window_hwnd：用 ctypes 抓取真实窗口（含标题栏），需要窗口真的显示出来
- render_state_sequence：连续渲染多个状态并出图
'''
import ctypes
import ctypes.wintypes
import os
import sys
import time


def ensure_dir(path: str):
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)


def capture_widget(widget, path: str, scale: float = 1.0) -> str:
    '''把控件渲染成 PNG（离屏可用）。返回实际写入的路径。'''
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap

    ensure_dir(path)
    pixmap: QPixmap = widget.grab()
    if scale != 1.0:
        pixmap = pixmap.scaled(
            int(pixmap.width() * scale), int(pixmap.height() * scale),
            Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if not pixmap.save(path, "PNG"):
        raise IOError(f"截图保存失败：{path}")
    return path


def capture_window_hwnd(title: str, path: str) -> str:
    '''按窗口标题抓真窗（含非客户区）。仅 Windows 可用。

    用 PrintWindow 的 PW_RENDERFULLCONTENT(2) 标志，否则 DWM 合成的内容会是黑的。
    '''
    if sys.platform != "win32":
        raise RuntimeError("capture_window_hwnd 仅支持 Windows")
    from PySide6.QtGui import QImage

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    hwnd = user32.FindWindowW(None, title)
    if not hwnd:
        raise RuntimeError(f"找不到标题为 {title!r} 的窗口")

    # 抓之前先置顶并稍等，避免抓到未绘制完成/还在播放展开动画的画面
    user32.SetForegroundWindow(hwnd)
    time.sleep(1.2)

    rect = ctypes.wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError("GetWindowRect 失败")
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    if width <= 0 or height <= 0:
        raise RuntimeError(f"窗口尺寸异常：{width}x{height}")

    hdc_window = user32.GetWindowDC(hwnd)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_window)
    hbitmap = gdi32.CreateCompatibleBitmap(hdc_window, width, height)
    gdi32.SelectObject(hdc_mem, hbitmap)
    try:
        if not user32.PrintWindow(hwnd, hdc_mem, 2):
            raise RuntimeError("PrintWindow 失败（可能窗口未响应）")
        # 用 QImage 接管这块 DIB 的像素
        image = QImage(width, height, QImage.Format_RGB32)
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize", ctypes.wintypes.DWORD),
                ("biWidth", ctypes.wintypes.LONG),
                ("biHeight", ctypes.wintypes.LONG),
                ("biPlanes", ctypes.wintypes.WORD),
                ("biBitCount", ctypes.wintypes.WORD),
                ("biCompression", ctypes.wintypes.DWORD),
                ("biSizeImage", ctypes.wintypes.DWORD),
                ("biXPelsPerMeter", ctypes.wintypes.LONG),
                ("biYPelsPerMeter", ctypes.wintypes.LONG),
                ("biClrUsed", ctypes.wintypes.DWORD),
                ("biClrImportant", ctypes.wintypes.DWORD),
            ]

        class BITMAPINFO(ctypes.Structure):
            _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", ctypes.wintypes.DWORD * 3)]

        info = BITMAPINFO()
        info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height  # 负数 = 自上而下
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = 0  # BI_RGB

        buffer = ctypes.create_string_buffer(width * height * 4)
        got = gdi32.GetDIBits(hdc_mem, hbitmap, 0, height, buffer, ctypes.byref(info), 0)
        if not got:
            raise RuntimeError("GetDIBits 失败")
        # 直接拷进 QImage 的缓冲区（from_buffer 拿到可写地址再拷贝）
        ctypes.memmove(ctypes.addressof(ctypes.c_char.from_buffer(image.bits())), buffer, width * height * 4)
    finally:
        gdi32.DeleteObject(hbitmap)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(hwnd, hdc_window)

    ensure_dir(path)
    if not image.save(path, "PNG"):
        raise IOError(f"截图保存失败：{path}")
    return path


def render_state_sequence(app, window, states, out_dir: str):
    '''states 形如 [("empty", callable), ("selected", callable), ...]

    每个 state 的回调会在出图前被调用，用来摆好界面状态。
    返回 [(state_name, path), ...]
    '''
    results = []
    for name, prepare in states:
        if prepare is not None:
            prepare()
        app.processEvents()
        # 多转几轮事件循环，等布局/委托测高完成
        for _ in range(6):
            app.processEvents()
            time.sleep(0.08)
        path = os.path.join(out_dir, f"{name}.png")
        capture_widget(window, path)
        results.append((name, path))
    return results
