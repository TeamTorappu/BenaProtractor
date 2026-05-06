#----------------------------------------
# 效果类Node（或者叫未分类更好）
#----------------------------------------
from translator import anne_dictionary
from .analyzer import analyze_damage, to_percent

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
    if node["_spString"] != None and node["_spString"] != "":
        amount = "["+node['_spString']+"]点"
        if node["_modifyValue"] != 0:
            descriptions.append(f"默认{modify_type}{node['_modifyValue']}点")

    if node["_modifyByRatio"]:
        amount = to_percent(node["_modifyRatio"]) if node["_spString"] == "" else "["+node['_spString']+"]%"
        if node["_modifyByRatioBasedOnCurSP"]: #按当前技力
            modify_type = "增加当前技力的"
        else: #按技力消耗量
            modify_type = "增加技力消耗量的"
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

# 增减占用阻挡数
def node_AddEnemyBlockVolume(node):
    target_name = anne_dictionary("target",node["_targetType"])
    addon = node["_additionVolume"] * (-1 if node["_isMinus"] else 1)
    return {"main" : f"让{target_name}（敌人类）的占用阻挡数{addon}"}



# 调整本buff提供的属性增益
def node_AttributeModifierWithBB(node):
    # 未解析参数：_targetType
    #target_name = anne_dictionary("target",node["_targetType"])
    attribute_type = anne_dictionary("attribute",node["_attributeType"])
    #formula_type = anne_dictionary("formula",node["_formulaType"])
    if node["_valueKey"] != None and node["_valueKey"] not in ["","none"]:
        if node["_formulaType"] == "FINAL_SCALER":
            return {"main" : f"调整本Buff提供的{attribute_type}加成：+[{node['_valueKey']}]%(终乘)"}
        elif node["_formulaType"] == "MULTIPLIER":
            return {"main" : f"调整本Buff提供的{attribute_type}加成：+[{node['_valueKey']}]%(直乘)"}
        elif node["_formulaType"] == "ADDITION":
            return {"main" : f"调整本Buff提供的{attribute_type}加成：+[{node['_valueKey']}](直加)"}
        elif node["_formulaType"] == "FINAL_ADDITION":
            return {"main" : f"调整本Buff提供的{attribute_type}加成：+[{node['_valueKey']}](终加)"}
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
        action = f"切换至{node['_modeIndex']}号模式"
    return {"main" : f"令{target_name}{action}"}

# 强制击倒
def node_InstantKill(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_killSource"]: # 改为击杀上下文中的来源
        target_name = "上下文来源"
    features = []
    result = {"main" : "强制击倒"+target_name}
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
    
# 修改阻挡模式
def node_ChangeCharBlockMode(node):
    target_name = anne_dictionary("target",node["_target"])
    if node["_resetToDefault"]:
        return {"main" : f"令{target_name}的阻挡模式切换回初始模式（可能是\"地面阻挡\"）"}
    block_mode = anne_dictionary("block_mode",node["_blockMode"])
    return {"main" : f"令{target_name}的阻挡模式切换为{block_mode}"}

# 记录战斗LOG（通常用于记录模组任务、藏品掉落、跨关卡生命比例继承等数据）
def node_LogExtraBattleInfo(node):
    target_name = anne_dictionary("target",node["_target"])
    if node["_countInHostIfToken"]:
        target_name += "（若为召唤物，改为其主人）"
    key = "[key]" if node["_loadKeyFromBlackBoard"] else node["_key"]
    log_str = ""
    log_info = ""
    addon = f"[{node['_additionValueKey']}]" if (node["_additionValueKey"] != None and node["_additionValueKey"] != "") else node["_additionValue"]
    if node["_logType"] == "SIMPLE": # 普通记录
        log_str = f"SIMPLE,(ID),{key}"
        log_info = f"记录特定ID的单位的数值（以 单位的ID + {key} 为键）"
    elif node["_logType"] == "DETAILED": # 完整记录
        log_str = f"DETAILED,(ID),(UID),{key}"
        log_info = f"记录一个特定UID的单位的数值（以 单位的ID + 战内UID + {key} 为键）"
    elif node["_logType"] == "ATTRIBUTE": # 记录数值
        if node["_attributeType"] == "HP_RATIO":
            log_str = "ATTRIBUTE,(ID),(UID),HP_RATIO,(生命比例)"
            log_info = f"存储单位此时的生命值比例（保留到小数点后四位）"
        elif node["_attributeType"] == "SP":
            log_str = "ATTRIBUTE,(ID),(UID),SP,(技力)"
            log_info = f"存储单位此时的技力"
        elif node["_attributeType"] == "COST":
            log_str = "ATTRIBUTE,(ID),(UID),COST,(部署费用)"
            log_info = f"存储当前关卡持有的部署费用"
        else:
            log_str = "ATTRIBUTE,(ID),(UID),NONE,0"
            log_info = f"存储该单位存在过的痕迹"
    elif node["_logType"] == "CHARACTER_SKILL": # 记录技能开启次数
        log_str = "CHARACTER_SKILL,(ID),(UID)"
        log_info = f"记录该单位（角色类）使用技能的次数（次数+{addon}）"
    elif node["_logType"] == "HIDDEN_WAVE_START" or node["_logType"] == "HIDDEN_WAVE_END": # 隐藏波次
        log_str = f"{node['_logType']},(单位配置的hiddenGroupKey)"
        if node["_logType"] == "HIDDEN_WAVE_START":
            log_info = f"记录该单位（敌人类）的隐藏组已出现"
        elif node["_logType"] == "HIDDEN_WAVE_END":
            log_info = f"记录该单位（敌人类）的隐藏组已结束"
    else: # 剩下的
        log_str = f"{node['_logType']},{key}"
        log_info = f"存储一个全局性的数值（以 {key} 为键）"
    return {
        "main" : f"记录战斗LOG：{log_info}",
        "description" : f" \"{log_str}\" += {addon} ",
        "style_closed" : True
    }

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

# 创建“BOSS倒计时”UI特效（无实际作用）
def node_SetBossCountDown(node):
    if node["_cdBBKey"] != None and node["_cdBBKey"] != "":
        return {"main" : f"在UI层上创建一个 [{node['_cdBBKey']}] 秒的关卡倒计时提示（无实际作用）"}
    return {"main" : f"在UI层上创建一个{node['_cdValue']}秒的关卡倒计时提示（无实际作用）"}