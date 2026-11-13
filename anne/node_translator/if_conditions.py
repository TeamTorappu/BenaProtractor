#----------------------------------------
# 多条件判断式Node
#----------------------------------------
from dictionary import anne_dictionary

DEX = "①②③④⑤⑥⑦⑧⑨"

# 如果全部+否则 / 如果任一+否则
def IfConditions(node,blackboard):
    from anne.action import Action
    from anne.node import Node
    #return {"main" : "如果满足条件...","true":"如果是...","false":"如果不是..."}
    # 检查条件数量
    if node["_conditionsNode"] == None or len(node["_conditionsNode"]) == 0:
        return {"main" : "无效的判断节点"}
    # 判断节点
    result = {
        "main" : "",
        "children" : []
    }
    results = []
    true_flag = "如果是/有/可行/可处理："
    false_flag = "如果不是/没有/不可行/无法处理："
    #开始处理
    for sub_node in node["_conditionsNode"]:
        results.append(Node(sub_node).translate(blackboard))
    true_flags = []
    false_flags = []
    index = 0
    for _result in results:
        if _result["main"] == "":
            if "true" in _result:
                _result["main"] = "检查：" + _result["true"]
            elif "false" in _result:
                _result["main"] = "检查：" + _result["false"]
            else:
                _result["main"] = "进行未知的检查"
        _result["main"] = DEX[index] + _result["main"]
        if "true" in _result:
            text = _result["true"]
            text = DEX[index] + text
            true_flags.append(text)
            del _result["true"]
        else:
            true_flags.append(_result["main"]+"处理成功")
        if "false" in _result:
            text = _result["false"]
            text = DEX[index] + text
            false_flags.append(text)
            del _result["false"]
        else:
            false_flags.append(_result["main"]+"处理成功")
        index += 1
    # IfConditions同样只影响内圈，对外圈逻辑不影响
    if node["_isAnd"]:
        result["main"] = "尝试判断多个条件，是否同时满足："
        true_flag = "若 " + " 且 ".join(true_flags)+"："
        false_flag = "若 " + " 或 ".join(false_flags)+"："
    else:
        result["main"] = "尝试判断多个条件，是否满足其中任意一个："
        true_flag = "若 " + " 或 ".join(true_flags)+"："
        false_flag = "若 " + " 且 ".join(false_flags)+"："
    # 条件节点
    result["children"] += results
    
    # 成功时执行的节点
    if node["_succeedNodes"] != None and len(node["_succeedNodes"]) > 0:
        success_translation = Action(node["_succeedNodes"]).translate(blackboard)
        success_translation["main"] = true_flag
        success_translation["role"] = "condition"
        result["children"].append(success_translation)
    # 失败时执行的节点
    if node["_failNodes"] != None and len(node["_failNodes"]) > 0:
        fail_translation = Action(node["_failNodes"]).translate(blackboard)
        fail_translation["main"] = false_flag
        fail_translation["role"] = "condition"
        result["children"].append(fail_translation)

    return result