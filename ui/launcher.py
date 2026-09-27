'''
启动器
负责：解析参数 → 选界面后端（Qt / tkinter）→ 初始化引擎 → 选择加载项 → 开窗
'''
import argparse
import os
import sys
import traceback


class SafeConsole:
    '''stdout/stderr 代理：编码编不出来的字符自动替换，绝不抛异常

    引擎（bena.py 等）里到处是 print，条目名里还有「²」这种字符；
    中文 Windows 的 cmd 是 GBK，输出被重定向到文件时更是如此，
    一旦 print 抛 UnicodeEncodeError，整个程序就会在启动阶段直接退出。
    '''

    def __init__(self,stream,encoding="utf-8"):
        self._stream = stream
        self._encoding = encoding

    def _fallback_stream(self):
        stream = self._stream
        for name in ("buffer","raw"):
            candidate = getattr(stream,name,None)
            if candidate is not None:
                return candidate
        try:
            return open(stream.fileno(),"wb",buffering=0)
        except Exception:
            return None

    def write(self,text):
        try:
            return self._stream.write(text)
        except UnicodeEncodeError:
            pass
        except (ValueError,OSError):
            return 0
        target = self._fallback_stream()
        data = str(text).encode(self._encoding,"replace")
        if target is None:
            return len(data)
        try:
            return target.write(data)
        except Exception:
            return len(data)

    def writelines(self,lines):
        for line in lines:
            self.write(line)

    def flush(self):
        try:
            self._stream.flush()
        except Exception:
            pass

    def isatty(self):
        try:
            return bool(self._stream.isatty())
        except Exception:
            return False

    def fileno(self):
        return self._stream.fileno()

    def __getattr__(self,item):
        return getattr(self._stream,item)


def force_utf8_console():
    '''把标准输出/错误切成「UTF-8 + 出错替换 + 永不抛异常」。

    引擎会打印大量中文与生僻符号（比如「²」），在 GBK 控制台或输出被重定向成文件时，
    print 会直接抛 UnicodeEncodeError 把程序带走；打包成 exe 后尤其容易遇到。
    '''
    for stream_name in ("stdout","stderr"):
        stream = getattr(sys,stream_name,None)
        if stream is None:
            continue
        if isinstance(stream,SafeConsole):
            continue
        reconfigure = getattr(stream,"reconfigure",None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8",errors="replace")
            except Exception:
                pass
        setattr(sys,stream_name,SafeConsole(stream))


force_utf8_console()


def install_excepthook():
    '''最后一道防线：任何未捕获异常都要能看见，别静默死掉。

    引擎里有大量 print，而中文 Windows 的 cmd / 重定向文件是 GBK 编码，
    遇到「²」这种字符会抛 UnicodeEncodeError；就算文本编不出来，也要把消息写出去。
    '''
    def _excepthook(exception_type,exception,tb):
        text = "".join(traceback.format_exception(exception_type,exception,tb))
        for stream_name in ("stderr","stdout"):
            stream = getattr(sys,stream_name,None)
            if stream is None:
                continue
            try:
                stream.write(text + "\n")
                return
            except Exception:
                pass
            try:
                # 编码不兼容时退回字节级写入，保证日志不丢
                stream.buffer.write(text.encode("utf-8","replace"))
                stream.buffer.flush()
                return
            except Exception:
                continue
        try:
            with open("bena_error.log","a",encoding="utf-8") as file:
                file.write(text + "\n")
        except Exception:
            pass

    sys.excepthook = _excepthook


install_excepthook()

# 引擎里到处用的是相对路径（./tables、./translation ...），所以必须先把工作目录钉在
# 「程序所在目录」：源码运行时是仓库根目录，打包（PyInstaller）后是 exe 所在目录。
def runtime_root():
    if getattr(sys,"frozen",False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_ROOT = runtime_root()
if _ROOT not in sys.path:
    sys.path.insert(0,_ROOT)
os.chdir(_ROOT)

# 运行必需的数据文件（都在「程序所在目录」下）。
# 引擎在 import 阶段就会读 translation/*.json，缺文件会直接抛异常闪退，
# 所以这里先检查一遍，给出能看懂的中文提示。
REQUIRED_FILES = (
    "translation/bena_dictionary.json",
    "translation/anne_dictionary.json",
    "dummy/global_buff_dummy.json",
)


def missing_required_files(root=None):
    root = root or _ROOT
    missing = []
    for relative in REQUIRED_FILES:
        if not os.path.exists(os.path.join(root,relative)):
            missing.append(relative)
    return missing


def show_fatal(message,title="贝娜的量角器 - 无法启动"):
    '''不依赖任何 GUI 工具包的致命错误提示（Windows 上用系统 MessageBox）'''
    print(f"[量角器]{title}：{message}",file=sys.stderr)
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,message,title,0x10)   # MB_ICONERROR
        return
    except Exception:
        pass
    try:
        import tkinter
        from tkinter import messagebox
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror(title,message)
        root.destroy()
    except Exception:
        pass


def preflight(root=None):
    '''返回 True 表示可以继续启动'''
    missing = missing_required_files(root)
    if not missing:
        return True
    frozen = bool(getattr(sys,"frozen",False))
    lines = ["缺少运行所需的文件："] + ["　· " + name for name in missing]
    if frozen:
        lines += ["",
                  "分发包必须整目录一起用：",
                  "　· 只把 BenaProtractor.exe 单独拿出来是不能运行的，",
                  "　　它旁边还要有 _internal 文件夹、translation 文件夹、dummy 文件夹。",
                  "　· 正确的做法是把压缩包里的整个文件夹解压出来，再运行里面的 exe。"]
    else:
        lines += ["","请在项目根目录（含 translation/ 与 dummy/ 的那一层）运行本程序。"]
    lines += ["",f"当前程序目录：{root or _ROOT}"]
    show_fatal("\n".join(lines))
    return False


import bootstrap  # noqa: E402

DEFAULT_UI = "qt"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="贝娜的量角器：明日方舟机制/藏品翻译分析工具")
    parser.add_argument("--ui",choices=["qt","tk"],default=None,
                        help="界面后端：qt（默认，Fluent 界面）／tk（旧 tkinter 界面，备用）")
    parser.add_argument("--yes",action="store_true",
                        help="跳过「选择要加载的内容」对话框，直接用记住的选择（没有则用默认选择）")
    parser.add_argument("--loads",default=None,
                        help="直接指定要加载的内容，逗号分隔，例如 buff,buff_template,rogue_6")
    parser.add_argument("--screenshot",default=None,
                        help="启动后把界面渲染成 PNG（用于 UI 自查），值是输出文件路径")
    parser.add_argument("--attach",action="store_true",
                        help="配合 --screenshot：额外用 PrintWindow 抓一次带标题栏的真窗（Windows）")
    parser.add_argument("--id",default=None,
                        help="配合 --screenshot：启动后自动展示指定条目，例如 buff.ChargeBuff")
    parser.add_argument("--exit-after-screenshot",action="store_true",
                        help="截图完成后直接退出（自动化用）")
    return parser.parse_args(argv)


def choose_backend(requested):
    '''返回 (后端名, 提示信息列表)。requested 为 None 时读 config.json

    qt -> Fluent 界面（PySide6 + QFluentWidgets）；没有 QFluentWidgets 就退回 tk 备用界面。
    '''
    notes = []
    config = bootstrap.load_config()
    backend = requested or config.get("ui") or DEFAULT_UI
    if backend not in ("qt","tk"):
        notes.append(f"配置里的界面后端 {backend!r} 不认识，改用 {DEFAULT_UI}")
        backend = DEFAULT_UI
    if backend == "qt":
        try:
            import PySide6  # noqa: F401
            import qfluentwidgets  # noqa: F401
        except ImportError as error:
            notes.append(f"缺少 Qt 依赖（{error.name}），本次使用 tkinter 备用界面。"
                         "想要新界面请运行：pip install -r requirements.txt")
            backend = "tk"
    return backend, notes


def build_ui(backend):
    '''实例化界面对象（此时还没有建立目录）'''
    if backend == "qt":
        from ui.qt_ui import FluentProtractor
        return FluentProtractor()
    from ui.tk_ui import Protractor
    return Protractor()


def ask_loads(ui, backend):
    '''弹选择对话框；用户取消则返回 None'''
    remembered = bootstrap.load_cache() if os.path.exists(bootstrap.CACHE) else None
    if backend == "qt":
        from ui.qt_selector import QtSelector
        selector = QtSelector(parent=ui.window if getattr(ui,"window",None) else None,
                              current=remembered)
        return selector.exec()
    from ui.tk_selector import TkSelector
    selector = TkSelector(parent=ui.window,current=remembered)
    return selector.exec()


def resolve_loads(args, ui, backend):
    if args.loads:
        loads = [item.strip() for item in args.loads.split(",") if item.strip()]
        bootstrap.save_cache(loads)
        return loads
    if args.yes:
        if os.path.exists(bootstrap.CACHE):
            return bootstrap.load_cache()
        loads = list(bootstrap.DEFAULT_LOAD)
        bootstrap.save_cache(loads)
        return loads
    # 与旧版本一致：只有没记住过选择时才弹对话框
    if os.path.exists(bootstrap.CACHE):
        return bootstrap.load_cache()
    loads = ask_loads(ui,backend)
    if loads is None:
        return None
    bootstrap.save_cache(loads)
    return loads


def describe_error(error):
    text = f"{type(error).__name__}: {error}"
    if isinstance(error,IOError) and "缺少文件" in str(error):
        text += "\n\n游戏数据没下载全。请检查网络（必要时开代理）后重试。"
    return text


def prepare_missing_data(ui):
    '''把缺的游戏数据下下来。返回 True 表示下齐了。

    Qt 版：弹一个带进度条与取消按钮的对话框（下载在子线程里）；
    其它后端：退回控制台进度 + 标题栏提示。
    '''
    import downloader
    missing = downloader.missing_files()
    print("[量角器]缺少数据文件：" + "、".join(missing))
    if hasattr(ui,"prepare_data_dialog"):
        while True:
            ok,message = ui.prepare_data_dialog(missing)
            if ok and not downloader.missing_files():
                return True
            if ok and downloader.missing_files():
                message = "下载流程结束了，但文件仍然不齐，请重试。"
            if message == "已取消":
                if not ui.confirm_retry("取消下载","要重新开始下载吗？（支持断点续传）"):
                    return False
                continue
            if not ui.confirm_retry("数据下载失败",message or "未知错误"):
                return False
    # 没有对话框的后端
    try:
        bootstrap.download_data(lambda stage,current,total: ui.set_status(stage,current,total)
                                if hasattr(ui,"set_status") else None)
    except Exception as error:
        print("[量角器]下载失败："+describe_error(error))
        return False
    return not downloader.missing_files()


def main(argv=None):
    args = parse_args(argv)
    if not preflight():
        return 2
    backend, notes = choose_backend(args.ui)
    for note in notes:
        print("[量角器]"+note)

    # 界面必须先建起来：引擎初始化可能很慢，需要有个东西能显示进度
    try:
        ui = build_ui(backend)
    except Exception as error:
        print("[量角器]界面初始化失败：")
        traceback.print_exc()
        if backend == "qt":
            print("[量角器]尝试退回 tkinter 界面")
            backend = "tk"
            ui = build_ui(backend)
        else:
            raise
    bootstrap.set_ui(ui)

    # 首次运行：先把游戏数据下载齐（约 70MB+，支持断点续传）
    import downloader
    while downloader.missing_files():
        if not prepare_missing_data(ui):
            print("[量角器]缺少游戏数据，退出。")
            if hasattr(ui,"close"):
                ui.close()
            return 1

    # 引擎初始化（读取干员/敌人名称表）
    def progress(stage,current=0,total=0):
        if hasattr(ui,"set_status"):
            ui.set_status(stage,current,total)

    try:
        bootstrap.init_engine(progress,skip_download=True)
    except Exception as error:
        message = describe_error(error)
        print("[量角器]初始化失败："+message)
        traceback.print_exc()
        if hasattr(ui,"show_error"):
            ui.show_error("初始化失败",message)
        else:
            raise
        return 1

    # 选择加载项 + 建立目录
    loads = resolve_loads(args,ui,backend)
    if loads is None:
        print("[量角器]用户取消了加载选择，退出。")
        if hasattr(ui,"close"):
            ui.close()
        return 0
    bootstrap.start_with(loads,ui)

    if args.id and hasattr(ui,"display_by_id"):
        if not ui.display_by_id(args.id):
            print(f"[量角器]没找到条目 {args.id}")
            if hasattr(ui,"set_status"):
                ui.set_status(f"没找到条目 {args.id}")

    # 截图模式：交给界面自己在窗口显示后处理
    if args.screenshot:
        if not hasattr(ui,"schedule_screenshot"):
            print("[量角器]当前界面后端不支持 --screenshot")
        else:
            ui.schedule_screenshot(args.screenshot,
                                   attach=args.attach,
                                   quit_after=args.exit_after_screenshot)

    ui.open()
    return 0


if __name__ == "__main__":
    sys.exit(main())
