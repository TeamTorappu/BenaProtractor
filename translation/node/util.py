#----------------------------------------
# 效果类Node（或者叫未分类更好）
#----------------------------------------
from .analyzer import anne_dictionary, analyze_damage, to_percent
    
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

# 中断召唤物的技能
def node_InterruptTokenSkill(node):
    host_name = anne_dictionary("target",node["_hostType"])
    return {"main" : f"由{host_name}终止Buff持有者的技能（通常来说，持有者应该是{host_name}的召唤物）"}

# 补充召唤物数量
def node_RechargeToken(node):
    # 未解析参数：_rechargeTiming
    if node["_refreshRemainingCnt"]:
        return {"main" : "将Buff持有者的召唤物数量恢复至默认值"}
    else:
        return {"main" : f"根据黑板上 {node['_cntKey']} 的数值，为Buff持有者补充召唤物（不会超过上限）"}

# 临时提升攻击力倍率
def node_AtkScaleUp(node):
    conditions = []
    result = {
        "main" : f"攻击力倍率乘以{node['_defaultValue']}倍",
        "description" : f"会读取黑板中的{node['_atkScaleKey']}作为乘数"
    }
    # 筛选目标的攻击方式
    if node["_filterApplyWay"]:
        if node["_applyWay"] == "NONE" and node["_filterNoneApplyWay"]:
            conditions.append("目标攻击方式为\"不攻击\"或未标注攻击方式") # 存疑
        elif node["_applyWay"] == "NONE":
            conditions.append("目标攻击方式为\"不攻击\"")
        elif node["_applyWay"] == "MELEE":
            conditions.append("目标攻击方式为\"近战\"")
        elif node["_applyWay"] == "RANGED":
            conditions.append("目标攻击方式为\"远程\"")
    # 筛选弹道Key
    if node["_filterProjectileKey"] != "":
        conditions.append(f"伤害来自{node['_filterProjectileKey']}弹道")
    # 写入条件
    if len(conditions) > 0:
        result["main"] = "若"+"且".join(conditions)+"，"+result["main"]
    # 乘后若攻击倍率为0时，取消本次伤害
    if node["_cancelIfAtkScaleZero"]:
        result["description"] += "；若乘算后本次伤害的攻击力倍率为0，则取消此次伤害"
    return result

# 修改技力
def node_ModifySp(node):
    # 未解析参数：_spString
    target_name = anne_dictionary("target",node["_targetType"])
    modify_type = "减少" if node["_isMinis"] else "增加"
    amount = str(node["_modifyValue"])+"点"
    if node["_modifyByRatio"]:
        amount = to_percent(node["_modifyRatio"])
        if node["_modifyByRatioBasedOnCurSP"]: #按当前技力
            modify_type = "当前技力的"+amount
        else: #按技力消耗量
            modify_type = "技力消耗量的"+amount
    descriptions = []
    result = {}
    if node["_forceFlag"]:
        modify_type = "强制"+modify_type
    if node["_spString"] != "":
        descriptions.append(f"会读取黑板的{node['_spString']}作为技力{modify_type}量")
    if node["_customModifierKey"] != "":
        descriptions.append(f"此次回复带有标签\"{node['_customModifierKey']}\"")
    # 修改技力
    if node["_dontCheckSpType"] or node["_spMask"] == "ALL":
        result["main"] = f"令{target_name}的技力{modify_type}{amount}"
    else:
        sp_type = anne_dictionary("sp_type",node["_spMask"])
    if len(descriptions) > 0:
        result["description"] = ";".join(descriptions)
    return result

# 调整本buff提供的属性增益
def node_AttributeModifierWithBB(node):
    # 未解析参数：_targetType
    #target_name = anne_dictionary("target",node["_targetType"])
    attribute_type = anne_dictionary("attribute",node["_attributeType"])
    #formula_type = anne_dictionary("formula",node["_formulaType"])
    if node["_valueKey"] != None and node["_valueKey"] not in ["","none"]:
        if node["_formulaType"] == "FINAL_SCALER":
            return {"main" : f"调整本Buff提供的{attribute_type}加成：+{node['_valueKey']}%(终乘)"}
        elif node["_formulaType"] == "MULTIPLIER":
            return {"main" : f"调整本Buff提供的{attribute_type}加成：+{node['_valueKey']}%(直乘)"}
        elif node["_formulaType"] == "ADDITION":
            return {"main" : f"调整本Buff提供的{attribute_type}加成：+{node['_valueKey']}(直加)"}
        elif node["_formulaType"] == "FINAL_ADDITION":
            return {"main" : f"调整本Buff提供的{attribute_type}加成：+{node['_valueKey']}(终加)"}
    return {"main" : f"清除本Buff提供的{attribute_type}加成"}

# 切换模式
def node_SwitchMode(node):
    # 未解析参数：_restartFSM
    target_name = anne_dictionary("target",node["_targetType"])
    action = ""
    if node["_restoreDefault"]:
        action = "切换回默认模式"
    elif node["_loadModeFromBlackboard"]:
        action = "切换至第X号模式"
    else:
        action = f"切换至第{node['_modeIndex']}号模式"
    return {"main" : f"令{target_name}{action}"}

# 播放音效
def node_PlayAudio(node):
    target_name = anne_dictionary("target",node["_target"])
    return {"main" : f"让{target_name}播放音效 {node['_audioSignal']}"}
    
# 创建特效
def node_CreateEffect(node):
    # 暂不详细翻译
    target_name = anne_dictionary("target",node["_targetType"])
    effect_id = node["_effectKey"]
    return {"main" : f"为{target_name}创建特效{effect_id}（暂不翻译）"}