#----------------------------------------
# 逻辑类Node（通常不在这里处理）
#----------------------------------------
from translator import anne_dictionary

# 逻辑 如果+否则
def node_IfElse(node):
    return {"main" : "如果...","true":"如果是...","false":"如果不是..."}

# 逻辑 如果全部+否则
def node_IfConditions(node):
    return {"main" : "如果满足条件...","true":"如果是...","false":"如果不是..."}

# 假节点，用于翻译占位
def node_Dummy(node):
    return {"main" : node["_dummy"]}

# 否则
def node_IfNot(node):
    return {"main" : "（反转前一个节点执行成功/失败的结果）"}

# 始终执行
def node_AlwaysNext(node):
    return {"main" : "（不论前一个节点是否成功，始终继续执行）"}

# 循环
def node_Loop(node):
    loop_time = ""
    result = {
        "sub_nodes" : node["_loopBody"]
    }
    if node["_useMappingList"]: # 按数据循环
        key_mapping_list = node["_keyMappingList"]
        result["main"] = f"进行{len(key_mapping_list)}次循环，并在每次循环前设置黑板值："
        result["children"] = [
            {
                "main" : "根据循环次数，设置黑板值：",
                "children" : []
            }
        ]
        index = 1
        for key_mapping in key_mapping_list:
            maps = []
            for mapping in key_mapping["mapping"]:
                key = mapping["target"]
                value = mapping["source"]
                maps.append(f"[{key}] = [{value}]")
            result["children"][0]["children"].append(f"第{index}次循环： "+"；".join(maps))
            index += 1
    elif node["_loopCntKey"] != None and node["_loopCntKey"] != "": # 按黑板记载次数循环
        loop_time = f" [{node['_loopCntKey']}] 次"
        if node["_loopCnt"] != 0:
            loop_time += f"（默认{node['_loopCnt']}次）"
        result["main"] = f"循环执行以下内容{loop_time}："
    elif node["_loopCnt"] != 0: # 按固定次数循环
        loop_time = f"{node['_loopCnt']}次"
        result["main"] = f"循环执行以下内容{loop_time}："
    else: # 无限循环
        result["main"] = "无限循环以下内容："
    # 失败终止模式 vs 成功终止模式
    if node["_stopWhenPreviousSucceed"]:
        # result["description"] = "若内部任一节点执行失败将进入下次循环；若全部执行成功将提前终止循环；本节点始终视为执行成功"
        result["description"] = "若内部任一节点执行失败，尝试进行下一次循环"
        result["sub_nodes"].append({
            "$type" : "Torappu.Battle.Action.Nodes+Dummy, Assembly-CSharp",
            "_dummy" : "跳出循环"
        })
    else:
        result["description"] = "若内部任一节点执行失败，仅此次结束循环"
    return result