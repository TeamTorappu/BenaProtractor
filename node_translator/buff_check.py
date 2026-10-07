#----------------------------------------
# Buff相关的检查类Node
#----------------------------------------
from dictionary import anne_dictionary

# 检查是否持有某Buff
def CheckContainsBuff(node,blackboard):
    # 未解析参数：
    target_name = anne_dictionary("target",node["_targetType"])
    condition = f"检查{target_name}是否"
    true_flag = "其持有该Buff"
    false_flag = "其没有该Buff"
    if node["_loadFromBlackboard"]: # 定向甄选
        condition += f"持有黑板 [buff_key] 记载的buff"
    elif node["isAND"]: # 与模式
        if len(node["_buffKeys"]) > 1:
            buffs = '、'.join([f"<{key}>" for key in node['_buffKeys']])
            if node["_checkBuffSource"]:
                source_name = anne_dictionary("target",node["_buffSourceType"])
                condition += f"同时持有来自{source_name}的 {buffs} Buff"
            else:
                condition += f"同时持有 {buffs} Buff"
            true_flag = "其持有全部这些Buff"
            false_flag = "其少了其中任意一个Buff"
        elif len(node["_buffKeys"]) == 1:
            if node["_checkBuffSource"]:
                source_name = anne_dictionary("target",node["_buffSourceType"])
                if node["_checkSourceHost"]:
                    source_name = source_name+"（召唤物）的主人"
                condition += f"持有来自{source_name}的 <{node['_buffKeys'][0]}> Buff"
            else:
                condition += f"持有 <{node['_buffKeys'][0]}> Buff"
    else: # 或模式
        if len(node["_buffKeys"]) > 1:
            buffs = '、'.join([f"<{key}>" for key in node['_buffKeys']])
            if node["_checkBuffSource"]:
                source_name = anne_dictionary("target",node["_buffSourceType"])
                if node["_checkSourceHost"]:
                    source_name = source_name+"（召唤物）的主人"
                condition += f"持有来自{source_name}的 {buffs} 中的任意一个Buff"
            else:
                condition += f"持有 {buffs} 中的任意一个Buff"
            true_flag = "其持有其中任意一个Buff"
            false_flag = "其全部Buff都没有"
        elif len(node["_buffKeys"]) == 1:
            if node["_checkBuffSource"]:
                source_name = anne_dictionary("target",node["_buffSourceType"])
                if node["_checkSourceHost"]:
                    source_name = source_name+"（召唤物）的主人"
                condition += f"持有来自{source_name}的 <{node['_buffKeys'][0]}> Buff"
            else:
                condition += f"持有 <{node['_buffKeys'][0]}> Buff"
    if condition != "" :
        return {
            "main" : condition,
            "link" : "buff." + ",buff.".join(node["_buffKeys"]),
            "true" : true_flag,
            "false" : false_flag
        }
    else:
        return {
            "main" : "检查持有的Buff，但给定条件无法检查（写法有误？）",
            "true" : "始终不通过",
            "false" : "始终通过"
        }

# 检查是否持有本Buff的附属Buff
def CheckContainsDerviedBuff(node,blackboard):
    if node["_derviedBuffKey"] != None and node["_derviedBuffKey"] != "":
        return {
            "main" : f"检查持有者是否同时持有本Buff的附属Buff <{node['_derviedBuffKey']}>",
            "link" : f"buff.{node['_derviedBuffKey']}",
            "true" : "其同时持有该附属Buff",
            "false" : "其不持有该附属Buff"
        }
    else:
        return {
            "main" : f"检查持有者是否同时持有本Buff的任意附属Buff",
            "true" : "其同时持有本Buff的任一附属Buff",
            "false" : "其不持有本Buff的任何附属Buff"
        }

# 检查Buff剩余持续时间
def CheckRemainTime(node,blackboard):
    remaining_time = node["_checkRemainTime"]
    return {
        "main" : "检查本Buff的剩余持续时间",
        "true" : f"剩余时间 ≤ {remaining_time}秒",
        "false" : f"剩余时间 > {remaining_time}秒"
    }

# 检查上下文中的Buff的名称
def CheckMainBuffId(node,blackboard):
    return {
        "main" : "检查\"上下文\"中的那个Buff的名称",
        "true" : f"该Buff名称为 <{node['_idToFilter']}>",
        "false" : f"该Buff名称不为 <{node['_idToFilter']}>"
    }

# 检查Buff叠加层数
def FilterByBuffStackCount(node,blackboard):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_checkTargetHost"]:
        target_name = target_name+"（召唤物）的主人"
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    features = []
    # 处理Buff对象
    buff_name = f"名为 <{node['_buffKey']}> Buff"
    if node["_checkBuffSource"]:
        if node["_sourceType"] == "BUFF_SOURCE":
            buff_name = "相同来源的、" + buff_name
        else:
            buff_source = anne_dictionary("target",node["_sourceType"])
            buff_name = "来源于" + buff_source + "的、" + buff_name
    # 处理右侧比对对象
    default_value = int(node["_stackCount"]) - int(node["_stackCountPeeling"])
    right_value = f"{default_value}"
    if node["_stackCountKey"] != "" and node["_stackCountKey"] != "_":
        if node["_stackCountPeeling"] != 0:
            if node["_stackCountKey"] in blackboard:
                bb_value = int(blackboard[node["_stackCountKey"]]) - int(node["_stackCountPeeling"])
                right_value = f"{bb_value}"
            else:
                right_value = f"[{node['_stackCountKey']}]（默认{default_value}） - {node['_stackCountPeeling']}"
        else:
            if node["_stackCountKey"] in blackboard:
                bb_value = int(blackboard[node["_stackCountKey"]])
                right_value = f"{bb_value}"
            else:
                right_value = f"[{node['_stackCountKey']}]（默认{default_value}）"
    # 特征
    if node["_checkFromUnoverridableBuffCount"]: # 不知道什么效果
        features.append("checkFromUnoverridableBuffCount")
    if node["_checkSnapshotBuff"]: # 不知道什么效果
        features.append("checkSnapshotBuff")

    # 返回结果
    result = {
        "main" : f"检查{target_name}持有的所有{buff_name}的总层数",
        "true" : f"Buff总层数 {compare} {right_value}",
        "false" : f"Buff总层数 {compare_not} {right_value}",
        "description" : "通常等同于\"该名称Buff的数量\"；层数上限由第一个施加的Buff决定，超出层数上限的层数无效"
    }
    if len(features) > 0:
        result["description"] += "；"+"；".join(features)
    return result