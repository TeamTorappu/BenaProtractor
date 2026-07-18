#----------------------------------------
# 元素损伤相关Node
#----------------------------------------
from translator import anne_dictionary

# 施加元素损伤
def node_ApplyElementDamage(node):
    source_name = anne_dictionary("target",node["_sourceType"])
    target_name = anne_dictionary("target",node["_targetType"])
    element_type = anne_dictionary("element",node["_elementDamageType"])
    scale = " × " + node["_epDamageScale"]
    result = {"main" : ""}
    descriptions = []
    if node["_loadElementTypeFromBb"]: # 读取黑板
        element_type = "黑板记述元素的"
    if node["_isEnvElementDamage"]:
        descriptions.append("环境元素损伤")
    if node["_isFixedEpDamage"]: # 固定值的损伤
        descriptions.append(f"无损伤计算时事件")
        if node["_fixedEpDamageScale"] != None and node["_fixedEpDamageScale"] != "": # 覆盖倍率黑板值
            scale = " × " + node["_fixedEpDamageScale"]
        else:
            scale = ""
        if node["_noSource"]:
            descriptions.append("视为无来源")
            if node["_fixedEpDamageKey"] != None and node["_fixedEpDamageKey"] != "":
                result["main"] = f"对{target_name}造成 [{node['_fixedEpDamageKey']}]{scale} 点{element_type}损伤"
                if node["_fixedEpDamage"] != 0:
                    result["main"] += f"（默认{node['_fixedEpDamage']}点）"
            else:
                result["main"] = f"对{target_name}造成 [{node['_fixedEpDamage']}]{scale} 点{element_type}损伤"
        else:
            if node["_fixedEpDamageKey"] != None and node["_fixedEpDamageKey"] != "":
                result["main"] = f"令{source_name}对{target_name}造成 [{node['_fixedEpDamageKey']}]{scale} 点{element_type}损伤"
                if node["_fixedEpDamage"] != 0:
                    result["main"] += f"（默认{node['_fixedEpDamage']}点）"
            else:
                result["main"] = f"令{source_name}对{target_name}造成 [{node['_fixedEpDamage']}]{scale} 点{element_type}损伤"
    else: 
        if node["_multiplyWithBuffValidStackCnt"] and node["_buffKey"] != None and node["_buffKey"] != "":
            scale += " × 层数"
            descriptions.append(f"层数指的是Buff来源持有的{node['_buffKey']}的叠加层数")
        if node["_baseOnHostAtk"] or node["_baseOnEnemyHostAtk"]: #这俩参数完全没区别，基于攻击力的损伤
            result["main"] = f"令{source_name}对{target_name}造成 攻击力{scale} 点{element_type}损伤"
            if node["_noSource"]:
                descriptions.append("视为无来源")
            if node["_forceUseProjectileCachedAtk"]:
                descriptions.append("强制使用来自弹道的缓存攻击力")
        else: # 貌似是基于伤害
            result["main"] = f"令{source_name}对{target_name}造成 本次伤害{scale} 点{element_type}损伤"
    # 返回结果
    if len(descriptions) > 0:
        result["description"] = "；".join(descriptions)
    return result

# 检查元素爆发类型
def node_FilterEPBreakRecoveryType(node):
    target_name = anne_dictionary("target",node["_target"])
    result = {}
    if node["_readTypeFromBb"] and node["_bbKey"] != "":
        result["main"] = f"检查{target_name}的元素爆发是否为黑板 [{node['_bbKey']}] 记述的类型"
        result["true"] = "若爆发的类型与黑板相同"
        result["false"] = "若爆发的类型与黑板不同"
    else:
        element = anne_dictionary("element",node["_recoveryType"])
        result["main"] = f"检查{target_name}的元素爆发是否{element}"
        result["true"] = f"若爆发类型为{element}"
        result["false"] = f"若爆发类型不为{element}"
    if node["_skipInEPBreakRecoveryCheck"]: # ON_BEFORE_EP_BREAK_START时点里使用，跳过“是否还在恢复”判断
        result["description"] = "兼容模式：若在元素爆发前则改为检查本次元素爆发类型"
    return result
    
# 检查目标元素值是否为全满/特定元素值是否为满
def node_CheckTargetEpIsFull(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_elementType"] != None and node["_elementType"] != "":
        element = anne_dictionary("element",node["_elementType"])
        return {
            "main" : f"检查{target_name}的{element}元素值",
            "true" : f"若其{element}元素值 ≥ 其元素上限且不处于\"爆条\"状态",
            "false" : f"若其{element}元素值 < 其元素上限或处于\"爆条\"状态"
        }
    else:
        return {
            "main" : f"检查{target_name}的所有类型的元素值",
            "true" : f"若其所有元素值均 ≥ 其元素上限且不处于\"爆条\"状态",
            "false" : f"若其任何一项元素值 < 其元素上限，或其处于\"爆条\"状态"
        }