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
        return {"main" : f"根据黑板上 [{node['_cntKey']}] 的数值，为Buff持有者补充召唤物（不会超过上限）"}

# 临时提升攻击力倍率
def node_AtkScaleUp(node):
    conditions = []
    result = {
        "main" : ""
    }
    if node["_atkScaleKey"] != None and node["_atkScaleKey"] != "":
        result["main"] = f"令攻击力倍率提升至[{node['_atkScaleKey']}]倍"
        if node["_defaultValue"] != 1:
            result["main"] += f"（默认提升至{node['_defaultValue']}倍）"
    else:
        result["main"] = f"令攻击力倍率提升至{node['_defaultValue']}倍"
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
        conditions.append(f"伤害来自[{node['_filterProjectileKey']}]弹道")
    # 写入条件
    if len(conditions) > 0:
        result["main"] = "若"+"且".join(conditions)+"，"+result["main"]
    # 乘后若攻击倍率为0时，取消本次伤害
    if node["_cancelIfAtkScaleZero"]:
        if "description" not in result:
            result["description"] = "若乘算后本次伤害的攻击力倍率为0，则取消此次伤害"
        else:
            result["description"] += "；若乘算后本次伤害的攻击力倍率为0，则取消此次伤害"
    return result

# 修改技力
def node_ModifySp(node):
    # 未解析参数：_spString
    target_name = anne_dictionary("target",node["_targetType"])
    modify_type = "减少" if node["_isMinis"] else "增加"
    amount = str(node["_modifyValue"])+"点"
    result = {"main" : ""}
    descriptions = []
    if node["_spString"] != "":
        amount = "["+node['_spString']+"]点"
        if node["_modifyValue"] != 0:
            descriptions.append(f"默认{modify_type}{node['_modifyValue']}点")
    if node["_modifyByRatio"]:
        amount = to_percent(node["_modifyRatio"])
        if node["_modifyByRatioBasedOnCurSP"]: #按当前技力
            modify_type = "当前技力的"+amount
        else: #按技力消耗量
            modify_type = "技力消耗量的"+amount
    # 额外内容
    if node["_forceFlag"]:
        modify_type = "强制"+modify_type
    if node["_customModifierKey"] != "":
        descriptions.append(f"此次回复带有标签\"{node['_customModifierKey']}\"")
    result["main"] = f"令{target_name}的技力{modify_type}{amount}"
    # 修改技力
    if not node["_dontCheckSpType"] and node["_spMask"] != "ALL":
        sp_type = anne_dictionary("sp_type",node["_spMask"])
        result["main"] = f"若{target_name}技力类型为 {sp_type} ，令其技力{modify_type}{amount}"
    if len(descriptions) > 0:
        result["description"] = "；".join(descriptions)
    return result
    
# 修改费用
def node_ModifyCost(node):
    source_name = anne_dictionary("target",node["_sourceType"])
    shared_flags = []
    if node["_forceToDisplayNumber"]: # 强制显示正数？
        shared_flags.append(anne_dictionary("shared_flag","FORCE_TO_DISPLAY_NUMBER"))
    if node["_forceToDisplayNegativeNumber"]: # 强制显示负数？
        shared_flags.append(anne_dictionary("shared_flag","FORCE_TO_DISPLAY_NEGATIVE_NUMER"))
    if len(shared_flags) > 0:
        return {
            "main" : f"令持有的部署费用+{node['_blackboardKey']}",
            "description" : "、".join(shared_flags)
        }
    else:
        return {"main" : f"令持有的部署费用+{node['_blackboardKey']}"}

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
                result["main"] = f"对{target_name}造成 {node['_fixedEpDamageKey']}{scale} 点{element_type}损伤"
                if node["_fixedEpDamage"] != 0:
                    result["main"] += f"（默认{node['_fixedEpDamage']}点）"
            else:
                result["main"] = f"对{target_name}造成 {node['_fixedEpDamage']}{scale} 点{element_type}损伤"
        else:
            if node["_fixedEpDamageKey"] != None and node["_fixedEpDamageKey"] != "":
                result["main"] = f"令{source_name}对{target_name}造成 {node['_fixedEpDamageKey']}{scale} 点{element_type}损伤"
                if node["_fixedEpDamage"] != 0:
                    result["main"] += f"（默认{node['_fixedEpDamage']}点）"
            else:
                result["main"] = f"令{source_name}对{target_name}造成 {node['_fixedEpDamage']}{scale} 点{element_type}损伤"
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
        action = "切换至特定编号的模式，编号由黑板值 [mode] 决定"
    else:
        action = f"切换至第{node['_modeIndex']}号模式"
    return {"main" : f"令{target_name}{action}"}

# 强制击倒
def node_InstantKill(node):
    target = "Buff来源" if node["_killSource"] else "Buff持有者"
    features = []
    result = {"main" : "强制击倒"+target}
    if node["_skipReborn"]: # 无视二阶段
        features.append("无视重生能力")
    if node["_noSource"]: # 无视击杀来源
        features.append("视为无击杀源")
    if node["_noReason"]: # 无原因
        features.append("视为无原因")
    elif node["_markReachExit"]: # 视为抵达路径终点
        features.append("视为抵达路径终点")
    if not node["_switchState"]: # 正常情况下是要切换至死亡状态机播放死亡动画的
        features.append("无动画/状态机")
    # 战术点相关适配
    if node["_withdrawIfRallyPoint"]:
        features.append("若为战术点，改为执行撤退")
        if not node["_resultIfInRallyPointMode"]: # 不开这个参数的情况下，如果目标处于战术点状态，节点处理失败
            result["true"] = "若目标不为战术点或未处于战术点形态"
            result["false"] = "若目标已处于战术点形态"
    # 返回
    if len(features) > 0:
        result["description"] = "；".join(features)
    return result

# 撤退/强制撤退
def node_Withdraw(node):
    # 未解析参数：_needLog
    target = "Buff来源" if node["_withdrawSource"] else "Buff持有者"
    result = {"main" : "撤退"+target}
    if node["_force"]:
        result["main"] = "强制"+result["main"]
    if node["_switchToDeadState"]: # 史尔特尔的伪击倒
        result["main"] += "，但令其进入\"死亡\"状态机（会播放被击倒的动画）"
    return result

# 清空技力（减少等同于当前技力值的技力）
def node_ClearCharacterSp(node):
    target_name = anne_dictionary("target",node["_charFrom"])
    if node["_forceFlag"]:
        return {"main" : f"令{target_name}清空技力（强制流失等同于当前技力值的技力）"}
    else:
        return {"main" : f"令{target_name}清空技力（减少等同于当前技力值的技力，受阻回影响）"}

# 修改目标生命值
def node_ModifyLifePoint(node):
    source_name = anne_dictionary("target",node["_sourceType"])
    value = " - ["+node["_blackboardKey"]+"]" if node["_isSub"] else " + ["+node["_blackboardKey"]+"]"
    if node["_isReachExit"]:
        return {"main" : f"令关卡目标生命值{value}，视为由{source_name}\"抵达路径终点\"导致的修改"}
    elif node["_sourceType"] != "BUFF_OWNER":
        return {"main" : f"令关卡目标生命值{value}，视为由{source_name}导致的修改"}
    else:
        return {"main" : f"令关卡目标生命值{value}"}

# 播放音效
def node_PlayAudio(node):
    target_name = anne_dictionary("target",node["_target"])
    return {"main" : f"让{target_name}播放音效 {node['_audioSignal']}"}
    
# 创建特效
def node_CreateEffect(node):
    # 暂不详细翻译
    target_name = anne_dictionary("target",node["_targetType"])
    effect_id = node["_effectKey"]
    return {"main" : f"为{target_name}创建特效 {effect_id}（暂不翻译）"}