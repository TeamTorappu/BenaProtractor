'''
打包脚本
用法：
    python packer.py            # 把 dist 里已经构建好的程序压成 output/贝娜的量角器 <日期> <后缀>.zip
    python packer.py --build    # 先调 PyInstaller 构建（默认 Qt 界面，onedir），再压缩
    python packer.py --build --legacy   # 构建旧 tkinter 版（onefile，体积小）

不想打成 zip、只想直接拷目录分发也可以：直接发 dist/BenaProtractor/ 整个文件夹，
注意里面不能带 .bena_ai.json / config.json / .bena_cache（可能含 API Key 与个人进度）。
'''
import argparse
import datetime
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "贝娜的量角器"
EXE_NAME = "BenaProtractor"

# 运行时需要随包分发的东西（引擎数据 tables/ 由用户首次启动时自行下载，不打包）
RUNTIME_FILES = [
    ("icon/icon.ico","icon/icon.ico"),
    ("translation/bena_dictionary.json","translation/bena_dictionary.json"),
    ("translation/anne_dictionary.json","translation/anne_dictionary.json"),
    ("dummy/global_buff_dummy.json","dummy/global_buff_dummy.json"),
    ("README.md","README.md"),
]

# 绝不能进包的东西
BLOCKED_NAMES = {".bena_ai.json",".bena_cache","config.json",".cache",".venv",".uvcache",
                 "__pycache__",".screenshots","tables",
                 # 开发用的目录：不随分发包发出去
                 "tests","tools",".git",".kilo","dist_lean","build",
                 # 开发文档也不发（README 是给用户的，另外两份是内部交接用的）
                 "HANDOVER.md","AI.md"}
BLOCKED_SUFFIXES = (".pyc",".pyo",".part",".log")


def zip_dir(zip_file,folder,arc_root):
    for root,dirs,files in os.walk(folder):
        dirs[:] = [name for name in dirs if name not in BLOCKED_NAMES]
        for name in files:
            if name in BLOCKED_NAMES or name.endswith(BLOCKED_SUFFIXES):
                continue
            full = os.path.join(root,name)
            relative = os.path.relpath(full,folder)
            zip_file.write(full,os.path.join(arc_root,relative))


# 界面实际只用到 QtCore/QtGui/QtWidgets/QtSvg/QtSvgWidgets/QtXml，
# 这些模块一个都不需要（收了的话 WebEngine 一个 dll 就 194MB）。
HEAVY_MODULES = [
    "PySide6.QtWebEngineCore","PySide6.QtWebEngineWidgets","PySide6.QtWebEngineQuick",
    "PySide6.QtQuick","PySide6.QtQuick3D","PySide6.QtQuickWidgets","PySide6.QtQuickControls2",
    "PySide6.QtQml","PySide6.QtDesigner","PySide6.QtUiTools","PySide6.QtPdf","PySide6.QtPdfWidgets",
    "PySide6.QtMultimedia","PySide6.QtMultimediaWidgets","PySide6.QtCharts","PySide6.QtDataVisualization",
    "PySide6.Qt3DCore","PySide6.Qt3DRender","PySide6.Qt3DInput","PySide6.Qt3DLogic","PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras","PySide6.QtOpenGL","PySide6.QtOpenGLWidgets","PySide6.QtSql","PySide6.QtTest",
    "PySide6.QtHelp","PySide6.QtBluetooth","PySide6.QtNfc","PySide6.QtSensors","PySide6.QtSerialPort",
    "PySide6.QtWebSockets","PySide6.QtWebChannel","PySide6.QtNetworkAuth","PySide6.QtRemoteObjects",
    "PySide6.QtPositioning","PySide6.QtLocation","PySide6.QtSpatialAudio","PySide6.QtTextToSpeech",
    "PySide6.QtScxml","PySide6.QtStateMachine","PySide6.QtConcurrent","PySide6.QtHttpServer",
    "PySide6.QtGraphs","PySide6.QtGraphsWidgets","PySide6.QtSerialBus","PySide6.QtVirtualKeyboard",
    # 注意：绝对不能排除 shiboken6.Shiboken——PySide6/__init__.py 自己要 import 它，
    # 排掉之后 PySide6 直接没法初始化（报 Unable to import Shiboken）。
    # 纯分析用不到的东西（打包机上有、运行不需要）
    "setuptools","pkg_resources","pip","wheel","PyInstaller",
    "pythonwin","win32com","win32comext","pywin32_system32","numpy","matplotlib",
]

# 这些文件即使被钩子收进来也可以删（软件 OpenGL 兜底、Qt 自带翻译、QML、没用到的 Qt 库）
# 说明：界面只用 QtCore/QtGui/QtWidgets/QtSvg/QtXml，且 tk 备用界面在 Qt 版里被排除；
# 已经实测删掉这些之后 exe 能正常启动、出图（tools/shot_ui.py + 打包版 --screenshot）。
STRIPPABLE_PATTERNS = [
    # 大件：软件渲染 / 引擎相关
    "opengl32sw.dll",              # 19.7MB：没有 GPU 加速时的软件渲染兜底
    "d3dcompiler_47.dll",
    "QtWebEngineProcess.exe",
    "qtwebengine_devtools_resources.pak","qtwebengine_resources.pak",
    "qtwebengine_resources_100p.pak","qtwebengine_resources_200p.pak",
    "icudtl.dat",
    # 用不到的 Qt 运行库（Qt6Quick/Qml/Pdf 会被 PySide6 钩子顺带收进来）
    "Qt6Quick.dll","Qt6Quick3D.dll","Qt6Qml.dll","Qt6QmlModels.dll","Qt6QmlWorkerScript.dll",
    "Qt6Pdf.dll","Qt6Designer.dll","Qt6DesignerComponents.dll","Qt6Help.dll","Qt6Sql.dll",
    "Qt6Test.dll","Qt6Multimedia.dll","Qt6Charts.dll","Qt6DataVisualization.dll",
    "Qt6Bluetooth.dll","Qt6Nfc.dll","Qt6Sensors.dll","Qt6SerialPort.dll","Qt6WebSockets.dll",
    "Qt6WebChannel.dll","Qt6Positioning.dll","Qt6Location.dll","Qt6TextToSpeech.dll",
    "Qt6ShaderTools.dll","Qt6QuickControls2.dll","Qt6QuickTemplates2.dll","Qt6QuickWidgets.dll",
    "Qt6VirtualKeyboard.dll","Qt6RemoteObjects.dll","Qt6Scxml.dll","Qt6StateMachine.dll",
    "Qt6Graphs.dll","Qt6SpatialAudio.dll","Qt6HttpServer.dll","Qt6SerialBus.dll",
    # tkinter 的运行时（Qt 版用不到；备用界面以源码方式运行）
    "tcl86t.dll","tk86t.dll","tcl8","tk8",
]
STRIPPABLE_DIRS = ["translations","qml","translations/qtwebengine_locales"]


def strip_dist(dist_dir,aggressive=True):
    '''删掉确定用不到的大文件，返回节省的字节数'''
    saved = 0
    if not aggressive:
        return saved
    for root,dirs,files in os.walk(dist_dir):
        for name in list(dirs):
            if name in STRIPPABLE_DIRS:
                target = os.path.join(root,name)
                saved += sum(os.path.getsize(os.path.join(dp,f))
                             for dp,_,fs in os.walk(target) for f in fs)
                shutil.rmtree(target,ignore_errors=True)
                dirs.remove(name)
        for name in files:
            if name in STRIPPABLE_PATTERNS:
                target = os.path.join(root,name)
                try:
                    saved += os.path.getsize(target)
                    os.remove(target)
                except OSError:
                    pass
    return saved


# 构建目录里必须有的运行期文件/文件夹
# （不复制进去的话，dist 里的 exe 直接双击就会闪退：引擎在 import 阶段就要读 translation/*.json）
RUNTIME_DIRS = ("translation","dummy","icon")


def install_runtime_files(dist_dir):
    '''把运行必需的文件复制进构建目录，让 dist 里的 exe 能直接跑

    以前只在打 zip 的时候才附带这些文件，导致「构建完成后直接运行 dist 里的 exe」必崩。
    '''
    copied = []
    for folder in RUNTIME_DIRS:
        source = os.path.join(ROOT,folder)
        if not os.path.isdir(source):
            print(f"[打包]警告：找不到 {folder}/，跳过了")
            continue
        target = os.path.join(dist_dir,folder)
        if os.path.exists(target):
            shutil.rmtree(target,ignore_errors=True)
        shutil.copytree(source,target,
                        ignore=shutil.ignore_patterns(*BLOCKED_NAMES,"*.pyc","*.part"))
        copied.append(folder + "/")
    for source,target in RUNTIME_FILES:
        if source.startswith(RUNTIME_DIRS):
            continue                      # 上面的整目录复制已经包含了
        full = os.path.join(ROOT,source)
        if os.path.exists(full):
            destination = os.path.join(dist_dir,target)
            os.makedirs(os.path.dirname(destination),exist_ok=True)
            shutil.copy2(full,destination)
            copied.append(target)
    print("[打包]已放入运行必需文件：" + "、".join(copied))
    return copied


def build(legacy=False,dist_name="dist",aggressive=True):
    command = [sys.executable,"-m","PyInstaller","--noconfirm","--clean",
               f"--name={EXE_NAME}"]
    if legacy:
        command += ["--onefile","--exclude-module","PySide6","--exclude-module","shiboken6",
                    "--exclude-module","qfluentwidgets"]
    else:
        # onedir：Qt 的插件与 DLL 太多，onefile 每次启动都要解包，慢且容易漏插件。
        # 注意不要用 --collect-all PySide6：那会把 632MB 的 PySide6 整个搬进来
        # （WebEngine 一个 dll 就 194MB），交给 PyInstaller 的 PySide6 钩子按需收集即可。
        command += ["--onedir"]
    command += ["--icon",os.path.join(ROOT,"icon","icon.ico")]
    command += ["--distpath",os.path.join(ROOT,dist_name),
                "--workpath",os.path.join(ROOT,"build"),
                "--specpath",os.path.join(ROOT,"build")]
    if not legacy:
        for module in HEAVY_MODULES:
            command += ["--exclude-module",module]
    command += [os.path.join(ROOT,"main.py")]
    print("[打包]运行：" + " ".join(command))
    result = subprocess.call(command,cwd=ROOT)
    if result != 0:
        raise SystemExit(f"[打包]PyInstaller 失败，退出码 {result}")
    dist_dir = os.path.join(ROOT,dist_name,EXE_NAME)
    if not legacy and aggressive:
        saved = strip_dist(dist_dir,aggressive=True)
        print(f"[打包]精简掉 {saved / (1024 * 1024):.1f} MB（软件渲染兜底 / Qt 翻译 / QML / ICU）")
    # 关键一步：把 translation/dummy/icon 等运行必需文件放进构建目录，
    # 这样 dist 里的 exe 可以直接双击运行，不必等打包成 zip
    install_runtime_files(dist_dir)
    return dist_dir


def sanity_check(dist_dir):
    '''确认包里没有混进游戏数据、缓存、私密配置，或开发用的目录'''
    forbidden = ["tables",".bena_cache",".uvcache","config.json",".bena_ai.json",".cache",
                 # 开发用的东西不该发给用户：测试与自查脚本、版本库、构建中间产物
                 "tests","tools",".git",".kilo","build",".screenshots"]
    problems = []
    for name in forbidden:
        if os.path.exists(os.path.join(dist_dir,name)):
            problems.append(name)
    for root,dirs,files in os.walk(dist_dir):
        for name in dirs:
            if name in ("tests","tools",".git"):
                problems.append(os.path.relpath(os.path.join(root,name),dist_dir))
        for name in files:
            if name in (".bena_ai.json","config.json") or name.endswith(".part"):
                problems.append(os.path.relpath(os.path.join(root,name),dist_dir))
    if problems:
        raise SystemExit("[打包]包里出现了不该有的文件，先清理：\n  " + "\n  ".join(problems))
    print("[打包]自检通过：不含游戏数据 / 缓存 / 配置文件 / 开发用目录（tests、tools 等）")


def make_zip(legacy=False,dist_name="dist"):
    if not os.path.exists(os.path.join(ROOT,"output")):
        os.makedirs(os.path.join(ROOT,"output"),exist_ok=True)
    today = datetime.datetime.now().strftime("%Y.%m.%d")
    suffix = "tk版" if legacy else "Qt版"
    zip_path = os.path.join(ROOT,"output",f"{APP_NAME} {today} {suffix}.zip")

    dist_dir = os.path.join(ROOT,dist_name,EXE_NAME)
    if not os.path.exists(dist_dir):
        raise SystemExit(f"[打包]找不到 {dist_dir}，先运行 python packer.py --build")
    sanity_check(dist_dir)

    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as zip_file:
        zip_dir(zip_file,dist_dir,APP_NAME)
        for source,target in RUNTIME_FILES:
            full = os.path.join(ROOT,source)
            if os.path.exists(full):
                zip_file.write(full,os.path.join(APP_NAME,target))
            else:
                print(f"[打包]警告：缺少 {source}，已跳过")
        # 附带一个说明，免得用户不知道数据要自己下
        readme = (f"{APP_NAME} - 使用说明\n"
                  "1. 请把整个文件夹解压出来再运行，不要只把 exe 单独拿出来：\n"
                  f"   运行 {EXE_NAME}.exe 时，它旁边必须有 _internal、translation、dummy、icon 这几个文件夹；\n"
                  f"2. 然后运行 {EXE_NAME}.exe；\n"
                  "3. 首次启动会自动下载《明日方舟》游戏数据（约 70MB+），请保持网络畅通；"
                  "下载支持断点续传，中途关掉再打开会接着下；\n"
                  "4. 下载慢或失败时，请先开启代理（俗称梯子）再重试；\n"
                  "5. AI 翻译需要自行填写接口地址、模型名与 API Key（本地模型可以留空）；\n"
                  "6. 本工具只做分析与翻译，不含任何编辑/私服功能。\n")
        zip_file.writestr(os.path.join(APP_NAME,"使用说明.txt"),readme)
    size = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[打包]完成：{zip_path}（{size:.1f} MB）")
    return zip_path


def main():
    parser = argparse.ArgumentParser(description="贝娜的量角器 打包工具")
    parser.add_argument("--build",action="store_true",help="先构建再压缩")
    parser.add_argument("--legacy",action="store_true",help="构建旧 tkinter 版（onefile，小体积）")
    parser.add_argument("--dist",default="dist",help="构建输出目录（默认 dist）")
    parser.add_argument("--keep-big",action="store_true",
                        help="不做精简（保留 opengl32sw.dll 等软件渲染兜底，体积会大 ~20MB）")
    parser.add_argument("--zip",action="store_true",help="构建完顺带压成 zip")
    args = parser.parse_args()
    if args.build:
        build(legacy=args.legacy,dist_name=args.dist,aggressive=not args.keep_big)
    if args.zip:
        make_zip(legacy=args.legacy,dist_name=args.dist)
    if not args.build and not args.zip:
        parser.print_help()


if __name__ == "__main__":
    main()
