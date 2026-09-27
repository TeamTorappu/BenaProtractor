'''
译文 → 树节点数据的构建（不依赖 Qt，方便单测）
ui/qt_tree.py 只负责把这里产出的 Spec 变成 QTreeWidgetItem。

除了文本与结构，这里还会推断两件**只影响颜色**的东西（绝不改 spec.text）：
  depth —— 层级，用来做灰阶分级
  spans —— 一行里各段的语义（[(start, end, role), ...]），用来给数字/占位符/引用上色
'''
import json
import re

from ai.treewalk import normalize

# 节点的语义标记
KIND_TEXT = "text"
KIND_LINK = "link"
KIND_NOTE = "note"      # 备注 / 真值提示（灰字、不可选）
KIND_AI = "ai"          # 被 AI 译文替换过的行
KIND_ERROR = "error"

# span 的语义角色（与 ui/palette.py 的 token 一一对应）
ROLE_KEY = "value.key"
ROLE_VALUE = "value.text"          # 文本值：键弱、值实
ROLE_NUMBER = "value.number"
ROLE_PLACEHOLDER = "value.placeholder"
ROLE_REFERENCE = "value.reference"
ROLE_UNIT = "value.unit"
ROLE_META = "value.meta"
ROLE_SEARCH_HIT = "search.hit"     # 搜索命中（目录行高亮用）

# 数字：整数/小数/百分比/倍率
NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
# 占位符与引用
PLACEHOLDER_RE = re.compile(r"\[[^\[\]]+\]")
REFERENCE_RE = re.compile(r"<[^<>]+>")
# 末尾单位
UNIT_RE = re.compile(r"(秒|层|倍|个|次|点|格|帧|名|单位|%|s|x)$")
# "键 : 值" / "键：值" / "键 = 值" 的分隔（前后可能有空格）
SEPARATOR_RE = re.compile(r"^(.{0,40}?)\s*(?::|：|=)\s*(.+)$")


class NodeSpec:
    '''一棵译文树里的一个可见行'''

    __slots__ = ("node_path","text","link","kind","ai_origin","ai_status","expanded",
                 "children","node","depth","spans")

    def __init__(self,node_path,text,link="",kind=KIND_TEXT,ai_origin=None,
                 ai_status="none",expanded=True,node=None,depth=0,spans=None):
        self.node_path = node_path
        self.text = text
        self.link = link
        self.kind = kind
        self.ai_origin = ai_origin
        self.ai_status = ai_status
        self.expanded = expanded
        self.children = []
        self.node = node      # 对应的（已规整的）译文结构体，AI 侧栏要按 node_path 找回去
        self.depth = depth    # 0 = 顶层
        self.spans = spans or []

    def add(self,child):
        if child is not None:
            self.children.append(child)
        return child

    def count(self):
        return 1 + sum(child.count() for child in self.children)

    def __repr__(self):
        return f"<NodeSpec {self.node_path} {self.text[:24]!r} kids={len(self.children)}>"


# ----------------------------------------
# 语义推断（纯函数，可单测）
# ----------------------------------------
def infer_spans(text):
    '''推断一行文本里各段的语义角色，返回 [(start, end, role), ...]

    只在「键值行」上做细分：`键 : 值` 的键压灰、值里的数字/占位符/引用各自上色；
    其余情况保持空列表（由节点 kind 决定整行颜色），这样既有效果又不容易出错。
    '''
    if not text:
        return []
    spans = []
    match = SEPARATOR_RE.match(text)
    if match:
        key = match.group(1)
        value = match.group(2)
        if key.strip() and value.strip():
            spans.append((0,len(key),ROLE_KEY))
            value_start = match.start(2)
            inner = _value_spans(value,value_start)
            if inner:
                spans.extend(inner)
            else:
                # 值是纯文本（如 "PHYSICAL"、"藏品"）：整段用「值」色，让键弱下去
                spans.append((value_start,len(text.rstrip()),ROLE_VALUE))
            return spans
    # 非键值行：整行里出现的占位符/引用单独标出来
    spans.extend(_value_spans(text,0))
    return spans


def _value_spans(value,offset):
    '''给一段「值」里出现的数字/占位符/引用/单位打标记'''
    spans = []
    placeholders = [(m.start(),m.end()) for m in PLACEHOLDER_RE.finditer(value)]
    references = [(m.start(),m.end()) for m in REFERENCE_RE.finditer(value)]
    numbers = [(m.start(),m.end()) for m in NUMBER_RE.finditer(value)]

    consumed = []
    for start,end in placeholders:
        spans.append((offset + start,offset + end,ROLE_PLACEHOLDER))
        consumed.append((start,end))
    for start,end in references:
        spans.append((offset + start,offset + end,ROLE_REFERENCE))
        consumed.append((start,end))
    for start,end in numbers:
        if _overlaps(start,end,consumed):
            continue
        spans.append((offset + start,offset + end,ROLE_NUMBER))
        consumed.append((start,end))
    # 纯数字后面紧跟的单位，压成灰色（"10 秒" 里的 "秒"）
    unit = UNIT_RE.search(value.rstrip())
    if unit and consumed:
        unit_start = len(value.rstrip()) - len(unit.group(1))
        if not _overlaps(unit_start,len(value),consumed):
            spans.append((offset + unit_start,offset + len(value.rstrip()),ROLE_UNIT))
    spans.sort()
    return spans


def _overlaps(start,end,ranges):
    for left,right in ranges:
        if start < right and left < end:
            return True
    return False


def depth_of(node_path):
    '''由 node_path 算层级（"0" = 0，"0.1.2" = 2）'''
    if not node_path:
        return 0
    return node_path.count(".")


def build_lines(struct,breadcrumb=None):
    '''把译文结构变成 NodeSpec 列表（LinkItem 的兄弟，纯数据）'''
    specs = []
    if breadcrumb:
        crumb = NodeSpec("breadcrumb","> " + " > ".join(breadcrumb),kind=KIND_NOTE,depth=0)
        specs.append(crumb)
    for index,child in enumerate(_as_children(struct)):
        specs.append(_build(child,f"{index}",[],0))
    return specs


def _as_children(struct):
    if struct is None:
        return []
    if isinstance(struct,list):
        return struct
    return [struct]


def _build(node,node_path,path_titles,depth):
    if node is None:
        return None
    normalized = normalize(node)
    if normalized is None:
        return None
    text = str(normalized.get("main",""))
    link = normalized.get("link","") or ""
    ai_status = normalized.get("ai_status","none")
    ai_origin = normalized.get("ai_origin")
    style_closed = bool(normalized.get("style_closed"))
    if "children" not in normalized and normalized.get("true","") != "":
        # 真值结果（并行）：没有子节点时并到同一行显示
        truth = str(normalized["true"])
        text = f"{truth}：" if text == "" else f"{text}，{truth}："

    kind = KIND_TEXT
    if link:
        kind = KIND_LINK
    elif ai_status == "applied":
        kind = KIND_AI

    spec = NodeSpec(node_path,text,link=link,kind=kind,
                    ai_origin=ai_origin,ai_status=ai_status,
                    expanded=not style_closed,node=normalized,
                    depth=depth,
                    spans=[] if kind in (KIND_LINK,KIND_NOTE) else infer_spans(text))

    description = normalized.get("description","")
    if description:
        spec.add(NodeSpec(node_path + ".desc",f"（{description}）",kind=KIND_NOTE,
                          depth=depth + 1))
    if "children" in normalized and normalized.get("true","") != "":
        # 真值结果（另起一行）
        spec.add(NodeSpec(node_path + ".true",f"...{normalized['true']}：",kind=KIND_NOTE,
                          depth=depth + 1))

    if "children" in normalized:
        for index,child in enumerate(normalized["children"]):
            built = _build(child,f"{node_path}.{index}",path_titles + [text],depth + 1)
            spec.add(built)
    return spec


def build_raw(datas):
    '''无法翻译时的兜底：把 json 结构变成 NodeSpec 列表'''
    specs = []
    return _build_raw(datas,"0",specs,0)


def _build_raw(datas,node_path,out,depth=0):
    if isinstance(datas,dict):
        for index,(data_key,content) in enumerate(datas.items()):
            path = f"{node_path}.{index}"
            if isinstance(content,(dict,list)):
                text = f"{data_key} : {'{' if isinstance(content,dict) else '['}"
                spec = NodeSpec(path,text,spans=infer_spans(text),depth=depth)
                _build_raw(content,path,spec.children,depth + 1)
                spec.add(NodeSpec(f"{path}.end","}" if isinstance(content,dict) else "]",
                                  kind=KIND_NOTE,depth=depth + 1))
                out.append(spec)
            else:
                text = f"{data_key} : {raw_text(content)}"
                out.append(NodeSpec(path,text,spans=infer_spans(text),depth=depth))
    elif isinstance(datas,list):
        for index,content in enumerate(datas):
            path = f"{node_path}.{index}"
            if isinstance(content,(dict,list)):
                spec = NodeSpec(path,"{" if isinstance(content,dict) else "[",depth=depth)
                _build_raw(content,path,spec.children,depth + 1)
                spec.add(NodeSpec(f"{path}.end","}" if isinstance(content,dict) else "]",
                                  kind=KIND_NOTE,depth=depth + 1))
                out.append(spec)
            else:
                out.append(NodeSpec(path,raw_text(content),depth=depth))
    else:
        out.append(NodeSpec(node_path,raw_text(datas),depth=depth))
    return out


def raw_text(value):
    if isinstance(value,str):
        return f'"{value}"'
    if isinstance(value,bool):
        return "true" if value else "false"
    return str(value)


def raw_json_text(datas):
    '''原文面板的文本（与旧版 display_origin 输出一致）

    注意：这里刻意不用 json.dumps(整个列表)，而是自己拼 [] 与逗号。
    本机这个 CPython 构建里 json.dumps(list) 会异常地只输出第一个元素的 {} 形式
    （同一表达式在其它上下文又正常），为免踩这个坑，列表一律手工拼。
    '''
    if isinstance(datas,list):
        parts = [json.dumps(item,indent=4,ensure_ascii=False) for item in datas]
        if not parts:
            return "[]"
        if len(parts) == 1:
            return "[\n" + parts[0] + "\n]"
        return "[\n" + ",\n".join(parts) + "\n]"
    if isinstance(datas,dict):
        return json.dumps(datas,indent=4,ensure_ascii=False)
    return str(datas)


def specs_to_text(specs,depth=0):
    '''把 Spec 列表拍平成缩进文本（右侧/复制用，也方便测试断言）'''
    lines = []
    for spec in specs:
        lines.append("    " * depth + spec.text)
        lines.extend(specs_to_text(spec.children,depth + 1))
    return lines


# ----------------------------------------
# 搜索：纯字符串匹配（不引正则，中文/方括号都不用转义）
# ----------------------------------------
def match_spans(text,keywords):
    '''某段文本里所有关键词命中的区间 → [(start, end, "search.hit"), ...]

    - 子串匹配、大小写不敏感（先 casefold 再找，索引与原文一一对应）；
    - 空关键词直接跳过；命中的区间去重、按 start 排序、互不重叠（同一起点取最长）。
    '''
    if not text:
        return []
    folded = str(text).casefold()
    hits = []
    for keyword in keywords or []:
        word = str(keyword or "").strip()
        if not word:
            continue
        needle = word.casefold()
        start = folded.find(needle)
        while start >= 0:
            hits.append((start,start + len(needle)))
            start = folded.find(needle,start + len(needle))
    if not hits:
        return []
    hits.sort(key=lambda span:(span[0],-span[1]))
    merged = []
    for start,end in hits:
        if merged and start < merged[-1][1]:
            # 与上一段重叠：取更长的那个，保证区间互不重叠（高亮不会叠色）
            if end > merged[-1][1]:
                merged[-1] = (merged[-1][0],end)
            continue
        merged.append((start,end))
    return [(start,end,ROLE_SEARCH_HIT) for start,end in merged]


def merge_spans(base_spans,hits):
    '''把命中高亮叠在语义 span 上：命中优先，其余保持原位

    绘制层要求区间有序、互不重叠，所以这里做一次「按起点排序 + 命中覆盖」。
    '''
    if not hits:
        return list(base_spans or [])
    result = []
    for start,end,role in sorted(base_spans or []):
        # 与任一命中区间相交的语义段直接丢掉（让命中高亮完整显示）
        if any(start < hit_end and hit_start < end for hit_start,hit_end,_ in hits):
            continue
        result.append((start,end,role))
    result.extend(hits)
    result.sort(key=lambda span:(span[0],span[1]))
    return result


def filter_items(items,keywords,keep=None,sort_key=None):
    '''按关键词筛选目录条目 → (命中的条目列表, {full_key: 命中区间})

    items 只需要「鸭子类型」：带 display_name / data_key / full_key 三个属性即可，
    所以这里不依赖 Qt、也不依赖 qt_ui 里的 ProtractorItem，可以直接单测。
    匹配范围与旧版一致：显示名或内部 key 命中任一关键词就算命中（多关键词为「与」）。

    keep：优先保留在结果最前面的条目（「清空搜索后恢复原选中项」用）；
          其余保持原有顺序（目录顺序 = 数据里的顺序，稳定且可预期）。
    sort_key：可调用对象 item -> 排序键；给了就按它**稳定**排序。
    '''
    words = [str(word).strip() for word in (keywords or []) if str(word or "").strip()]
    matched = []
    hits = {}
    for item in items:
        name = str(getattr(item,"display_name","") or "")
        key = str(getattr(item,"data_key","") or "")
        if words:
            haystack = (name + "\n" + key).casefold()
            if not all(word.casefold() in haystack for word in words):
                continue
        matched.append(item)
        if words:
            spans = match_spans(name,words)
            if not spans:
                spans = match_spans(key,words)
            if spans:
                hits[getattr(item,"full_key",name)] = spans
    if sort_key is not None:
        matched.sort(key=sort_key)
    if keep:
        # 恢复选中项：稳定排序之后再把目标提到最前，避免「排序一变选中项就不见了」
        matched.sort(key=lambda item: 0 if getattr(item,"full_key","") == keep else 1)
    return matched,hits


def extract_copy_options(text):
    '''从一行译文里抽出可以单独复制的片段，返回 [(标签,内容), ...]

    与旧 tkinter 版右键菜单的规则保持一致：
        "A : B" / "A：B" / "A（B）"，其中 $type 那种超长值会被裁剪
    '''
    options = []
    if ":" in text:
        keys = [key.strip() for key in text.split(":")]
        if keys[1].startswith("$type"):
            keys[1] = keys[1][28:-17]
        options.append((keys[0],keys[0]))
        options.append((keys[1],keys[1]))
    elif "：" in text:
        keys = [key.strip() for key in text.split("：")]
        options.append((keys[0],keys[0]))
        options.append((keys[1],keys[1]))
    elif "（" in text and text.endswith("）"):
        keys = [key.strip() for key in text.split("（")]
        keys[1] = keys[1][:-1].strip()
        options.append((keys[0],keys[0]))
        options.append((keys[1],keys[1]))
    result = []
    for label,content in options:
        if content in ("","未翻译","$type"):
            continue
        result.append((content,content) if label == content else (label,content))
    return result
