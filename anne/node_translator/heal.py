#----------------------------------------
# 治疗类Node
#----------------------------------------
from analyzer import to_percent
from dictionary import anne_dictionary

# 固定数值治疗
def FixedValueHeal(node,blackboard):
    source_name = anne_dictionary("target",node["_sourceType"])
    target_name = anne_dictionary("target",node["_targetType"])
    extra = ""
    if node["_ignoreHealFree"]:
        extra = "（无视禁疗）"
    if node["_healValueKey"] in blackboard:
        return {"main" : f"让{source_name}治疗{target_name} {blackboard[node['_healValueKey']]} 点生命值{extra}"}
    return {"main" : f"让{source_name}治疗{target_name} {node['_healValueKey']} 点生命值{extra}"}

# 基于最大生命值的治疗
def HealViaMaxHpRatio(node,blackboard):
    extra = ""
    if node["_ignoreHealFree"]:
        extra = "（无视禁疗）"
        if node["_skipModifierEvent"]:
            extra = "（无视禁疗；生命复原）"
    elif node["_skipModifierEvent"]:
        extra = "（生命复原）"

    result = {
        "main" : "",
        "description" : "治疗来源为Buff的来源"
    }
    if node["_healTarget"] == "BUFF_SOURCE": # 这种情况下是否取目标的生命值已经不重要了
        result["main"] = f"Buff来源恢复相当于自身最大生命值一定比例的生命值{extra}"
    else:
        target_name = anne_dictionary("target",node["_healTarget"])
        heal_scale = to_percent(blackboard["hp_ratio"]) if "hp_ratio" in blackboard else "[hp_ratio]"
        if node["_getMaxHpFromTarget"]: # 开了这个时以自己的最大生命值为准（怎么和参数名字反的）
            result["main"] = f"{target_name}恢复 Buff来源最大生命值 × {heal_scale} 的生命值{extra}"
        else:
            result["main"] = f"{target_name}恢复相当于 其最大生命值 × {heal_scale} 的生命值{extra}"
    return result

# 基于伤害的治疗
def HealViaDamage(node,blackboard):
    prefix = ""
    if node["_filterModifierCancelled"]:
        prefix = "若此次伤害未被取消，"
    result = {
        "main" : prefix + "治疗持有者 ",
        "description" : "治疗来源为伤害的来源；若伤害为无来源则治疗变为无来源治疗"
    }
    if node["_healType"] == "FIXED":
        if "value" in blackboard and "heal_scale" in blackboard:
            heal_value = blackboard["value"] * blackboard["heal_scale"]
            result["main"] += f"{heal_value} 点生命值"
        elif "value" in blackboard:
            result["main"] += f"{blackboard['value']} × [heal_scale] 点生命值"
        elif "heal_scale" in blackboard:
            heal_scale = to_percent(blackboard["heal_scale"]) 
            result["main"] += f"[value] × {heal_scale} 点生命值"
        else:
            result["main"] += "[value] × [heal_scale] 点生命值"
    elif node["_healType"] == "DAMAGE_SCALE":
        if "heal_scale" in blackboard:
            heal_scale = to_percent(blackboard["heal_scale"]) 
            result["main"] += f"伤害值 × {heal_scale} 的生命值"
        else:
            result["main"] += "伤害值 × [heal_scale] 的生命值"
    return result