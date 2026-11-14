#----------------------------------------
# 逻辑类Node（通常不在这里处理）
#----------------------------------------
from dictionary import enum_dictionary

# 否则
def IfNot(node,blackboard):
    return {"main" : "（反转前一个节点执行成功/失败的结果）"}

# 始终执行
def AlwaysNext(node,blackboard):
    return {"main" : "（不论前一个节点是否成功，始终继续执行）"}

# 循环
def Loop(node,blackboard):
    loop_time = ""
    result = {
        "main" : "循环以下内容："
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
    
    # 循环内容
    from anne.action import Action
    loop_body = Action(node["_loopBody"] or []).translate(blackboard)
    result["children"] += loop_body["children"]
    
    # 失败终止模式 vs 成功终止模式
    if node["_stopWhenPreviousSucceed"]:
        # result["description"] = "若内部任一节点执行失败将进入下次循环；若全部执行成功将提前终止循环；本节点始终视为执行成功"
        result["description"] = "若内部任一节点执行失败，尝试进行下一次循环"
        result["children"].append({"main" : "跳出循环"})
    else:
        result["description"] = "若内部任一节点执行失败，仅此次结束循环"
    return result

# 分区执行
def AlwaysExecuteNodeList(node,blackboard):
    result = {
        "main" : "分区执行以下节点：",
        "description" : "分区之间的运行互不干扰，内部处理失败时改为转跳至下一分区",
        "children" : []
    }
    if node["_failWhenOneFail"]:
        result["true"] = "若所有分区均执行成功，无一失败"
        result["false"] = "若任一分区执行中止"
    # 分区
    from anne.action import Action
    index = 1
    for chunk_nodes in node["_nodes"]:
        chunk = Action(chunk_nodes).translate(blackboard)
        chunk["main"] = f"第{index}分区："
        index += 1
        result["children"].append(chunk)
    return result
