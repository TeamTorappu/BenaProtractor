#----------------------------------------
# 效果类Node（或者叫未分类更好）
#----------------------------------------
from .analyzer import anne_dictionary, analyze_damage

# 造成无来源伤害
def node_NoSourceDamage(node):
    damage_name = analyze_damage(node,"无来源的") # 直接把整个node传参进去
    return {"main" : "对持有者造成X点"+damage_name}
    
# 造成伤害
def node_AdvancedApplyDamage(node):
    # 未解析参数：_modifierKey _emitSourceOnCalculateDamage
    source_name = anne_dictionary("target",node["_sourceType"])
    target_name = anne_dictionary("target",node["_targetType"])
    damage_name = analyze_damage(node) # 直接把整个node传参进去
    default_atk_scale = to_percent(node["_defaultAtkScale"])
    return {
        "main" : f"让{source_name}对{target_name}造成{str(default_atk_scale)}{damage_name}",
        "description" : f"会读取黑板中的{node['_atkScaleVar']}作为攻击力倍率使用"
    }
    
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

# 格挡/护盾/屏障（还得具体情况具体分析）
def node_BlockDamage(node):
    # 未解析参数：_useSource _sourceType
    #source_name = anne_dictionary("target",node["_sourceType"])
    name = "处理概率格挡/计次护盾效果"
    features = []
    # 使用动态值，说明是屏障
    if node["_useDynamicVar"]:
        name = "处理屏障效果"
        if node["_allowNegativeDynamicVar"]:
            features.append("允许负屏障值")
        if node["_showShieldUI"]:
            features.append("在血条上显示屏障值")
    elif node["_useFixedValue"]: # 使用定值，说明是林式阈值盾
        name = "处理干员林的阈值格挡效果"
    if node["_showDamageNumber"]:
        features.append("即使成功格挡也显示伤害数值")
    if node["_specifyBlockEffect"] != None:
        features.append("使用格挡特效"+node["_specifyBlockEffect"])
    # 检查伤害的施加方式
    if node["_filterApplyWay"]:
        if node["_applyWayFilter"] == "NONE": # 仅无类型
            features.append("仅格挡施加方式为“无”的伤害")
        elif node["_applyWayFilter"] == "MELEE": # 无类型与近战
            features.append("仅格挡施加方式为“近战”或“无”的伤害")
        elif node["_applyWayFilter"] == "RANGED": # 无类型与远程
            features.append("仅格挡施加方式为“远程”或“无”的伤害")
        #elif node["_applyWayFilter"] == "ALL": # 全部都可以就不用写了
    if len(features) > 0:
        return {"main" : name + "（"+",".join(features)+"）"}
    else:
        return {"main" : name}

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

# 结束特定Buff(s)
def node_FinishBuffsById(node):
    # 未解析参数：_updateOverrideMap _finishHostBuff
    target_name = anne_dictionary("target",node["_targetType"])
    buff_name = "特定Buff（取决于黑板）" if node["_loadFromBlackboard"] else node["_buffKey"]
    # 仅限某人的buff
    if node["_checkBuffSource"]:
        source_name = anne_dictionary("target",node["_sourceType"])
        if node["_alsoClearNullSource"]:
            buff_name = "来源于" + source_name + "或无来源的" + buff_name
        else:
            buff_name = "来源于" + source_name + "的" + buff_name
    action = f"结束"
    if node["_decCntIfStack"]:
        if node["_decCntKey"] != None:
            action = f"减少黑板{node['_decCntKey']}值层叠层（变为0层时该Buff结束）"
        else:
            action += f"减少{node['_decCnt']}层叠层（变为0层时该Buff结束）"
    return {"main" : f"令{target_name}身上的{buff_name}{action}"}

# “分摊伤害”，实际上是给予其他单位当前伤害的一部分。
def node_DamageSplit(node):
    target_name = anne_dictionary("target",node["_targetType"])
    attack_type = anne_dictionary("attack_type",node["_attackType"])
    return {"main" : f"将本次伤害的X%以同类型{attack_type}伤害的形式传递给{target_name}（原伤害不会变化）"}

# 伤害倍率
def node_DamageScale(node):
    # 未解析参数：_customKey _isValidStackCnt
    damage_scale = ""
    action = "提升"
    # 需要把减伤值改为*(1-X)
    if node["_isOneMinus"]:
        damage_scale = "(1-X)"
        action = "降低"
    else:
        damage_scale = "(1+X)"
    # 根据Buff层数加倍
    if node["_isStackable"]:
        damage_scale = f"({damage_scale}×Buff层数)"
    text = f"令本次伤害{action}至{damage_scale}倍"
    # 检查伤害类型与施加方式
    conditions = []
    if node["_filterDamageType"]:
        conditions.append("伤害类型为"+anne_dictionary("damage_type",node["_damageMask"]))
    if node["_filterApplyWay"]:
        if node["_applyWayFilter"] == "NONE":
            conditions.append("施加方式为无类型施加")
        elif node["_applyWayFilter"] == "MELEE":
            conditions.append("施加方式为近战")
        elif node["_applyWayFilter"] == "RANGED":
            conditions.append("施加方式为远程")
    
    if len(conditions) > 0:
        text = f"若{'且'.join(conditions)}，{text}"
    # 差值记录，一般是拿来算“减少部分的伤害”的
    if node["_cachedDeltaValueToBBKey"]:
        text += "，并将减少/增加的部分记在黑板上"
    return {"main" : text}

# 播放音效
def node_PlayAudio(node):
    target_name = anne_dictionary("target",node["_target"])
    return {"main" : f"让{target_name}播放音效 {node['_audioSignal']}"}
    
# 创建特效
def node_CreateEffect(node):
    return {"main" : "创建特效（暂不翻译）"}