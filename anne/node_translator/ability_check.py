#----------------------------------------
# 能力相关的检测类Node
#----------------------------------------
from dictionary import anne_dictionary

# 检查能力用途
def FilterAbilityFamily(node,blackboard):
    family = anne_dictionary("ability_family",node["_familyGroupMask"])
    return {
        "main" : "检查此能力的类别（或称用途）",
        #"description" : "分为：常规攻击、阻挡攻击、技能、天赋、无特定类别；\"特性\"也是一种天赋或无特定类型能力",
        "true" : "其隶属于"+family,
        "false" : "其不隶属于"+family,
    }


# 检查角色技能状态
def CheckCharSkillAffecting(node,blackboard):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_checkTargetHost"]:
        return {
            "main" : f"检查{target_name}（角色类）的技能状态（若对方为召唤物，改为检查其主人）",
            "true" : "检查对象处于技能期间",
            "false" : "检查对象不处于技能期间"
        }
    else:
        return {
            "main" : f"检查{target_name}（角色类）的技能状态",
            "true" : "其处于技能期间",
            "false" : "其不处于技能期间"
        }
    
# 检查携带的技能（仅限角色类可用）
def CheckSkillIndex(node,blackboard):
    owner_name = anne_dictionary("target",node["_ownerType"])
    return {
        "main" : f"检查{owner_name}（角色类）携带的技能",
        "true" : f"{owner_name}携带的是{node['_skillIndex'] + 1}技能", # Index从0开始，技能序号从1开始
        "false" : f"{owner_name}携带的不是{node['_skillIndex'] + 1}技能或没有技能"
    }

# 检查技能触发类型
def CheckCharacterSkillType(node,blackboard):
    target_name = anne_dictionary("target",node["_targetType"])
    skill_type = anne_dictionary("skill_type",node["_skillType"])
    return {
        "main" : f"检查{target_name}（角色类）携带技能的触发类型",
        "true" : f"其为 {skill_type} 技能",
        "false" : f"其不为 {skill_type} 技能"
    }

# 检查技能持续类型（目前仅用作弹药类处理）
def CheckTargetSkillDurationType(node,blackboard):
    target_name = anne_dictionary("target",node["_targetType"])
    if len(node["_checkTypes"]) == 1 and node["_checkTypes"][0] == "AMMO":
        return {
            "main" : f"检查{target_name}（角色类）携带技能的持续类型",
            "true" : f"其为\"弹药类\"技能",
            "false" : f"其不为\"弹药类\"技能"
        }
    else:
        allow_types = [anne_dictionary("skill_duration_type",_type) for _type in node["_checkTypes"]]
        return {
            "main" : f"检查{target_name}（角色类）携带技能的持续类型",
            "true" : f"其隶属于 {'/'.join(allow_types)}",
            "false" : f"其不隶属于 {'/'.join(allow_types)}"
        }

# 检查上下文能力的当前目标数
def FilterAbilityValidCastTargetCnt(node,blackboard):
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    return {
        "main" : f"检查当前\"上下文\"能力的有效目标数量",
        "true" : f"目标数 {compare} [cnt]",
        "false" : f"目标数 {compare_not} [cnt]"
    }

# 检查能力结束的原因
def FilterByAbilityFinishReason(node,blackboard):
    target = "本Buff所隶属的能力" if node["_useBuffAbility"] else "当前\"上下文\"能力"
    reason = anne_dictionary("ability_finish_reason",node["_finishReason"])
    return {
        "main" : f"检查{target}的结束原因",
        "true" : f"能力因\"{reason}\"结束",
        "false" : f"未结束或能力不因\"{reason}\"结束"
    }

# 检查能力是否不受麻痹影响
def FilterByAbilityIgnorePalsyInterrupt(node,blackboard):
    if node["_skipUnitCheck"]:
        return {
            "main" : f"检查当前\"上下文\"能力是否被定义为\"无视麻痹\"",
            "description" : f"只考虑配置，不考虑单位是否可受麻痹影响",
            "true" : f"其不可\"无视麻痹\"" if node["_unset"] else f"其可\"无视麻痹\"",
            "false" : f"其可\"无视麻痹\"" if node["_unset"] else f"其不可\"无视麻痹\""
        }
    else:
        return {
            "main" : f"检查当前\"上下文\"能力是否能够\"无视麻痹\"",
            "true" : f"其不可\"无视麻痹\"且能力持有者为敌人类" if node["_unset"] else f"其可\"无视麻痹\"且能力持有者为敌人类",
            "false" : f"其可\"无视麻痹\"或能力持有者不为敌人类" if node["_unset"] else f"其不可\"无视麻痹\"或能力持有者不为敌人类"
        }