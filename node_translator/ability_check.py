#----------------------------------------
# 能力相关的检测类Node
#----------------------------------------
from .analyzer import anne_dictionary

# 检查能力用途
def node_FilterAbilityFamily(node):
    family = anne_dictionary("ability_family",node["_familyGroupMask"])
    return {
        "main" : "检查此能力的类别（或称用途）",
        #"description" : "分为：常规攻击、阻挡攻击、技能、天赋、无特定类别；\"特性\"也是一种天赋或无特定类型能力",
        "true" : "若其隶属于"+family,
        "false" : "若其不隶属于"+family,
    }


# 检查角色技能状态
def node_CheckCharSkillAffecting(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_checkTargetHost"]:
        return {
            "main" : f"检查{target_name}（角色类）的技能状态（若对方为召唤物，改为检查其主人）",
            "true" : "若检查对象处于技能期间",
            "false" : "若检查对象不处于技能期间"
        }
    else:
        return {
            "main" : f"检查{target_name}（角色类）的技能状态",
            "true" : "若其处于技能期间",
            "false" : "若其不处于技能期间"
        }
    
# 检查携带的技能（仅限角色类可用）
def node_CheckSkillIndex(node):
    owner_name = anne_dictionary("target",node["_ownerType"])
    return {
        "main" : f"检查{owner_name}（角色类）携带的技能",
        "true" : f"若{owner_name}携带的是{node['_skillIndex'] + 1}技能", # Index从0开始，技能序号从1开始
        "false" : f"若{owner_name}携带的是其他技能"
    }

# 检查技能触发类型
def node_CheckCharacterSkillType(node):
    target_name = anne_dictionary("target",node["_targetType"])
    skill_type = anne_dictionary("skill_type",node["_skillType"])
    return {
        "main" : f"检查{target_name}（角色类）携带技能的触发类型",
        "true" : f"若其为 {skill_type} 技能",
        "false" : f"若其不为 {skill_type} 技能"
    }

# 检查上下文能力的当前目标数
def node_FilterAbilityValidCastTargetCnt(node):
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    return {
        "main" : f"检查当前\"上下文\"能力的有效目标数量",
        "true" : f"若目标数 {compare} [cnt]",
        "false" : f"若目标数 {compare_not} [cnt]"
    }