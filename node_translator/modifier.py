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