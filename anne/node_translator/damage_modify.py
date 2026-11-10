#----------------------------------------
# 修改伤害类Node
#----------------------------------------
from analyzer import to_percent
from dictionary import anne_dictionary

# 弱点伤害（必须于计算伤害时使用）
def WeakDamage(node,blackboard):
    #source_name = anne_dictionary("target",node["_sourceType"])
    return {
        #"main" : f"让{source_name}的本次伤害变为弱点伤害",
        "main" : f"让本次伤害变为弱点伤害",
        "description" : "分别预计算一次物理和一次法术伤害，将本次伤害的伤害类型改为前两者之间的高者",
        "true" : "转换前伤害为物理/法术伤害",
        "false" : "转换前伤害不为物理/法术伤害"
    }

# “分摊伤害”，实际上是给予其他单位当前伤害的一部分。
def DamageSplit(node,blackboard):
    target_name = anne_dictionary("target",node["_targetType"])
    attack_type = anne_dictionary("attack_type",node["_attackType"])
    return {"main" : f"将本次伤害的X%以同类型{attack_type}伤害的形式传递给{target_name}（原伤害不会变化）"}

# 伤害倍率
def DamageScale(node,blackboard):
    # 未解析参数：_isValidStackCnt
    damage_scale = ""
    action = "提升/降低"
    bb_key = "damage_resistance" if node["_isOneMinus"] else "damage_scale"
    # 自定义bb_key
    if node["_customKey"] != None and node["_customKey"] != "":
        bb_key = node['_customKey']
    # 减伤值
    if bb_key in blackboard:
        damage_scale_var = 1
        if node["_isStackable"] and node["_isOneMinus"]: # 公式：(1-nx)
            damage_scale = f"(1 - {blackboard[bb_key]} × Buff层数) 倍"
        elif node["_isOneMinus"]: # 公式：(1-x)
            damage_scale_var = 1 - blackboard[bb_key]
            if damage_scale_var > 1:
                action = "提升"
            if damage_scale_var < 1:
                action = "降低"
            damage_scale = to_percent(damage_scale_var)
        elif node["_isStackable"]: # 公式：(1+nx)
            damage_scale = f"(1 + {blackboard[bb_key]} × Buff层数) 倍"
        else:
            damage_scale_var = blackboard[bb_key]
            if damage_scale_var > 1:
                action = "提升"
            if damage_scale_var < 1:
                action = "降低"
            damage_scale = to_percent(damage_scale_var)
    else:
        if node["_isStackable"] and node["_isOneMinus"]: # 公式：(1-nx)
            damage_scale = f"(1 - [{bb_key}] × Buff层数) 倍"
            action = "降低"
        elif node["_isOneMinus"]: # 公式：(1-x)
            damage_scale = f"(1 - [{bb_key}]) 倍"
            action = "降低"
        elif node["_isStackable"]: # 公式：(1+nx)
            damage_scale = f"(1 + [{bb_key}] × Buff层数) 倍"
        else: # 公式：x
            damage_scale = f" [{bb_key}] 倍"
    text = f"令本次伤害{action}至{damage_scale}"
    # 检查伤害类型与施加方式
    conditions = []
    if node["_filterDamageType"]:
        conditions.append("伤害类型为"+anne_dictionary("damage_type",node["_damageMask"]))
    if node["_filterApplyWay"]:
        if node["_applyWayFilter"] == "NONE":
            conditions.append("施加方式为无类型施加")
        elif node["_applyWayFilter"] == "MELEE":
            conditions.append("施加方式为近战")
        elif node["_applyWayFilter"] == "RANGED":
            conditions.append("施加方式为远程")
    
    # 差值记录，一般是拿来算“减少部分的伤害”的
    if node["_cachedDeltaValueToBBKey"] != None and node["_cachedDeltaValueToBBKey"] != "":
        text += "，并将减少/增加的部分记入 [" + node["_cachedDeltaValueToBBKey"] + "]"
    # 返回
    if len(conditions) > 0:
        return {
            "main" : f"若{'且'.join(conditions)}，{text}",
            "true" : f"若成功修改伤害",
            "false" : f"若不满足条件或无法修改伤害"
        }
    return {
        "main" : text,
        "true" : f"若成功修改伤害",
        "false" : f"若无法修改伤害"
    }

# 基于距离的伤害倍率提升
def DamageScaleBaseOnDistance(node,blackboard):
    target_name = anne_dictionary("target",node["_targetType"])
    source_name = anne_dictionary("target",node["_sourceType"])
    condition = ""
    result = {}
    if node["_filterDamageType"] and node["_filterApplyWay"]: # 伤害类型与施加途径筛选
        damage_type = anne_dictionary("damage_type",node["_damageMask"])
        apply_way = anne_dictionary("apply_way",node["_applyWayFilter"])
        condition = f"若本次伤害是{apply_way}的{damage_type}伤害，"
        result["true"] = f"若本次伤害的伤害类型为{damage_type}且施加途径为{apply_way}"
        result["false"] = f"若本次伤害的伤害类型不为{damage_type}或者施加途径不为{apply_way}"
    elif node["_filterDamageType"]: # 伤害类型筛选
        damage_type = anne_dictionary("damage_type",node["_damageMask"])
        condition = f"若本次伤害是{damage_type}伤害，"
        result["true"] = f"若本次伤害的伤害类型为{damage_type}"
        result["false"] = f"若本次伤害的伤害类型不为{damage_type}"
    elif node["_filterApplyWay"]: # 施加途径筛选
        apply_way = anne_dictionary("apply_way",node["_applyWayFilter"])
        if node["_applyWayFilter"] == "NONE":
            apply_way = "无"
        condition = f"若本次伤害由{apply_way}途径施加，"
        result["true"] = f"若本次伤害的施加途径为{apply_way}"
        result["false"] = f"若本次伤害的施加途径不为{apply_way}"
    # 距离核心计算逻辑
    if node["_reverseDistance"]:
        damage_scale = to_percent(1. + node["_maxScale"])
        result["main"] = f"{condition}计算{source_name}与{target_name}之间的直线距离，令本次伤害提升至 linearstep(直线距离,[max_dist],[min_dist]) × (1 + [damage_scale])"
        result["description"] = f"三个黑板值默认为浮点数类型上限、{node['_minTriggerDistance']}、{node['_maxScale']}"
    else:
        result["main"] = f"{condition}计算{source_name}与{target_name}之间的直线距离，令本次伤害提升至 linearstep(直线距离,[min_dist],[max_dist]) × (1 + [damage_scale])"
        result["description"] = f"三个黑板值默认为{node['_minTriggerDistance']}、浮点数类型上限、{node['_maxScale']}"
    return result

# 闪避伤害
def Evade(node,blackboard):
    features = []
    # 检查伤害类型
    if node["_damageMask"] != "ALL":
        damage_type = anne_dictionary("damage_type",node["_damageMask"])
        features.append(f"{damage_type}")
    # 检查伤害的施加方式
    if node["_applyWayFilter"] == "NONE": # 仅无类型
        features.append("无途径")
    elif node["_applyWayFilter"] == "MELEE": # 无类型与近战
        features.append("近战")
    elif node["_applyWayFilter"] == "RANGED": # 无类型与远程
        features.append("远程")
    #elif node["_applyWayFilter"] == "ALL": # 全部都可以就不用写了
    result = {
        "main" : "有 [prob] 概率闪避此次伤害（\"骰子\"判定）",
        "true" : "闪避成功",
        "false" : "闪避失败或无法处理"
    }
    if "prob" in blackboard:
        result["main"] = "有" + to_percent(blackboard["prob"]) + "概率闪避此次伤害（\"骰子\"判定）"
    if len(features) > 0:
        result["main"] = "若此次伤害为" + ",".join(features) + "伤害，" + result["main"]
        result["true"] = "伤害合规且闪避成功"
        result["false"] = "伤害不合规、闪避失败、或无法处理"
    return result
    
# 增加附加攻击力（逻哥2天赋）
def AtkAdditionUpBeforeCalcDamage(node,blackboard):
    if node["_filterDamageType"]:
        damage_type = anne_dictionary("damage_type",node["_damageType"])
        return {
            "main" : f"若本次伤害类型为{damage_type}，令其附加攻击力增加 {node['_atkAdditionKey']}（默认{node['_defaultValue']}点）",
            "true" : f"本次伤害确为{damage_type}伤害",
            "false" : f"本次伤害不为{damage_type}伤害"
        }
    else:
        return {
            "main" : f"令本次伤害的附加攻击力增加 {node['_atkAdditionKey']}（默认{node['_defaultValue']}点）"
        }

# 修改伤害类型（弱点伤害相关机制）
def ModifyDamageType(node,blackboard):
    damage_type = anne_dictionary("damage_type",node["_damageType"])
    return {
        "main" : f"将本次伤害的类型改为{damage_type}"
    }