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