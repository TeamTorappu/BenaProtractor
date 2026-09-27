'''
配色分级：全项目唯一的语义色板
界面里任何地方要上色，都从这里按语义 token 取，别再散落写十六进制。

分五级：
  L0 底色  surface.window / card / inset / border —— 统一背景，避免几层底色拼在一起
  L1 结构  text.depth1/2/3       —— 靠明度区分层级/主次
  L2 类型  type.buff / template / global / relic
  L3 语义值 value.number / placeholder / reference / key / unit / meta
  L4 状态  state.pending / running / ok / error、chat.*、search.hit

用户自定义（存在 config.json 的 "colors" 里）：
    {"preset": "arknights",
     "overrides": {"value.number": ["#C2410C", "#FFB86B"]}}   # [亮色, 暗色]
    {"preset": "custom",
     "overrides": {"value.number": "#C2410C"}}               # 也可以只给当前这一套

约束：
1. 每个 token 都有亮/暗两个值，取色按当前主题现场决定，切主题后新绘制立刻正确；
2. 不 import 任何 GUI（QColor 取不到就返回 None）；
3. 颜色只影响显示，绝不影响引擎输出的文本。
'''
import re

TOKEN = {}


def _t(name,light,dark):
    TOKEN[name] = (light,dark)


# ----------------------------------------
# L0 底色：统一背景（默认跟随 Fluent 主题，可被用户覆盖）
# ----------------------------------------
_t("surface.window", "#F3F3F3","#202020")   # 窗口/页面底色
_t("surface.card",   "#FFFFFF","#2B2B2B")   # 卡片、列表、树、输入框
_t("surface.inset",  "#FAFAFA","#262626")   # 内嵌区域（消息区）
_t("surface.border", "#E5E5E5","#3A3A3A")   # 分隔线/描边
# 目录/列表的交互态：Fluent 自带的选中底色很淡，配上我们自己的目录底色几乎看不出来，
# 所以显式定义两个 token，让「读到哪一行」在明暗两套主题下都一眼可辨。
_t("surface.hover",  "#F0F0F0","#333333")   # 鼠标悬浮
_t("surface.selected","#DCE9F7","#3B4A5A")  # 选中行

# ----------------------------------------
# L1 结构：层级与主次
# ----------------------------------------
_t("text.primary",   "#1B1B1B","#F3F3F3")
_t("text.secondary", "#575757","#C3C3C3")
_t("text.muted",     "#8A8A8A","#8F8F8F")   # 备注、注释
_t("text.faint",     "#A9A9A9","#787878")   # 面包屑、最弱提示
_t("text.depth1",    "#1B1B1B","#F3F3F3")   # 译文树第 1 层
_t("text.depth2",    "#3D3D3D","#DCDCDC")   # 第 2 层
_t("text.depth3",    "#5A5A5A","#B9B9B9")   # 第 3 层
_t("text.depth4",    "#757575","#9A9A9A")   # 第 4 层及更深

# ----------------------------------------
# L2 类型：这是什么东西
# ----------------------------------------
_t("type.buff",     "#0F7B34","#6CCB5F")   # 常见 Buff
_t("type.template", "#6B3FA0","#C79BE8")   # Buff 模板（机制底层）
_t("type.global",   "#B26A00","#EFB45C")   # 全局 Buff（藏品/关卡机制）
_t("type.relic",    "#0F6CBD","#6CB8F6")   # 肉鸽物品（藏品/钱/券…）

# ----------------------------------------
# L3 语义值：值本身是什么
# ----------------------------------------
_t("value.number",      "#C2410C","#FFB86B")   # 数字
_t("value.placeholder", "#0E7490","#5EEAD4")   # [黑板变量]
_t("value.reference",   "#1D4ED8","#93C5FD")   # <Buff 引用>（可转跳）
_t("value.text",        "#243B53","#E4E7EB")   # 文本值（键弱值实）
_t("value.key",         "#4B5563","#9CA3AF")   # "键 : 值" 里的键
_t("value.unit",        "#6B7280","#A1A1AA")   # 秒/层/倍/个
_t("value.meta",        "#8A8A8A","#8F8F8F")   # （读取自数据库）之类的说明

# ----------------------------------------
# L4 状态：现在什么情况
# ----------------------------------------
_t("state.pending", "#B26A00","#EFB45C")   # 待翻译
_t("state.running", "#0F6CBD","#6CB8F6")   # 翻译中
_t("state.ok",      "#0F7B34","#6CCB5F")   # 成功 / 已应用
_t("state.error",   "#C62828","#FF6B6E")   # 失败
_t("chat.me",       "#0F6CBD","#6CB8F6")   # [我]
_t("chat.ai",       "#0F7B34","#6CCB5F")   # [AI]
_t("search.hit",    "#B26A00","#FFD166")   # 搜索命中

# ----------------------------------------
# 原文面板：JSON 语法高亮
# ----------------------------------------
_t("json.key",    "#0F6CBD","#6CB8F6")
_t("json.string", "#0F7B34","#8FD98F")
_t("json.number", "#C2410C","#FFB86B")
_t("json.bool",   "#6B3FA0","#C79BE8")
_t("json.punct",  "#8A8A8A","#8F8F8F")

# 缺 token 时的兜底（别让界面因为拼错 token 崩掉）
FALLBACK = ("#333333","#DDDDDD")
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_CACHE = {}
_OVERRIDES = {}          # token -> (light, dark)，用户自定义优先


# ----------------------------------------
# 预设：用户可以在「外观 → 颜色」里一键切换
# ----------------------------------------
def _preset(label,**tokens):
    '''写一套预设：键名里的 __ 会换成 . （例如 surface__window → surface.window）

    只写需要覆盖的 token，其余沿用默认值（apply_overrides 是「叠加」而不是「替换」）。
    '''
    return {"label" : label,
            "overrides" : {key.replace("__",".") : value for key,value in tokens.items()}}


PRESETS = {
    "default" : _preset("默认（跟随系统）"),

    "arknights" : _preset(
        "暖夜（低亮度护眼）",
        surface__window=("#F5F1EA","#1B1B1F"),
        surface__card=("#FFFFFF","#26262C"),
        surface__inset=("#FAF7F2","#212127"),
        surface__border=("#E6DFD2","#3A3A44"),
        text__primary=("#241F1A","#F2EDE6"),
        text__secondary=("#5C5348","#C6BFB4"),
        text__depth2=("#453C31","#DED6C9"),
        text__depth3=("#635748","#B7AE9F"),
        text__depth4=("#7D7264","#968D80"),
        type__buff=("#2E7D32","#7BD389"),
        type__global=("#B2691F","#F0B45C"),
        value__text=("#2B2622","#EDE6DC"),
        value__key=("#7A6F60","#A79C8B"),
    ),

    "highcontrast" : _preset(
        "高对比（久读）",
        surface__window=("#FFFFFF","#101010"),
        surface__card=("#FFFFFF","#1A1A1A"),
        surface__inset=("#F7F7F7","#141414"),
        surface__border=("#D0D0D0","#3F3F3F"),
        text__depth1=("#000000","#FFFFFF"),
        text__depth2=("#1A1A1A","#EDEDED"),
        text__depth3=("#333333","#D2D2D2"),
        text__depth4=("#4D4D4D","#B5B5B5"),
        value__text=("#000000","#FFFFFF"),
        value__key=("#555555","#B0B0B0"),
        value__number=("#A63200","#FFC078"),
        value__placeholder=("#00606B","#63F0DB"),
        value__reference=("#0B3FBF","#A8CBFF"),
    ),

    "sakura" : _preset(
        "樱（柔粉）",
        surface__window=("#FBF6F7","#1F1A1D"),
        surface__card=("#FFFFFF","#272124"),
        surface__inset=("#FAF4F6","#231D20"),
        surface__border=("#EDE0E4","#3A3034"),
        text__primary=("#2A1F23","#F5EEF1"),
        text__secondary=("#5B474E","#C8BCC1"),
        text__depth2=("#45363C","#DED4D8"),
        text__depth3=("#5F4C53","#BCB0B5"),
        text__depth4=("#7A656C","#9B9095"),
        text__muted=("#8C7A80","#8B8085"),
        type__buff=("#2E7D5B","#6FD3A3"),
        type__template=("#8E44AD","#D3A2E8"),
        type__global=("#B2691F","#F0B45C"),
        type__relic=("#2D6CB5","#8CC4F2"),
        value__text=("#2A1F23","#F2EAEE"),
        value__key=("#7A656C","#A79A9F"),
        value__number=("#C2410C","#FFB086"),
        value__placeholder=("#0E7490","#63E3D0"),
        value__reference=("#8E44AD","#D8AEFF"),
        state__ok=("#2E7D5B","#6FD3A3"),
        state__error=("#C62828","#FF8080"),
        chat__me=("#2D6CB5","#8CC4F2"),
        chat__ai=("#2E7D5B","#6FD3A3"),
    ),

    "mint" : _preset(
        "薄荷",
        surface__window=("#F2FAF7","#13201C"),
        surface__card=("#FFFFFF","#1A2A25"),
        surface__inset=("#EFF9F5","#172622"),
        surface__border=("#D6EAE2","#2C443C"),
        text__primary=("#16302A","#E8F6F1"),
        text__secondary=("#3F6157","#BBD5CB"),
        text__depth2=("#2C4F46","#CBE6DD"),
        text__depth3=("#446B60","#A9CEC2"),
        text__depth4=("#5C8378","#8CB4A8"),
        text__muted=("#7C9A90","#8AA79D"),
        type__buff=("#0F7B5A","#5FD3A8"),
        type__template=("#5B5BD6","#B9B9F2"),
        type__global=("#A8641B","#E9B26A"),
        type__relic=("#0F6CBD","#7CC0F5"),
        value__text=("#16302A","#E4F2ED"),
        value__key=("#5C8378","#9DBFB5"),
        value__number=("#B45309","#FFC078"),
        value__placeholder=("#0F766E","#5EEAD4"),
        value__reference=("#4338CA","#A5B4FC"),
        state__ok=("#0F7B5A","#5FD3A8"),
        state__error=("#B3261E","#FF8A80"),
        chat__me=("#0F6CBD","#7CC0F5"),
        chat__ai=("#0F7B5A","#5FD3A8"),
    ),

    "nord" : _preset(
        "极地（Nord）",
        surface__window=("#ECEFF4","#2E3440"),
        surface__card=("#FFFFFF","#3B4252"),
        surface__inset=("#E5E9F0","#333B4A"),
        surface__border=("#D8DEE9","#4C566A"),
        text__primary=("#2E3440","#ECEFF4"),
        text__secondary=("#4C566A","#C8D0DC"),
        text__depth2=("#434C5E","#D8DEE9"),
        text__depth3=("#4C566A","#C0C8D8"),
        text__depth4=("#616E88","#A7B1C2"),
        text__muted=("#7B88A1","#8F9AAC"),
        type__buff=("#4C8C4A","#A3BE8C"),
        type__template=("#5E81AC","#B48EAD"),
        type__global=("#B48EAD","#EBCB8B"),
        type__relic=("#5E81AC","#88C0D0"),
        value__text=("#2E3440","#E5E9F0"),
        value__key=("#616E88","#A7B1C2"),
        value__number=("#BF616A","#D08770"),
        value__placeholder=("#5E81AC","#8FBCBB"),
        value__reference=("#5E81AC","#81A1C1"),
        state__ok=("#4C8C4A","#A3BE8C"),
        state__error=("#BF616A","#FF9AA2"),
        chat__me=("#5E81AC","#88C0D0"),
        chat__ai=("#4C8C4A","#A3BE8C"),
    ),

    "sepia" : _preset(
        "羊皮纸（暖色低蓝光）",
        surface__window=("#F4ECD8","#221D16"),
        surface__card=("#FBF5E6","#2A241B"),
        surface__inset=("#F1E7D0","#1E1913"),
        surface__border=("#E0D2B4","#453B2C"),
        text__primary=("#3B2F1E","#F4ECD8"),
        text__secondary=("#6B5A42","#C9BCA2"),
        text__depth2=("#574733","#DFD2B8"),
        text__depth3=("#736046","#C2B295"),
        text__depth4=("#8F7A5C","#A69B86"),
        text__muted=("#9A8A6E","#9C907C"),
        type__buff=("#4C7A3F","#9CCB8A"),
        type__template=("#8A5A2B","#D9A96A"),
        type__global=("#9C6B1F","#E0B268"),
        type__relic=("#2F6B8C","#7FB6D6"),
        value__text=("#3B2F1E","#F0E7D4"),
        value__key=("#8F7A5C","#A69B86"),
        value__number=("#A8440F","#F0A96A"),
        value__placeholder=("#0E7490","#63D9C4"),
        value__reference=("#2F6B8C","#8FC4E0"),
        state__ok=("#4C7A3F","#9CCB8A"),
        state__error=("#A62B1F","#FF8A80"),
        chat__me=("#2F6B8C","#8FC4E0"),
        chat__ai=("#4C7A3F","#9CCB8A"),
    ),

    "ink" : _preset(
        "水墨（朱红点缀）",
        surface__window=("#FAFAF8","#141414"),
        surface__card=("#FFFFFF","#1C1C1C"),
        surface__inset=("#F5F5F3","#171717"),
        surface__border=("#E2E2DE","#333333"),
        text__primary=("#111111","#F5F5F5"),
        text__secondary=("#4A4A4A","#C4C4C4"),
        text__depth2=("#2A2A2A","#DCDCDC"),
        text__depth3=("#444444","#B8B8B8"),
        text__depth4=("#5E5E5E","#949494"),
        type__buff=("#2F6B4F","#7BC9A3"),
        type__template=("#6B4E9E","#C0A6E8"),
        type__global=("#A85A1F","#E5A868"),
        type__relic=("#2A5F8F","#84BAD8"),
        value__text=("#111111","#F2F2F2"),
        value__key=("#5E5E5E","#9E9E9E"),
        value__number=("#B0350F","#F09A6A"),
        value__placeholder=("#0F6B7A","#63D3D0"),
        value__reference=("#8C2F2F","#E89A9A"),
        state__ok=("#2F6B4F","#7BC9A3"),
        state__error=("#B3261E","#FF8A80"),
        chat__me=("#2A5F8F","#84BAD8"),
        chat__ai=("#2F6B4F","#7BC9A3"),
    ),

    "neon" : _preset(
        "霓虹（暗色为主）",
        surface__window=("#F4F4FA","#0E0B18"),
        surface__card=("#FFFFFF","#171226"),
        surface__inset=("#F1F1F8","#120E1F"),
        surface__border=("#DEDEF0","#33285A"),
        text__primary=("#16122A","#EDE9FF"),
        text__secondary=("#4B4270","#C0B6E0"),
        text__depth2=("#322A55","#CFC4F5"),
        text__depth3=("#4E4479","#A99CD6"),
        text__depth4=("#6B5F9C","#867BB0"),
        text__muted=("#857BA8","#8A80AC"),
        type__buff=("#00A36C","#4AE0A0"),
        type__template=("#7A3FF2","#B58CFF"),
        type__global=("#E08A00","#FFC061"),
        type__relic=("#00A0D8","#5FD4F5"),
        value__text=("#16122A","#EFE9FF"),
        value__key=("#6B5F9C","#9E93C4"),
        value__number=("#FF5C00","#FFA366"),
        value__placeholder=("#00A0A0","#5FE8E8"),
        value__reference=("#7A3FF2","#C4A0FF"),
        state__ok=("#00A36C","#4AE0A0"),
        state__error=("#E0245E","#FF7AA2"),
        chat__me=("#00A0D8","#5FD4F5"),
        chat__ai=("#00A36C","#4AE0A0"),
    ),

    "ocean" : _preset(
        "深海",
        surface__window=("#EEF6FA","#0D1B24"),
        surface__card=("#FFFFFF","#132630"),
        surface__inset=("#E9F3F8","#10212A"),
        surface__border=("#D2E5EF","#25404E"),
        text__primary=("#0F2A38","#E6F2F8"),
        text__secondary=("#35606F","#B0CBD6"),
        text__depth2=("#1E4658","#C3DCE8"),
        text__depth3=("#2F6379","#9FC2D2"),
        text__depth4=("#437F94","#7FA6B8"),
        text__muted=("#6E93A1","#829FA9"),
        type__buff=("#1F7A4C","#63D39B"),
        type__template=("#5A4FCF","#AFA6F2"),
        type__global=("#B26B1F","#EFB45C"),
        type__relic=("#0F6CBD","#7CC0F5"),
        value__text=("#0F2A38","#E3F0F6"),
        value__key=("#437F94","#8FB0BE"),
        value__number=("#C2410C","#FFB07A"),
        value__placeholder=("#0E7490","#5EEAD4"),
        value__reference=("#1D4ED8","#93C5FD"),
        state__ok=("#1F7A4C","#63D39B"),
        state__error=("#C62828","#FF8080"),
        chat__me=("#0F6CBD","#7CC0F5"),
        chat__ai=("#1F7A4C","#63D39B"),
    ),

    "amber" : _preset(
        "琥珀",
        surface__window=("#FDF6EC","#1F1710"),
        surface__card=("#FFFFFF","#2A2016"),
        surface__inset=("#FBF1E3","#231A12"),
        surface__border=("#EEDFC6","#463726"),
        text__primary=("#33261A","#F7EFE3"),
        text__secondary=("#5F4B33","#CDBCA5"),
        text__depth2=("#4E3B28","#E3D5C2"),
        text__depth3=("#6B5439","#C4B29A"),
        text__depth4=("#886E4E","#A79378"),
        text__muted=("#8F7C60","#9C8C77"),
        type__buff=("#3F7A34","#8FD07E"),
        type__template=("#7A4FA0","#C7A0E0"),
        type__global=("#A8641B","#E8B466"),
        type__relic=("#2C6B8F","#7FBCDC"),
        value__text=("#33261A","#F2E8DA"),
        value__key=("#886E4E","#A79378"),
        value__number=("#A8440F","#F0A96A"),
        value__placeholder=("#0E7490","#5EE0CC"),
        value__reference=("#2C6B8C","#8FC4E0"),
        state__ok=("#3F7A34","#8FD07E"),
        state__error=("#B3261E","#FF8A80"),
        chat__me=("#2C6B8F","#8FC4E0"),
        chat__ai=("#3F7A34","#8FD07E"),
    ),
}


def preset_names():
    return list(PRESETS.keys())


def preset_label(name):
    entry = PRESETS.get(name)
    return entry["label"] if entry else str(name)


def apply_overrides(overrides=None,preset=None):
    '''装载用户自定义配色

    overrides: {token: [light, dark]}，或 {token: "#RRGGBB"}（只给一套时自动推另一套）
    preset:    预设名
    '''
    global _OVERRIDES
    _OVERRIDES = merge_overrides(overrides,preset)
    refresh()
    return _OVERRIDES


def merge_overrides(overrides=None,preset=None):
    '''把「预设 + 用户覆盖」合并成一张表，**不改动当前状态**

    颜色过渡动画需要先算出「目标配色长什么样」再逐帧走过去；
    如果顺手改了全局状态，动画就会从终点起步（等于没有过渡）。
    '''
    merged = {}
    entry = PRESETS.get(preset or "default")
    if entry:
        for token,value in entry["overrides"].items():
            normalized = _normalize(value)
            if normalized:
                merged[token] = normalized
    for token,value in (overrides or {}).items():
        if not is_valid(token):
            continue
        normalized = _normalize(value)
        if normalized:
            merged[token] = normalized
    return merged


def _normalize(value):
    '''把用户给的写法统一成 (light, dark)'''
    if value is None:
        return None
    if isinstance(value,str):
        text = value.strip()
        if not HEX_RE.match(text):
            return None
        return (text,_auto_dark(text))
    if isinstance(value,(list,tuple)):
        items = [str(item).strip() for item in value]
        if len(items) == 1 and HEX_RE.match(items[0]):
            return (items[0],_auto_dark(items[0]))
        if len(items) >= 2 and HEX_RE.match(items[0]) and HEX_RE.match(items[1]):
            return (items[0],items[1])
    return None


def _auto_dark(color):
    '''给一个颜色推一个深色主题下的近似值：提高明度'''
    red,green,blue = _rgb(color)
    average = (red + green + blue) / 3
    boost = 0.38 if average < 180 else 0.12
    red = int(red + (255 - red) * boost)
    green = int(green + (255 - green) * boost)
    blue = int(blue + (255 - blue) * boost)
    return f"#{red:02X}{green:02X}{blue:02X}"


def _rgb(color):
    return (int(color[1:3],16),int(color[3:5],16),int(color[5:7],16))


def _rgba(color):
    '''解析 "#RRGGBB" / "#AARRGGBB"（Qt 的 #AARRGGBB 写法也认）'''
    text = str(color).lstrip("#")
    if len(text) == 8:
        alpha = int(text[0:2],16)
        return (int(text[2:4],16),int(text[4:6],16),int(text[6:8],16),alpha)
    if len(text) == 6:
        return (int(text[0:2],16),int(text[2:4],16),int(text[4:6],16),255)
    return (0,0,0,255)


def _to_qcolor_spec(rgba):
    red,green,blue,alpha = rgba
    if alpha >= 255:
        return "#%02X%02X%02X" % (red,green,blue)
    return "#%02X%02X%02X%02X" % (alpha,red,green,blue)


def display_map():
    '''当前实际生效的整套颜色对 → {token: (light, dark)}

    这是颜色过渡的起点：预设 default 没有任何 overrides，
    必须从「现在真正会显示的颜色」出发，动画才有中间状态
    （拿空覆盖表当起点会直接跳到终点，等于没有过渡）。
    '''
    result = {}
    for token in TOKEN:
        light,dark_value = raw(token)
        result[token] = (light,dark_value)
    return result


def display_map_of(overrides):
    '''按一张「覆盖表」算出它生效后每个 token 的颜色对（只覆盖表里有的）'''
    return _pairs(overrides)


def current_overrides():
    return dict(_OVERRIDES)


def target_overrides():
    '''当前 config.json 里应该生效的整套覆盖（= 预设 + 用户 overrides）

    用途：颜色过渡动画先算出「目标配色」，再让界面逐帧过渡过去。
    只反映**配置层**，不像 current_overrides() 那样会被动画中途改写。
    '''
    try:
        import bootstrap
        colors = bootstrap.config_section("colors",{}) or {}
        overrides = colors.get("overrides") if isinstance(colors.get("overrides"),dict) else {}
        preset = colors.get("preset") or "default"
    except Exception:
        return dict(_OVERRIDES)
    return merge_overrides(overrides,preset)


def themed_tokens():
    '''会被主题影响、值得给用户自定义的 token 分组'''
    return {
        "底色" : ["surface.window","surface.card","surface.inset","surface.border",
                  "surface.hover","surface.selected"],
        "结构" : ["text.depth1","text.depth2","text.depth3","text.depth4",
                  "text.secondary","text.muted"],
        "类型" : ["type.buff","type.template","type.global","type.relic"],
        "语义值" : ["value.text","value.key","value.number","value.placeholder",
                    "value.reference","value.unit"],
        "状态" : ["state.pending","state.running","state.ok","state.error",
                  "chat.me","chat.ai","search.hit"],
        "原文高亮" : ["json.key","json.string","json.number","json.bool","json.punct"],
    }


def export_overrides():
    '''导出「当前生效值 ≠ 默认值」的 token，可直接写进 config.json 的 colors.overrides'''
    result = {}
    for token in tokens():
        light,dark = raw(token)
        if (light,dark) != TOKEN[token]:
            result[token] = [light,dark]
    return result


def is_dark():
    '''当前是不是深色主题；没装 QFluentWidgets 时按亮色处理'''
    try:
        from qfluentwidgets import isDarkTheme
        return bool(isDarkTheme())
    except Exception:
        return False


def qss_background(token="surface.window"):
    '''给普通 QWidget 铺底色的样式表片段（注意：单独这样写 Qt 会忽略，要配类型选择器）'''
    return f"background-color:{hex(token)};"


# 只有这些「纯文字」控件需要透明底：Fluent 标签自带背景，压在卡片上会多出一层颜色。
# 注意不要把按钮/输入框也列进来——那会把 Fluent 自己的配色盖掉，深色主题下字就看不见了。
QSS_TEXT_TYPES = (
    "QLabel","StrongBodyLabel","BodyLabel","CaptionLabel","SubtitleLabel",
    "TitleLabel","LargeTitleLabel",
)


def qss_container(token="surface.window",object_name=None):
    '''容器样式：容器铺底色 + 纯文字控件透明底

    object_name 给出时只对那个控件生效（`#名字 { … }`），
    这样不会波及按钮、输入框等自带配色的控件。
    '''
    parts = []
    if object_name:
        parts.append(f"#{object_name} {{ background-color:{hex(token)}; }}")
    else:
        parts.append(f"QWidget {{ background-color:{hex(token)}; }}")
    parts.append(f"{','.join(QSS_TEXT_TYPES)} {{ background:transparent; }}")
    return "".join(parts)


TEXT_VIEW_QSS = "QPlainTextEdit, QTextEdit, QTextBrowser"


def qss_text_view(base="surface.card",text="text.primary",border="surface.border"):
    '''给 QPlainTextEdit / QTextEdit 这类控件上背景

    它们的可见区域是内部 viewport，只对控件设 background-color 往往不起作用（会留白），
    所以要连 `> QWidget`（viewport）一起写；QPalette 也一并设上作为兜底。
    '''
    base_hex = hex(base)
    selectors = ",".join(part.strip() for part in TEXT_VIEW_QSS.split(","))
    return (f"{selectors} {{ background-color:{base_hex}; color:{hex(text)};"
            f" border:1px solid {hex(border)}; border-radius:6px; }}"
            f"{selectors} > QWidget {{ background-color:{base_hex}; }}")


def apply_text_palette(widget,base_token="surface.card",text_token="text.primary"):
    '''给文本视图设调色板 + 视口背景（配合 qss_text_view 用，双保险）'''
    try:
        from PySide6.QtGui import QColor, QPalette
    except ImportError:
        return
    colors = widget.palette()
    base_color = QColor(hex(base_token))
    text_color = QColor(hex(text_token))
    for role in (QPalette.Base,QPalette.Window):
        colors.setColor(role,base_color)
    colors.setColor(QPalette.Text,text_color)
    widget.setPalette(colors)
    viewport = getattr(widget,"viewport",None)
    if callable(viewport):
        widget.viewport().setPalette(colors)
        widget.viewport().setAutoFillBackground(True)


def refresh():
    '''主题切换 / 改配色后调用，丢掉缓存（否则会继续用旧颜色）'''
    _CACHE.clear()


# ----------------------------------------
# 颜色过渡：换配色/切主题时让界面「渐变」过去，而不是啪地一下换掉
# ----------------------------------------
def _blend(left,right,ratio):
    '''把两个颜色按比例混合（用于过渡动画；输入是 "#RRGGBB" 这类颜色字符串）'''
    lr,lg,lb,la = _rgba(left)
    rr,rg,rb,ra = _rgba(right)
    return _to_qcolor_spec((round(lr + (rr - lr) * ratio),
                            round(lg + (rg - lg) * ratio),
                            round(lb + (rb - lb) * ratio),
                            round(la + (ra - la) * ratio)))


def _pairs(overrides):
    '''把「覆盖表」映射成 {token: (light色, dark色)} 的纯颜色对

    过渡动画插值必须在**颜色对**上做：`_OVERRIDES` 里每个 token 必须是
    (light, dark) 两个值，否则 `raw(token)[0]` 这类读取会直接把单个色值当序列用，
    整个绘制层都会报 "unexpected 2"（第一版就是这么炸的）。
    '''
    result = {}
    for token,value in (overrides or {}).items():
        if not isinstance(value,(tuple,list)) or len(value) != 2:
            continue
        result[token] = (str(value[0]),str(value[1]))
    return result


def mix(old,new,ratio):
    '''两套「颜色对」之间插值；old/new 都是 {token: (light, dark)}

    只对**两边都有的 key** 插值：缺的那一侧交给最终设置处理。
    以前这里用 `after or before` 兜底，结果「预设 default（没有任何 overrides）」这种
    起点为空的情况会直接跳到终点色，整段过渡等于没有（就是最初那个 bug）。
    '''
    result = {}
    for token in set(old) & set(new):
        before = old[token]
        after = new[token]
        result[token] = (_blend(before[0],after[0],ratio),
                         _blend(before[1],after[1],ratio))
    return result


def _ease(t):
    '''ease-out：起步快、收尾稳，比线性看着舒服'''
    return 1.0 - (1.0 - t) ** 3


_TWEEN_FRAMES = 14


def set_overrides_raw(values,base=None):
    '''直接换掉整张覆盖表（过渡动画逐帧调用；不做校验，值必须已经是合法颜色对）

    base 不给时以当前覆盖表为底：这样「这次不参与过渡的 token」保持不变，
    而不是被顺手清空（清空会让它们在动画期间闪回默认色）。
    '''
    global _OVERRIDES
    if base is None:
        merged = dict(_OVERRIDES)
        merged.update(values or {})
    else:
        merged = dict(base)
        merged.update(values or {})
    _OVERRIDES = merged
    refresh()


def animate_to(target,on_frame=None,frames=_TWEEN_FRAMES,cancel=None):
    '''把界面当前显示的颜色平滑过渡到 target（{token: (light, dark)}）

    起点取的是**当前实际显示的颜色**（display_map），不是「覆盖表」：
    预设 default 的覆盖表是空的，拿它当起点会让所有颜色直接跳到终点（等于没有过渡）。
    target 里没有的 token（例如换到一套没覆盖该 token 的预设）中途保持不动，最后一步归位。
    '''
    try:
        from PySide6.QtCore import QTimer
    except ImportError:
        set_overrides_raw(target)
        if on_frame is not None:
            on_frame()
        return None
    start = display_map()
    target = _pairs({token:value for token,value in (target or {}).items()
                     if token in TOKEN and value})
    final = dict(target)
    state = {"step" : 0}

    def _tick():
        if cancel is not None and cancel():
            return
        state["step"] += 1
        ratio = _ease(state["step"] / frames)
        # base=start：起点里那些「目标没有覆盖」的 token 保持原样，不会中途闪回默认色
        set_overrides_raw(mix(start,target,ratio),base=start)
        if on_frame is not None:
            on_frame()
        if state["step"] >= frames:
            timer.stop()
            set_overrides_raw(final)
            if on_frame is not None:
                on_frame()

    timer = QTimer()
    timer.setInterval(16)
    timer.timeout.connect(_tick)
    timer.start()
    return timer


def raw(token):
    '''取 (light, dark) 原始值（用户覆盖优先）'''
    value = _OVERRIDES.get(token)
    if value is not None:
        return value
    return TOKEN.get(token,FALLBACK)


def hex(token):
    '''取当前主题下的十六进制字符串'''
    cached = _CACHE.get(token)
    if cached is not None:
        return cached
    light,dark = raw(token)
    value = dark if is_dark() else light
    _CACHE[token] = value
    return value


def qss(token):
    '''"color:#xxxxxx;" —— 给 setStyleSheet 用的旧式写法'''
    return "color:" + hex(token) + ";"


def qcolor(token):
    '''取 QColor；没有 Qt 时返回 None'''
    try:
        from PySide6.QtGui import QColor
    except ImportError:
        return None
    return QColor(hex(token))


def tokens():
    return sorted(TOKEN.keys())


def is_valid(token):
    return token in TOKEN


# ----------------------------------------
# 字号缩放（译文树 / 目录 / 原文面板共用）
# ----------------------------------------
FONT_SCALE_MIN = 0.8
FONT_SCALE_MAX = 1.6
FONT_SCALE_DEFAULT = 1.0


def font_scale():
    '''当前全局字号比例（存在 config.json 的 window.font_scale）'''
    try:
        import bootstrap
        value = bootstrap.config_get("window","font_scale",FONT_SCALE_DEFAULT)
        value = float(value)
    except Exception:
        return FONT_SCALE_DEFAULT
    return min(max(value,FONT_SCALE_MIN),FONT_SCALE_MAX)


def set_font_scale(value,save=True):
    '''设置字号比例并落盘；返回真正生效的值（越界会被夹回来）'''
    value = min(max(float(value),FONT_SCALE_MIN),FONT_SCALE_MAX)
    if save:
        try:
            import bootstrap
            bootstrap.config_set("window","font_scale",round(value,3))
        except Exception:
            pass
    return value


def scaled_font(base,scale=None):
    '''按当前比例放大/缩小一个 QFont（base 原对象不被改动）'''
    if base is None:
        return None
    factor = font_scale() if scale is None else float(scale)
    if abs(factor - 1.0) < 0.001:
        return base
    font = type(base)(base)
    size = base.pointSizeF()
    if size and size > 0:
        font.setPointSizeF(max(size * factor,6.0))
    return font
