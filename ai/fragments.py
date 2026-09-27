'''
未译片段收集
把译文树里「看不懂的英文/未翻译标记」抽出来，交给 AI 翻译。
两条来源：
  1. 标记式：引擎自己标了「（未翻译）」「（翻译失败）」「未找到相应名称的Buff模板」
  2. 启发式：片段里一个中文字都没有、又含有字母（例如 ChargeBuff、rogue_4_relic_xxx），
     默认开启，可在 AI 设置里关掉
'''
import re
from dataclasses import dataclass, field
from typing import List, Tuple

from ai.treewalk import walk_text

UNTRANSLATED_MARKS = ("（未翻译）","（翻译失败）","未找到相应名称的Buff模板")
UNKNOWN_MARKS = ("未知时点",)

LETTER_RE = re.compile(r"[A-Za-z]{3,}")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")

# 这些词是工具里的固定术语，出现时说明已经翻译过了
KNOWN_TERMS = ("Buff","Node","黑板","藏品","节点")


@dataclass
class Fragment:
    node_path: str
    text: str
    kind: str                     # text / key / value
    reason: str                   # mark / heuristic / missing_main
    breadcrumb: Tuple[str,...] = ()
    parent_main: str = ""
    candidate: str = ""           # 真正要送出去翻译的片段
    needs_translation: bool = False
    ai_text: str = ""
    status: str = "idle"          # idle / running / done / error

    @property
    def key(self):
        return f"{self.node_path}|{self.candidate}"

    @property
    def breadcrumb_text(self):
        return " > ".join(self.breadcrumb)


def has_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text or ""))


def looks_like_identifier(text: str) -> bool:
    '''像不像一个没翻译的游戏内部标识'''
    if not text:
        return False
    stripped = text.strip()
    if stripped == "":
        return False
    if stripped.startswith("$"):
        # $type 之类的声明字段是给程序看的，不是待译内容
        return False
    if not LETTER_RE.search(stripped):
        return False
    if has_cjk(stripped):
        return False
    if stripped in ("true","false","None","null","empty"):
        return False
    return True


def _split_marked(text: str):
    '''把带「（未翻译）」这类标记的文本拆成 (内容, 说明) 并去掉标记'''
    note = ""
    for mark in UNTRANSLATED_MARKS:
        if mark in text:
            note = mark.strip("（）")
            text = text.replace(mark,"")
    for mark in UNKNOWN_MARKS:
        if mark in text:
            note = note or mark
    return text.strip(), note


def _split_key_value(text: str):
    '''把 "key : value" / "key：value" / "[key] = value" 拆开；拆不开就返回 ("", text)'''
    for sep in (" : ","："," = "):
        if sep in text:
            left,right = text.split(sep,1)
            return left.strip(),right.strip()
    return "",text.strip()


def _clean_candidate(candidate: str) -> str:
    '''候选片段本身可能带一层「（同名）」的自注释，去掉再说'''
    text = (candidate or "").strip()
    if text.endswith("）") and "（" in text:
        head,_,tail = text.rpartition("（")
        if tail[:-1].strip() == head.strip():
            text = head.strip()
    return text.strip()


def _value_is_identifier(value: str) -> bool:
    if not value:
        return False
    # 去掉引号/括号/百分号之类的噪声
    core = value.strip().strip('"').strip("'").strip()
    if core.startswith("$type"):
        return False
    return looks_like_identifier(core)


def collect_fragments(translation,heuristic=True,max_depth=-1) -> List[Fragment]:
    '''遍历译文树，返回可读顺序的片段列表'''
    fragments: List[Fragment] = []
    if translation is None:
        return fragments
    for node_path,text,breadcrumb,node in walk_text(translation):
        if max_depth >= 0 and node_path.count(".") > max_depth:
            continue
        content,note = _split_marked(text)
        parent_main = breadcrumb[-1] if breadcrumb else ""
        if note:
            key,value = _split_key_value(content)
            candidate = _clean_candidate(value or content)
            # 标记去掉之后可能什么都不剩（例如整行就是「（未翻译）」），这种没得翻
            if looks_like_identifier(candidate):
                fragments.append(Fragment(
                    node_path=node_path,
                    text=text,
                    kind="text",
                    reason="mark",
                    breadcrumb=breadcrumb,
                    parent_main=parent_main,
                    candidate=candidate,
                    needs_translation=True,
                ))
            continue
        key,value = _split_key_value(content)
        if key and _value_is_identifier(value):
            fragments.append(Fragment(
                node_path=node_path,
                text=text,
                kind="value",
                reason="heuristic",
                breadcrumb=breadcrumb,
                parent_main=parent_main,
                candidate=_clean_candidate(value.strip('"')),
                needs_translation=bool(heuristic),
            ))
            continue
        if not key and looks_like_identifier(content):
            fragments.append(Fragment(
                node_path=node_path,
                text=text,
                kind="text",
                reason="heuristic",
                breadcrumb=breadcrumb,
                parent_main=parent_main,
                candidate=_clean_candidate(content),
                needs_translation=bool(heuristic),
            ))
    return fragments


def pending_fragments(translation,heuristic=True,max_depth=-1) -> List[Fragment]:
    return [fragment for fragment in collect_fragments(translation,heuristic,max_depth)
            if fragment.needs_translation]


def already_translated(fragment: Fragment,translation_text: str) -> bool:
    '''AI 译文看起来有没有用（空/原样返回/纯符号视为没用）'''
    if not translation_text:
        return False
    cleaned = translation_text.strip()
    if cleaned == "" or cleaned == fragment.candidate.strip():
        return False
    if not CJK_RE.search(cleaned):
        return False
    return True


def group_by_candidate(fragments: List[Fragment]):
    '''同一个片段文本可能出现在多个位置，合并成一次请求'''
    groups = {}
    for fragment in fragments:
        groups.setdefault(fragment.candidate.strip(),[]).append(fragment)
    return groups
