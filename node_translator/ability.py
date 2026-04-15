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
        return {"main" :f"让{target_name}触发{ability_name}能力"}
    else:
        owner_name = anne_dictionary("target",node["_ownerType"])
        return {"main" :f"让{owner_name}向{target_name}触发{ability_name}能力"}

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