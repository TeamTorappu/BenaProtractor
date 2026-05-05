#----------------------------------------
# 治疗类Node
#----------------------------------------
from translator import anne_dictionary

# 固定数值治疗
def node_FixedValueHeal(node):
    source_name = anne_dictionary("target",node["_sourceType"])
    target_name = anne_dictionary("target",node["_targetType"])
    extra = ""
    if node["_ignoreHealFree"]:
        extra = "（无视禁疗）"
    return {"main" : f"让{source_name}治疗{target_name} {node['_healValueKey']} 点生命值{extra}"}

# 基于最大生命值的治疗
def node_HealViaMaxHpRatio(node):
    extra = ""
    if node["_ignoreHealFree"]:
        extra = "（无视禁疗）"
        if node["_skipModifierEvent"]:
            extra = "（无视禁疗；类生命\"流失\"）"
    elif node["_skipModifierEvent"]:
        extra = "（类生命\"流失\"）"

    result = {
        "main" : "",
        "description" : "治疗来源为Buff的来源；决定治疗量的生命值比例读取自黑板[hp_ratio]"
    }
    if node["_healTarget"] == "BUFF_SOURCE": # 这种情况下是否取目标的生命值已经不重要了
        result["main"] = f"来源恢复相当于其自身最大生命值一定比例的生命值{extra}"
    else:
        target_name = anne_dictionary("target",node["_healTarget"])
        if node["_getMaxHpFromTarget"]:
            result["main"] = f"{target_name}恢复相当于其自身最大生命值一定比例的生命值{extra}"
        else:
            result["main"] = f"{target_name}恢复相当于来源最大生命值一定比例的生命值{extra}"
    return result

# 基于伤害的治疗
def node_HealViaDamage(node):
    prefix = ""
    if node["_filterModifierCancelled"]:
        prefix = "若此次伤害未被取消，"
    if node["_healType"] == "FIXED":
        return {
            "main" : prefix + "治疗持有者 [value] × [heal_scale] 点生命值",
            "description" : "治疗来源为伤害的来源；若伤害为无来源则治疗变为无来源治疗"
        }
    elif node["_healType"] == "DAMAGE_SCALE":
        return {
            "main" : prefix + "治疗持有者 伤害值 × [heal_scale] 点生命值",
            "description" : "治疗来源为伤害的来源；若伤害为无来源则治疗变为无来源治疗"
        }