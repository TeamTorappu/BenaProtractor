#----------------------------------------
# 修改伤害类Node
#----------------------------------------
from .analyzer import to_percent
from translator import anne_dictionary

# 弱点伤害（必须于计算伤害时使用）
def node_WeakDamage(node):
    #source_name = anne_dictionary("target",node["_sourceType"])
    return {
        #"main" : f"让{source_name}的本次伤害变为弱点伤害",
        "main" : f"让本次伤害变为弱点伤害",
        "description" : "分别预计算一次物理和一次法术伤害，将本次伤害的伤害类型改为前两者之间的高者",
        "true" : "若转换前伤害为物理/法术伤害",
        "false" : "若转换前伤害不为物理/法术伤害"
    }

# “分摊伤害”，实际上是给予其他单位当前伤害的一部分。
def node_DamageSplit(node):
    target_name = anne_dictionary("target",node["_targetType"])
    attack_type = anne_dictionary("attack_type",node["_attackType"])
    return {"main" : f"将本次伤害的X%以同类型{attack_type}伤害的形式传递给{target_name}（原伤害不会变化）"}

# 伤害倍率
def node_DamageScale(node):
    # 未解析参数：_isValidStackCnt
    damage_scale = ""
    action = "提升"
    # 需要把减伤值改为*(1-X)
    if node["_customKey"] != None and node["_customKey"] != "":
        if node["_isOneMinus"]:
            damage_scale = f"(1 - [{node['_customKey']}])"
            action = "降低"
        else:
            damage_scale = f"(1 + [{node['_customKey']}])"
    else:
        if node["_isOneMinus"]:
            damage_scale = "(1 - [damage_resistance])"
            action = "降低"
        else:
            damage_scale = "(1 + [damage_scale])"
    # 根据Buff层数加倍
    if node["_isStackable"]:
        damage_scale = f"({damage_scale} × Buff层数)"
    text = f"令本次伤害{action}至{damage_scale}倍"
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
    
    if len(conditions) > 0:
        text = f"若{'且'.join(conditions)}，{text}"
    # 差值记录，一般是拿来算“减少部分的伤害”的
    if node["_cachedDeltaValueToBBKey"] != None and node["_cachedDeltaValueToBBKey"] != "":
        text += "，并将减少/增加的部分记入 [" + node["_cachedDeltaValueToBBKey"] + "]"
    return {"main" : text}

# 基于距离的伤害倍率提升
def node_DamageScaleBaseOnDistance(node):
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

# 格挡/护盾/屏障（还得具体情况具体分析）
def node_BlockDamage(node):
    # 未解析参数：_useSource _sourceType
    #source_name = anne_dictionary("target",node["_sourceType"])
    name = "概率格挡/计次护盾"
    features = []
    description = "若无法响应/伤害已被无效化将不会消耗次数（若有），本节点视为无法处理；格挡失败也会视为无法处理，但会消耗次数（若有）"
    # 使用动态值，说明是屏障
    if node["_useDynamicVar"]:
        name = "屏障"
        description = "若无法响应/伤害已被无效化本节点视为无法处理"
        if node["_allowNegativeDynamicVar"]:
            features.append("允许负屏障值")
        if node["_showShieldUI"]:
            features.append("在血条上显示屏障值")
    elif node["_useFixedValue"]: # 使用定值，说明是林式阈值盾
        name = "琉璃壁"
    if node["_showDamageNumber"]:
        features.append("即使成功格挡也显示伤害数值")
    if node["_specifyBlockEffect"] != None:
        features.append("使用格挡特效"+node["_specifyBlockEffect"])
    # 检查伤害的施加方式
    if node["_filterApplyWay"]:
        if node["_applyWayFilter"] == "NONE": # 仅无类型
            features.append("仅响应施加方式为“无”的伤害")
        elif node["_applyWayFilter"] == "MELEE": # 无类型与近战
            features.append("仅响应施加方式为“近战”或“无”的伤害")
        elif node["_applyWayFilter"] == "RANGED": # 无类型与远程
            features.append("仅响应施加方式为“远程”或“无”的伤害")
        #elif node["_applyWayFilter"] == "ALL": # 全部都可以就不用写了
    if len(features) > 0:
        return {
            "main" : name + "（"+",".join(features)+"）",
            "description" : description
        }
    else:
        return {
            "main" : name,
            "description" : description
        }

# 闪避伤害
def node_Evade(node):
    name = "概率/计次闪避"
    features = []
    # 检查伤害类型
    if node["_damageMask"] != "ALL":
        damage_type = anne_dictionary("damage_type",node["_damageMask"])
        features.append(f"伤害类型为{damage_type}")
    # 检查伤害的施加方式
    if node["_applyWayFilter"] == "NONE": # 仅无类型
        features.append("施加方式为“无”")
    elif node["_applyWayFilter"] == "MELEE": # 无类型与近战
        features.append("施加方式为“近战”或“无”")
    elif node["_applyWayFilter"] == "RANGED": # 无类型与远程
        features.append("施加方式为“远程”或“无”")
    #elif node["_applyWayFilter"] == "ALL": # 全部都可以就不用写了
    if len(features) > 0:
        return {
            "main" : name + "（仅响应"+",".join(features)+"的伤害）",
            "description" : "若无法响应/伤害已被无效化将不会消耗次数（若有），本节点视为无法处理；闪避失败也会视为无法处理，但会消耗次数（若有）"
        }
    else:
        return {
            "main" : name,
            "description" : "若无法响应/伤害已被无效化将不会消耗次数（若有），本节点视为无法处理；闪避失败也会视为无法处理，但会消耗次数（若有）"
        }
    
    