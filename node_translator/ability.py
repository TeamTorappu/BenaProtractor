#----------------------------------------
# 能力类Node
#----------------------------------------
from .analyzer import anne_dictionary

# 触发某个能力
def node_TriggerAbility(node):
    # 未解析参数：_checkCanUseAblityFlag
    target_name = anne_dictionary("target",node["_targetType"])
    ability_name = node["_abilityName"]
    if node["_ownerType"] == node["_targetType"]:
        return {"main" :f"尝试让{target_name}触发{ability_name}能力"}
    else:
        owner_name = anne_dictionary("target",node["_ownerType"])
        return {"main" :f"尝试让{owner_name}向{target_name}触发{ability_name}能力"}

# 触发自动触发技能（无视触发条件）
def node_TriggerAutoSkill(node):
    target_name = anne_dictionary("target",node["_targetType"])
    return {"main" : f"尝试让{target_name}触发其自动触发的技能（无视其自动触发条件，其余技能条件不会无视）"}

# 中断角色类技能
def node_InterruptCharacterSkill(node):
    target_name = anne_dictionary("target",node["_charFrom"])
    features = []
    if node["_resetAbilityCooldownIgnoreAffecting"]: # 按yj的逻辑，两个都开的话其实是重置两次冷却，意义不明
        features.append("强制重置能力的内置冷却（即使目前仍在生效也重置）")
    elif node["_resetAbilityCooldown"]:
        features.append("重置能力的内置冷却")
    if node["_switchOutFromSkillState"]:
        features.append("强制从\"技能\"状态机切出")
    result = {"main" : f"中断{target_name}当前的技能"}
    if len(features) > 0:
        result["description"] = "；".join(features)
    return result

# 中断召唤物的技能
def node_InterruptTokenSkill(node):
    host_name = anne_dictionary("target",node["_hostType"])
    return {"main" : f"由{host_name}终止Buff持有者的技能（通常来说，持有者应该是{host_name}的召唤物）"}

# 中断能力
def node_InterruptAbility(node):
    # 未解析参数：_stopAffect
    owner_name = anne_dictionary("target",node["_ownerType"])
    if node["_useBlackboardCardUidAsOwner"]:
        owner_name = f"UID为[card_uid]的单位"
    ability = ""
    if node["_useCurrentAbility"]:
        ability = "当前的能力"
    elif node["_loadFromBlackboard"]:
        ability = f"名为 [ability_name] 的能力"
    elif node["_abilityName"] != "":
        ability = f"名为 {node['_abilityName']} 的能力"
    else:
        ability = f"？能力"

    if node["_emitAttackFinishOnly"]:
        return {"main" : f"终止{owner_name}{ability}，不视为终止，改为触发\"攻击结束时\"事件"}
    else:
        return {"main" : f"终止{owner_name}{ability}"}

# 能力的伤害可能致命时（蕾缪安2技能斩杀线逻辑）
def node_CheckAbilityDamageDeadly(node):
    source_name = anne_dictionary("target",node["_sourceType"])
    if node["_damageType"] != "PHYSICAL": # 如果填入的不是物理伤害——直接失败。这是给设计师的图灵测试？？？
        return {
            "main" : f"检查{source_name}当前的攻击力倍率与目标的状态，但配置存在问题",
            "true" : "始终不执行",
            "false" : "始终执行"
        }
    return {
        "main" : f"检查{source_name}当前能力的攻击力倍率与目标的状态",
        "true" : "若 攻击力 × 其攻击力倍率 ≥ 目标当前生命值 + 目标当前防御力",
        "false" : "若 攻击力 × 其攻击力倍率 < 目标当前生命值 + 目标当前防御力"
    }