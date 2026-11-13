#----------------------------------------
# 条件判断式Node
#----------------------------------------
from dictionary import anne_dictionary

# 如果+否则
def IfElse(node,blackboard):
    from anne.action import Action
    from anne.node import Node
    #return {"main" : "如果...","true":"如果是...","false":"如果不是..."}
    # 判断节点
    true_flag = "如果是/有/可行/可处理："
    false_flag = "如果不是/没有/不可行/无法处理："
    if node["_conditionNode"] == None:
        return {"main" : "无效的判断节点"}
    result = Node(node["_conditionNode"]).translate(blackboard)
    if result["main"].endswith("（未翻译）"): # 未翻译，增加标识符
        result["main"] = "尝试判断: "+result["main"]
    # 若main是空的，补一个尝试判断
    elif result["main"] == "":
        result["main"] = "尝试判断："

    # 因为IfElse只影响内圈，对外圈逻辑不影响，修改逻辑
    if "true" in result:
        true_flag = result["true"]+"："
        result.pop("true") 
    if "false" in result:
        false_flag = result["false"]+"："
        result.pop("false")
    if "children" not in result:
        result["children"] = []
    if "style_closed" in result:
        del result["style_closed"]
    
    # 成功时执行的节点
    if node["_succeedNodes"] != None and len(node["_succeedNodes"]) > 0:
        success_translation = Action(node["_succeedNodes"]).translate(blackboard)
        if true_flag.endswith("时"):
            success_translation["main"] = true_flag
        else:
            success_translation["main"] = "若" + true_flag
        success_translation["role"] = "condition"
        result["children"].append(success_translation)
    # 失败时执行的节点
    if node["_failNodes"] != None and len(node["_failNodes"]) > 0:
        fail_translation = Action(node["_failNodes"]).translate(blackboard)
        if false_flag.endswith("时"):
            fail_translation["main"] = false_flag
        else:
            fail_translation["main"] = "若" + false_flag
        fail_translation["role"] = "condition"
        result["children"].append(fail_translation)
    
    return result