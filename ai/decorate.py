'''
把 AI 译文写回译文结构（旁挂式，不破坏引擎字段）
- 引擎自己的 main 原文永远保留在 ai_origin 里，方便随时回退/校对
- ai_status: pending（有候选但不译）/ running / applied / error
- UI 只认这些旁挂字段，所以 anne/bena 一行都不用改
'''
from ai.fragments import already_translated
from ai.treewalk import walk


def find_node(translation,node_path):
    for path,node,_ in walk(translation):
        if path == node_path:
            return node
    return None


def mark_pending(translation,node_path,status="pending"):
    node = find_node(translation,node_path)
    if node is None:
        return None
    node.setdefault("ai_origin",node.get("main",""))
    node["ai_status"] = status
    return node


def mark_error(translation,node_path,message=""):
    node = find_node(translation,node_path)
    if node is None:
        return None
    node.setdefault("ai_origin",node.get("main",""))
    node["ai_status"] = "error"
    if message:
        node["ai_note"] = message
    return node


def apply_fragment(translation,fragment,ai_text,force=False):
    '''把一个片段的 AI 译文写到对应节点上；返回是否真的写了

    展示效果：AI译文（原片段），原文标识保留在括号里，便于校对与回退。
    '''
    if not force and not already_translated(fragment,ai_text):
        return False
    node = find_node(translation,fragment.node_path)
    if node is None:
        return False
    original = node.get("ai_origin")
    if original is None:
        original = node.get("main","")
    cleaned = ai_text.strip()
    if fragment.candidate and fragment.candidate in original:
        display = original.replace(fragment.candidate,f"{cleaned}（{fragment.candidate}）",1)
    else:
        display = f"{cleaned}（{original}）"
    node["ai_origin"] = original
    node["ai_text"] = cleaned
    node["ai_status"] = "applied"
    node["main"] = display
    return True


def apply_results(translation,fragments,results):
    '''results: {fragment.key: ai_text}'''
    applied = 0
    for fragment in fragments:
        ai_text = results.get(fragment.key)
        if not ai_text:
            continue
        if apply_fragment(translation,fragment,ai_text):
            fragment.ai_text = ai_text
            fragment.status = "done"
            applied += 1
    return applied


def reset_node(translation,node_path):
    '''把某一行恢复成引擎原文'''
    node = find_node(translation,node_path)
    if node is None:
        return False
    if "ai_origin" in node:
        node["main"] = node["ai_origin"]
    node["ai_status"] = "none"
    node.pop("ai_text",None)
    return True


def reset_all(translation):
    count = 0
    for _,node,_ in walk(translation):
        if node.get("ai_status") in ("applied","error","pending","running"):
            if "ai_origin" in node:
                node["main"] = node["ai_origin"]
            node["ai_status"] = "none"
            node.pop("ai_text",None)
            node.pop("ai_note",None)
            count += 1
    return count


def applied_count(translation):
    return sum(1 for _,node,_ in walk(translation) if node.get("ai_status") == "applied")
