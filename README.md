《贝娜的量角器》注意事项及声明

1.《贝娜的量角器》为分析工具与翻译工具，旨在为普通玩家提供阅读机制和算法的渠道，其中不包含也没有任何计划包含编辑功能，亦不支持任何与“私服”相关的项目。我们坚决反对一切私服行为。

2.目前贝娜的量角器中出现的数值大多均为默认数据，详细数据可能受给定黑板的制约。

3.明日方舟体量庞大且杂乱，而贝娜仍处于早期版本，Node翻译与藏品机制的翻译仍需大量人力工作量，如果希望帮助此项目，欢迎提交pr。

4.若启动后发现无法下载数据/下载数据缓慢，请尝试开启梯子。

---

## 运行

界面是 **Qt（PySide6 + QFluentWidgets）** 的 Fluent 风格界面；旧的 tkinter 界面保留作备用。
左侧导航按数据类型分页，**只显示你这次勾选加载的类型**；右侧是「条目列表 | 译文/原文」和可自由拖拽宽度的 **AI 侧栏**。

```bat
:: 1) 安装依赖（建议装在项目里的虚拟环境）
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

:: 2) 启动
run.bat                  :: 默认 Fluent 界面
run.bat tk               :: 旧 tkinter 界面（备用）
python main.py           :: 等价于 run.bat
python main.py --ui tk   :: 等价于 run.bat tk
```

没有 PySide6 / QFluentWidgets 时会自动退回 tkinter 界面并在控制台说明原因，
也可以用 `python tools\launch.py --setup` 一键补依赖。

常用参数：

| 参数 | 作用 |
| --- | --- |
| `--ui qt` / `--ui tk` | 选择界面后端（默认 qt；缺依赖会自动退回 tk） |
| `--yes` | 跳过「选择要加载的内容」，直接用上次记住的选择 |
| `--loads buff,rogue_6` | 直接指定要加载的内容（逗号分隔），并记住 |
| `--id buff.stun` | 启动后直接展示某个条目（`类型.key`） |
| `--screenshot 路径.png` | 启动后把界面渲染成 PNG（自查/自动化用） |

**首次启动会自动下载游戏数据**（约 70MB+，来自 Kengxxiao/ArknightsGameData）。
下载在子线程里跑，界面上有进度条与取消按钮，**支持断点续传**：
中途关掉程序、重开还会从上次的位置接着下。下载慢或失败时先开代理再重试。

界面小贴士：

- 左下角「设置」里有四个分区：**外观**（主题/字号/目录密度）、**数据**（加载项、数据状态、分栏复位、打开配置）、**配色**（配色方案 + 逐项取色入口）、**关于**。
- 左下角「AI 助手」集中放模型接口配置与翻译记录统计；侧栏的「AI 设置」按钮也会切到这一页。
- 窗口大小、位置、最大化状态、每个页面的分栏比例、侧栏显示状态与宽度都会记住；侧栏宽度直接拖分隔条即可。
- 快捷键：`Ctrl+F` 搜索、`Esc` 清空搜索、`F5` 重新选择加载内容、`Ctrl+=` / `Ctrl+-` / `Ctrl+0` 调字号、`Ctrl+Shift+C` 复制全文。
- 搜索框空格分词，多个关键词需同时满足；目录右上角可切换「默认顺序 / 按名称 / 按 ID」，匹配到的关键词会在行内高亮。
- 标题旁边会显示当前条目还有多少处未译片段（`N 处待译`）。

## 颜色分级

界面配色集中在一个地方：`ui/palette.py`（唯一允许写十六进制颜色的 UI 模块），按语义分五级：

| 层级 | token | 用在哪 |
| --- | --- | --- |
| L0 底色 | `surface.window/card/inset/border` | 页面、卡片、列表、树、消息区、描边（统一底色，不会一块块拼色） |
| L1 结构 | `text.depth1..4`、`text.secondary/muted/faint` | 译文树按深度做灰阶（第 1 层还加粗），备注/面包屑用弱色 |
| L2 类型 | `type.buff/template/global/relic` | 目录条目按数据类型配色 + 前缀图标 |
| L3 语义值 | `value.key/text/number/placeholder/reference/unit` | `键 : 值` 里键压灰、值加深；`[黑板变量]` 青、`<Buff引用>` 蓝、数字橙 |
| L4 状态 | `state.pending/running/ok/error`、`chat.me/ai`、`search.hit` | 待译/翻译中/已应用/失败、`[我]`/`[AI]`、搜索命中 |

原文面板（JSON）也有语法高亮：键名、字符串、数字、`true/false`、括号各一色（`ui/json_highlight.py`）。

自定义方式（两种都行）：

1. **界面**：左下角「颜色」→ 选预设或逐个取色，自动写进 `config.json`。
2. **配置文件**：`config.json` 的 `colors` 一节

```json
"colors": {
  "preset": "default",
  "overrides": {
    "value.number": ["#C2410C", "#FFB86B"],
    "surface.card": "#FFFFFF"
  }
}
```

`overrides` 里给 `[亮色, 暗色]` 两个值最精确；只给一个颜色时，另一套会按明度自动推导。
改完重启程序即可（「颜色」页改的话是立刻生效）。

想让自己加的颜色也参与「亮/暗自动切换」，只要在 `ui/palette.py` 的 `TOKEN` 里按 `_t(名字, 亮色, 暗色)` 加一行。

## AI 翻译讲解

选中条目后，右侧「AI 翻译 / 讲解」侧栏会列出这个条目里**引擎没翻出来的片段**
（`（未翻译）`、纯英文标识等）。可以逐个点「翻译」，也可以点顶部的**「全部翻译」**
一次把当前条目所有待译片段顺序翻完（可随时「停止」），再点「全部应用」一次性写回译文树
（显示为 `中文译名（原标识）`，随时可以再点右键重新翻译）。每张片段卡片上还有「定位」，
能直接在译文树里展开并滚到对应那一行。

- 支持任何 OpenAI 兼容接口：DeepSeek / 硅基流动 / Ollama / LM Studio…
  在「AI 助手」页（或侧栏的「AI 设置」）里填 `base_url`、模型名与 API Key（本地模型可留空）。
- 消息区用 `[我]`（蓝）与 `[AI]`（绿）区分提问和回答，回答紧跟在 `[AI]` 后面流式出字。
- AI 结果只写 `.bena_cache/ai/`，**不会**自动改 `translation/*.json`；
  「导出条目」可以把当前条目的完整译文导出成 Markdown（同时复制到剪贴板），
  「导出翻译记录」导出缓存表格，都可以拿去人工提 PR。
- 配置与缓存文件都在仓库根目录、已被 gitignore，也不会打进分发包。
- 详细设计、拓展方式与测试说明见 [AI.md](AI.md)。

## 打包分发（可选，目前没在用）

平时直接源码运行即可；要出分发包时：

```bat
pack.bat           :: Fluent 版（onedir，推荐：单目录多文件，启动快、Qt 插件不会漏）
pack.bat legacy    :: 旧 tkinter 版（onefile，单文件但体积大、启动要解包）
```

产物在 `output\`，用 venv 里的 `pyinstaller`（`pip install pyinstaller`）。

**构建出的 `dist\BenaProtractor\` 现在可以直接运行**：构建完会把 `translation\`、`dummy\`、`icon\` 一并放进该目录
（以前只在打 zip 时才附带，导致直接双击 `dist` 里的 exe 会闪退 —— 引擎在 import 阶段就要读 `translation/*.json`）。
分发/挪动时务必**整目录一起**，只拿 exe 是跑不起来的；如果真的少了文件，程序会弹窗列出来缺哪几个。

**体积**：完整 PySide6 全收是 247MB，现在是 **76MB**，做法都在 `packer.py` 里：

1. **不要 `--collect-all PySide6`**（这一条省了约 150MB）。界面实际只用 QtCore / QtGui /
   QtWidgets / QtSvg / QtSvgWidgets / QtXml，交给 PyInstaller 的 PySide6 钩子按需收集即可。
   被带进来的 `Qt6WebEngineCore.dll` 一个文件就有 194MB。
2. `HEAVY_MODULES` 里逐个 `--exclude-module`（WebEngine / Quick / Qml / Designer / Pdf /
   Multimedia / Charts / 3D / Sql / Test / Help / 蓝牙 / 串口 / WebSocket / VirtualKeyboard…）。
   ⚠️ **不能排除 `shiboken6.Shiboken`**，PySide6 自己要 import 它，排掉之后界面直接起不来。
3. `strip_dist()` 在构建后删掉确定用不到的大文件：`opengl32sw.dll`（19.7MB 软件渲染兜底）、
   Qt 自带翻译、QML 目录、`icudtl.dat`、`Qt6Quick/Qml/Pdf/...`、`tcl86t/tk86t.dll`（Qt 版用不到）。
   这一步就是日志里的「精简掉 46.6 MB」。
4. `--keep-big` 可以关掉第 3 步（体积 +20MB 左右），换来「没有 GPU 加速的机器也能软件渲染」的兜底。

打包时 `packer.py` 会做一次自检：**包里不允许出现** `tables\`（游戏数据）、
`.bena_cache\`、`config.json`、`.bena_ai.json`（可能含 API Key）。
也就是说分发包里只有程序本体 + 词典/占位数据，游戏数据一律由用户首次启动时自行下载。

## 故障排查

| 现象 | 原因 / 处理 |
| --- | --- |
| 启动报「缺少 PySide6/QFluentWidgets」并进了 tk 界面 | 依赖没装，`pip install -r requirements.txt` |
| 界面控件绘制时闪退（0xC0000005 访问冲突） | 本机 QFluentWidgets 的 `TreeWidget` 与 Qt 版本不兼容；程序会自动探测并降级为原生 `QTreeWidget`（外观几乎一致），探测结果缓存在 `.bena_cache/ui/`。可 `python tools\probe_treewidget.py --force` 重测 |
| 点「测试连接」后终端打印 `QThread: Destroyed while thread is still running` 并整个进程退出 | 已修：测试用的线程现在挂在窗口上、并等到 `finished` 才释放引用；连线程的取消事件也提前建好。回归测试：`python tools\test_ai_thread_lifetime.py`（慢请求中关窗口）、`python tools\test_ai_settings.py`（没填 key 就点测试） |
| 左侧导航里少了几个类型 | 现在只显示本次勾选加载的类型；缺哪个就在「设置 → 数据 → 选择加载内容」里勾上 |
| `config.json` 读取失败 | 该文件必须是无 BOM 的 UTF-8，删掉重建即可（程序会自动生成默认配置） |
| 跑完诊断脚本后主题/配色被改了 | 已修：`tools/` 下的脚本现在统一走 `guard_config`，进出各自还原配置，并且进程崩溃也有兜底。可用 `python tools\guard_config.py` 体检当前配置 |
| 下载很慢/失败 | 开代理后重试；已下载的部分会保留，续传即可 |

## 目录结构速览

```
main.py              入口（转调 ui/launcher.py）
bootstrap.py         引擎装配：下载、名称表、建立目录、config.json
bena.py / anne.py    分析组件（贝娜）与翻译组件（安妮）——与界面无关
data_class.py        数据类（Node / Buff / 藏品…）
translation/         人工维护的词典（bena_dictionary.json / anne_dictionary.json）
node_translator/     Node 伪代码 → 人话（安妮）
relic_translator/    藏品效果 → 人话（安妮）
downloader.py        游戏数据下载（断点续传 + 进度回调）
ui/launcher.py       选界面后端 → 初始化引擎 → 选加载项 → 开窗
ui/qt_ui.py          Fluent 主界面（数据页 / 导航 / 配色 / 几何持久化）
ui/qt_settings_page.py  设置页（外观 / 数据 / 配色 / 关于）
ui/qt_ai_page.py     AI 助手页（接口配置 + 翻译记录）
ui/qt_ai_sidebar.py  AI 侧栏（单条翻译 / 全部翻译 / 全部应用 / 定位 / 导出）
ui/qt_colors_page.py 逐项取色页（35 个语义颜色）
ui/qt_search.py      搜索防抖
ui/qt_widgets.py     Fluent 控件兼容层 + 卡片配色适配（bena_card_style）
ui/qt_tree.py        译文树控件 + 委托（含 TreeWidget 可用性探测）
ui/treemodel.py      译文 → 树节点数据、搜索匹配（不依赖 Qt，可单测）
ui/tk_ui.py          旧 tkinter 界面（备用）
ai/                  AI 翻译/讲解（Provider、提示词、片段收集、装饰与缓存）
tools/               自查工具（逐页出图、边界用例、过渡体检、假 AI 服务…）
tests/run_tests.py   冒烟测试（纯标准库，不联网；139 个用例）
```


