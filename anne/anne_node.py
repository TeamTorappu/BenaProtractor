#----------------------------------------
# 安妮的节点翻译器
#----------------------------------------
import traceback

from analyzer import analyze_buff
from game_class import Node
import anne.node_translator as node_translator

DEX = "①②③④⑤⑥⑦⑧⑨"

# 翻译重定向器，本质switch case
# 翻译返回的结果始终是一层一层的结构体
def anne_node_translate(node,blackboard={}):
    node_name = node.node_name
    #print(f"[安妮]尝试翻译节点 {node_name}")
    method = getattr(node_translator, node_name, "")
    translation = None
    try:
        if method != "" :
            translation = method(node.node_data,blackboard)
            # 检查是否有需要嵌套翻译的内容
            if "sub_nodes" in translation:
                sub_content_list = []
                for sub_content in translation["sub_nodes"]:
                    sub_content_list.append(Node(sub_content))
                if "children" not in translation:
                    translation["children"] = []
                translation["children"] += anne_node_translate_all(sub_content_list,blackboard)["children"]
                del translation["sub_nodes"]
        else: # 无法翻译，把所有数据搓成可阅读的格式
            children = []
            for key,content in node.node_data.items():
                if isinstance(content,dict): # 如果是子节点或者buff，还是要嵌套翻译一下试试的
                    if "attributes" in content and isinstance(content["attributes"],dict): # 看着像buff
                        buff = analyze_buff(content,blackboard)
                        buff["main"] = str(key) + " : " + buff["main"]
                        children.append(buff)
                    elif "$type" in content: # 子节点
                        sub_node = anne_node_translate(Node(content),blackboard)
                        sub_node["main"] = str(key) + " : " + sub_node["main"]
                        children.append(sub_node)
                    else: # 解析不了没办法
                        children_children = []
                        for skey,scontent in content.items():
                            children_children.append({"main" : str(skey) + " : " + str(scontent)})
                        if len(children_children) > 0:
                            children.append({
                                "main" : str(key) + " : {",
                                "children" : children_children
                            })
                            children.append({"main" : "}"})
                        else:
                            children.append({"main" : str(key) + " : {}"})
                elif isinstance(content,list): # 可能是子节点列表或者buff列表？
                    if len(content) > 0 and "$type" in content[0]: # 子节点列表
                        sub_content_list = []
                        for sub_content in content:
                            new_node = Node(sub_content)
                            if new_node != None:
                                sub_content_list.append(new_node)
                        sub_node_list = anne_node_translate_all(sub_content_list,blackboard)
                        sub_node_list["main"] = str(key) + " : " + sub_node_list["main"]
                        children.append(sub_node_list)
                    elif len(content) > 0 and "attributes" in content[0]: # 附属Buff列表
                        children_children = []
                        for scontent in content:
                            children_children.append(node_translator.analyze_buff(scontent,blackboard))
                        children.append({
                            "main" : str(key) + " : [",
                            "children" : children_children
                        })
                        children.append({"main" : "]"})
                    elif len(content) > 0:
                        children_children = []
                        for scontent in content:
                            children_children.append({"main" : str(scontent)})
                        children.append({
                            "main" : str(key) + " : [",
                            "children" : children_children
                        })
                        children.append({"main" : "]"})
                    else:
                        children.append({"main" : str(key) + " : []"})
                elif key == "$type":
                    children.append({"main": node.node_name})
                else:
                    children.append({"main": str(key) + " : " + str(content)})
            translation = {
                "main" : node_name+"（未翻译）",
                "style_closed" : True,
                "children" : children
            }
    except Exception as e:
        print(f"[安妮]... {node_name} 节点翻译失败了")
        traceback.print_exc()
        translation = {
            "main" : node_name+"（翻译失败）",
            "style_closed" : True,
        }
    # 返回译文
    return translation

# 全部翻译，包含对一些上下文Node的特殊处理
def anne_node_translate_all(node_list,blackboard=None):
    children = []
    for node in node_list:
        # IfNot：反转前面的处理状态
        if len(children) > 0 and node.node_name == "IfNot" :
            if "reversed" not in children[-1] or not children[-1]["reversed"]: # 已经翻转过不要再反转
                if "true" in children[-1] and "false" in children[-1]:
                    children[-1]["true"], children[-1]["false"] = children[-1]["false"], children[-1]["true"]
                    children[-1]["reversed"] = True
                elif "true" in children[-1]:
                    children[-1]["false"] = children[-1]["true"] 
                    children[-1]["true"] = "若非\""+children[-1]["true"]+"\"" 
                    children[-1]["reversed"] = True
                else: # 拿来检查前面处理不了？
                    children.append({"main" : "若前面的逻辑无法处理"})
        elif node.node_name == "IfElse":
            children.append(anne_node_translate_ifelse(node,blackboard))
        elif node.node_name == "IfConditions":
            children.append(anne_node_translate_ifconditions(node,blackboard))
        else:
            children.append(anne_node_translate(node,blackboard))
    # 最后一项打上标记
    if len(children) > 0:
        children[len(children)-1]["last_one"] = True
    return {"main" : "","children" : children}

# IfElse的特殊处理
def anne_node_translate_ifelse(node,blackboard):
    if node.translation == None:
        node_data = node.node_data
        # 判断节点
        true_flag = "如果是/有/可行/可处理："
        false_flag = "如果不是/没有/不可行/无法处理："
        if node.condition_nodes == None:
            return {"main" : "无效的判断节点"}
        struct = anne_node_translate(node.condition_nodes[0],blackboard)
        if struct["main"].endswith("（未翻译）"): # 未翻译，增加标识符
            struct["main"] = "尝试判断: "+struct["main"]
        # 若main是空的，补一个尝试判断
        if struct["main"] == "":
            if "true" in struct:
                struct["main"] = "尝试判断："+struct["true"]
            elif "false" in struct:
                struct["main"] = "尝试判断："+struct["false"]
            else:
                struct["main"] = "尝试进行未知的判断"
        # 因为IfElse只影响内圈，对外圈逻辑不影响，修改逻辑
        if "true" in struct:
                true_flag = struct["true"]+"："
                struct.pop("true") 
        if "false" in struct:
                false_flag = struct["false"]+"："
                struct.pop("false")
        if "children" not in struct:
            struct["children"] = []
        if "style_closed" in struct:
            del struct["style_closed"]
        # 成功时执行的节点
        if node.succeed_nodes != None and len(node.succeed_nodes) > 0:
            success_translation = anne_node_translate_all(node.succeed_nodes,blackboard)
            if true_flag.endswith("时"):
                success_translation["main"] = true_flag
            else:
                success_translation["main"] = "若" + true_flag
            success_translation["role"] = "condition"
            struct["children"].append(success_translation)
        # 失败时执行的节点
        if node.fail_nodes != None and len(node.fail_nodes) > 0:
            fail_translation = anne_node_translate_all(node.fail_nodes,blackboard)
            if false_flag.endswith("时"):
                fail_translation["main"] = false_flag
            else:
                fail_translation["main"] = "若" + false_flag
            fail_translation["role"] = "condition"
            struct["children"].append(fail_translation)
        # 存储翻译
        node.translation = struct
        return struct
    else:
        return node.translation

# IfConditions的特殊处理
def anne_node_translate_ifconditions(node,blackboard):
    if node.translation == None:
        node_data = node.node_data
        # 检查条件数量
        if node.condition_nodes == None:
            return {"main" : "无效的判断节点"}
        if len(node.condition_nodes) == 1: # 如果只有一个，那你tmd为什么不用IfElse呢？？？
            return anne_node_translate_ifelse(node,blackboard)
        # 判断节点
        struct = {
            "main" : "",
            "children" : []
        }
        structs = []
        true_flag = "如果是/有/可行/可处理："
        false_flag = "如果不是/没有/不可行/无法处理："
        #开始处理
        for sub_node in node.condition_nodes:
            structs.append(anne_node_translate(sub_node))
        true_flags = []
        false_flags = []
        index = 0
        for _struct in structs:
            if _struct["main"] == "":
                if "true" in _struct:
                    _struct["main"] = "检查：" + _struct["true"]
                elif "false" in _struct:
                    _struct["main"] = "检查：" + _struct["false"]
                else:
                    _struct["main"] = "进行未知的检查"
            _struct["main"] = DEX[index] + _struct["main"]
            if "true" in _struct:
                text = _struct["true"]
                text = DEX[index] + text
                true_flags.append(text)
                del _struct["true"]
            else:
                true_flags.append(_struct["main"]+"处理成功")
            if "false" in _struct:
                text = _struct["false"]
                text = DEX[index] + text
                false_flags.append(text)
                del _struct["false"]
            else:
                false_flags.append(_struct["main"]+"处理成功")
            index += 1
        # IfConditions同样只影响内圈，对外圈逻辑不影响
        if node_data["_isAnd"]:
            struct["main"] = "尝试判断多个条件，是否同时满足："
            true_flag = "若 " + " 且 ".join(true_flags)+"："
            false_flag = "若 " + " 或 ".join(false_flags)+"："
        else:
            struct["main"] = "尝试判断多个条件，是否满足其中任意一个："
            true_flag = "若 " + " 或 ".join(true_flags)+"："
            false_flag = "若 " + " 且 ".join(false_flags)+"："
        # 条件节点
        struct["children"] += structs
        # 成功时执行的节点
        if node.succeed_nodes != None and len(node.succeed_nodes) > 0:
            success_translation = anne_node_translate_all(node.succeed_nodes,blackboard)
            success_translation["main"] = true_flag
            success_translation["role"] = "condition"
            struct["children"].append(success_translation)
        # 失败时执行的节点
        if node.fail_nodes != None and len(node.fail_nodes) > 0:
            fail_translation = anne_node_translate_all(node.fail_nodes,blackboard)
            fail_translation["main"] = false_flag
            fail_translation["role"] = "condition"
            struct["children"].append(fail_translation)
        # 存储翻译
        node.translation = struct
        return struct
    else:
        return node.translation