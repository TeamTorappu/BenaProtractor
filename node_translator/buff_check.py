#----------------------------------------
# Buff相关的检查类Node
#----------------------------------------
from translator import anne_dictionary

# 检查是否持有某Buff
def node_CheckContainsBuff(node):
    # 未解析参数：_loadFromBlackboard _checkSourceHost
    target_name = anne_dictionary("target",node["_targetType"])
    condition = f"检查{target_name}是否"
    true_flag = "若其持有该Buff"
    false_flag = "若其没有该Buff"
    if node["isAND"]: # 与模式
        if len(node["_buffKeys"]) > 1:
            buffs = '、'.join([f"<{key}>" for key in node['_buffKeys']])
            if node["_checkBuffSource"]:
                source_name = anne_dictionary("target",node["_buffSourceType"])
                condition += f"同时持有来自{source_name}的 {buffs} Buff"
            else:
                condition += f"同时持有 {buffs} Buff"
            true_flag = "若其持有全部这些Buff"
            false_flag = "若其少了其中任意一个Buff"
        elif len(node["_buffKeys"]) == 1:
            if node["_checkBuffSource"]:
                source_name = anne_dictionary("target",node["_buffSourceType"])
                condition += f"持有来自{source_name}的 <{node['_buffKeys'][0]}> Buff"
            else:
                condition += f"持有 <{node['_buffKeys'][0]}> Buff"
    else: # 或模式
        if len(node["_buffKeys"]) > 1:
            buffs = '、'.join([f"<{key}>" for key in node['_buffKeys']])
            if node["_checkBuffSource"]:
                source_name = anne_dictionary("target",node["_buffSourceType"])
                condition += f"持有来自{source_name}的 {buffs} 中的任意一个Buff"
            else:
                condition += f"持有 {buffs} 中的任意一个Buff"
            true_flag = "若其持有其中任意一个Buff"
            false_flag = "若其全部Buff都没有"
        elif len(node["_buffKeys"]) == 1:
            if node["_checkBuffSource"]:
                source_name = anne_dictionary("target",node["_buffSourceType"])
                condition += f"持有来自{source_name}的 <{node['_buffKeys'][0]}> Buff"
            else:
                condition += f"持有 <{node['_buffKeys'][0]}> Buff"
    if condition != "" :
        return {
            "main" : condition,
            "true" : true_flag,
            "false" : false_flag
        }
    else:
        return {
            "main" : "检查持有的Buff，但给定条件无法检查（写法有误？）",
            "true" : "始终不通过",
            "false" : "始终通过"
        }

# 检查是否持有本Buff的某个附属Buff
def node_CheckContainsDerviedBuff(node):
    return {
        "main" : f"检查持有者是否持有本Buff的附属Buff <{node['_derviedBuffKey']}>",
        "true" : "若持有者同时持有该附属Buff",
        "false" : "若持有者不持有该附属Buff"
    }

# 检查Buff剩余持续时间
def node_CheckRemainTime(node):
    remaining_time = node["_checkRemainTime"]
    return {
        "main" : "检查本Buff的剩余持续时间",
        "true" : f"若剩余时间 ≤ {remaining_time}秒",
        "false" : f"若剩余时间 > {remaining_time}秒"
    }