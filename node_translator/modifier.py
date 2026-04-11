#----------------------------------------
# 调整值专用的Node
#----------------------------------------
from .analyzer import anne_dictionary

# 是否为伤害？实际判定上为检查是否为伤害+伤害类型不为治疗
def node_IsDamage(node):
    return {
        "main" : "",
        "true" : f"若本次调整值为治疗以外类型的伤害",
        "false" : f"若本次调整值不为伤害，或为治疗类型的伤害"
    }

# 是否为治疗？实际判定上为检查是否为伤害+伤害类型为治疗
def node_IsHeal(node):
    return {
        "main" : "",
        "true" : f"若本次调整值为治疗（治疗类型的伤害）",
        "false" : f"若本次调整值不为治疗（治疗类型的伤害）"
    }

# 是否为元素损伤？最早明日方舟没有元素伤害这一概念，因此ElementDamage一直都是元素损伤
def node_IsElementDamage(node):
    return {
        "main" : "",
        "true" : f"若本次调整值为元素损伤",
        "false" : f"若本次调整值不为元素损伤"
    }

# 伤害的攻击力倍率是否为0？
def node_IsAtkScaleZero(node):
    return {
        "main" : "",
        "true" : f"若本次伤害的攻击力倍率为零",
        "false" : f"若本次伤害的攻击力倍率不为零"
    }

# 调整值实际产生影响后是否
def node_FilterModifierByRealDelta(node):
    modifier_target = anne_dictionary("modifier_target_type",node["_modifierTargetType"])
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    return {
        "main" : "在调整值影响后",
        "true" : f"若 {modifier_target} {compare} 原先的{modifier_target}",
        "false" : f"若 {modifier_target} {compare_not} 原先的{modifier_target}"
    }

# 检查调整值是否带有标记
def node_CheckModifierContainsKey(node):
    return {
        "main" : f"检查事件调整值是否具有\"{node['_customKey']}\"标记",
        "true" : f"若具有\"{node['_customKey']}\"标记",
        "false" : f"若没有\"{node['_customKey']}\"标记"
    }

# 取消调整值
def node_CancelModifier(node):
    reason = anne_dictionary("cancel_reason",node["_reason"])
    return {"main" : "取消本次调整值，原因："+reason}

# 确保伤害或治疗量至少有...
def node_EnsureDmgOrHeal(node):
    return {
        "main" : f"确保本次伤害或治疗量至少有 持有者攻击力 × [{node['_key']}] 点（若低于则设置为这个值）",
        "true" : "若此次调整值是伤害或治疗",
        "false" : "若此次调整值不是伤害也不是治疗"
    }

# 检查伤害的详细信息
def node_FilterDamageModifer(node):
    short_conditions = []
    conditions = []
    can_short = True
    # 检查来源
    if node["_filterModifierSource"]:
        if node["_filterBySourceId"]: # 依照ID来筛选
            conditions.append("来源ID为"+node["_sourceId"])
            short_conditions.append("源自 "+node["_sourceId"]+" 的")
        else:
            target_name = anne_dictionary("target",node["_source"])
            conditions.append("来源为"+target_name)
            short_conditions.append("源自"+target_name+"的")
    else: # 仅仅检查是否为有来源？
        if node["_checkHasScource"]: # 原文如此啊原文如此
            if node["_isNoSource"]:
                conditions.append("无来源")
                short_conditions.append("无来源的")
            else:
                conditions.append("存在来源")
                short_conditions.append("存在来源的")
    # 检查施加途径
    if node["_filterApplyWay"]:
        apply_way = anne_dictionary("apply_way",node["_applyWay"])
        conditions.append("施加途径为"+apply_way)
        short_conditions.append(apply_way+"途径的")
    # 检查伤害类型
    if node["_filterDamageType"]:
        damage_type = anne_dictionary("damage_type",node["_damageMask"])
        conditions.append("伤害类型为"+damage_type)
        if node["_filterSharedMask"] and node["_sharedFlag"] == "SKIP_MODIFIER_EVENT": # 生命流失
            if node["_damageMask"] == "PURE":
                short_conditions.append("生命流失")
            else:
                short_conditions.append(damage_type+"流失")
        else:
            short_conditions.append(damage_type)
    # 检查攻击类型
    if node["_filterAttackType"]:
        attack_type = anne_dictionary("attack_type",node["_attackTypeFilter"])
        conditions.append("攻击类型为"+attack_type)
        short_conditions.append(attack_type)
    # 检查标签
    if node["_filterSharedMask"] and (not node["_filterDamageType"] or node["_sharedFlag"] != "SKIP_MODIFIER_EVENT"): #生命流失前面处理过了
        shared_flag = anne_dictionary("sharedflag",node["_sharedFlag"])
        conditions.append("具有"+shared_flag+"标签")
        can_short = False
    # 写入条件    if len(conditions) > 0:
    result = {}
    if can_short:
        result["main"] = f"检查本次伤害"
        result["true"] = "若为"+"".join(short_conditions)+"伤害"
        result["false"] = "若不为"+"".join(short_conditions)+"伤害（或不是伤害）"
    else:
        result["main"] = f"检查本次伤害是否满足：{'、'.join(conditions)}"
        result["true"] = "若伤害满足上述所有条件"
        result["false"] = "若伤害不满足上述条件（或不是伤害）"
    # 检查未被取消
    if node["_filterModifierCancelled"]:
        result["true"] += "且未被取消"
        result["false"] += "或已被取消"
    return result