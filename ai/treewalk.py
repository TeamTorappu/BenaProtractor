'''
译文结构规范化与遍历
（放在 ai 包里，是因为 ui 与 ai 都要用；这里不 import 任何 GUI 或 ai 的其他模块）

注意：normalize 是「原地」规整——只有确认节点确实是 dict 时才会直接改它，
保证拿到的就是原对象，AI 写回的旁挂字段能立刻被界面看到。
'''

OPTIONAL_KEYS = ("description","true","false","link","style_closed")

# AI 旁挂字段（不参与引擎逻辑，只给界面用）
AI_KEYS = ("ai_text","ai_status","ai_note","ai_origin")


def normalize(node):
    '''把任意一个译文节点规整成 dict；无法规整则返回 None

    dict 会被原地补全（main 补成字符串、children 里的裸字符串包成 {main: ...}、None 子节点丢弃），
    非 dict（字符串/数字/None）会被包成一个新的 dict。
    '''
    if node is None:
        return None
    if isinstance(node,dict):
        if node.get("main") is None:
            node["main"] = ""
        elif not isinstance(node["main"],str):
            node["main"] = str(node["main"])
        if "children" in node:
            children = node["children"]
            if not isinstance(children,list):
                node["children"] = [children] if children is not None else []
            elif children:
                cleaned = []
                for child in children:
                    if child is None:
                        # 空的子节点直接丢掉（渲染出来只是个空行，没意义）
                        continue
                    if not isinstance(child,dict):
                        wrapped = _wrap(child)
                        if wrapped is not None:
                            cleaned.append(wrapped)
                        continue
                    normalize(child)
                    cleaned.append(child)
                node["children"] = cleaned
        return node
    return _wrap(node)


def _wrap(node):
    if node is None:
        return None
    return {"main" : str(node)}


def children_of(node):
    normalized = normalize(node)
    if normalized is None:
        return []
    return normalized.get("children",[])


def walk(node,node_path="0",breadcrumb=()):
    '''深度优先遍历，产出 (node_path, node, breadcrumb)

    breadcrumb 是祖先节点的 main 文本元组（不含自身）。
    '''
    normalized = normalize(node)
    if normalized is None:
        return
    yield node_path,normalized,breadcrumb
    for index,child in enumerate(normalized.get("children",[])):
        yield from walk(child,f"{node_path}.{index}",breadcrumb + (normalized["main"],))


def walk_text(node,node_path="0",breadcrumb=()):
    '''只遍历「一行文本」'''
    for path,current,crumbs in walk(node,node_path,breadcrumb):
        yield path,current["main"],crumbs,current


def find_breadcrumb(node,node_path):
    '''取某个 node_path 的祖先 main 文本元组'''
    for path,current,crumbs in walk(node):
        if path == node_path:
            return crumbs
    return ()


def text_lines(node,max_depth=-1):
    '''把译文结构导出成带缩进的纯文本行'''
    lines = []
    for path,current,_ in walk(node):
        depth = path.count(".")
        if max_depth >= 0 and depth > max_depth:
            continue
        lines.append("    " * depth + current["main"])
    return lines


def to_text(node,max_depth=-1):
    return "\n".join(text_lines(node,max_depth=max_depth))
