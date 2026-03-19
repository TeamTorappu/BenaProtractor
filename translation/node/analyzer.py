import json
import os

ANNE_DICTIONARY = None
# 继承字典数据
def set_dictionary(dictionary):
    ANNE_DICTIONARY = dictionary
        
# 安妮的查字典方法
# 如果查不到会返回原文
def anne_dictionary(catalogue,type_str):
    return ANNE_DICTIONARY[catalogue].get(type_str,type_str)

#----------------------------------------
# 数值文本化逻辑
#----------------------------------------
# 将数值加成改成+/-X的格式，如果结尾是.0还会自动删去
def to_delta(addition_value):
    # 去无意义小数
    if abs(addition_value - round(addition_value)) < GAP: 
        addition_value = round(addition_value)
    # 检查正负
    if addition_value < 0:
        return str(addition_value) # 负数本来就有符号
    else:
        return "+"+str(addition_value)

# 将数值加成改成X%格式，如果结尾是.0还会自动删去
# 可以要求提供正负符号，当然负数本来就有符号。
def to_percent(power_value,negative_need_plus_one=False):
    percent_value = power_value * 100
    # 如果为负则加一的可选项
    if negative_need_plus_one and percent_value < 0:
        percent_value += 100
    # 去无意义小数
    if abs(percent_value - round(percent_value)) < GAP: 
        percent_value = round(percent_value)
    # 检查正负（外部应该会自己加上符号，因此负数要打个括号）
    if percent_value < 0:
        return "("+str(percent_value)+")%"
    else:
        return str(percent_value)+"%"

# 将数值加成改成+/-X%格式，如果结尾是.0还会自动删去
# 可以要求提供正负符号，当然负数本来就有符号。
def to_delta_percent(power_value):
    percent_value = power_value * 100
    # 去无意义小数
    if abs(percent_value - round(percent_value)) < GAP: 
        percent_value = round(percent_value)
    # 检查正负
    if percent_value < 0:
        return str(percent_value)+"%" # 负数本来就有符号
    else:
        return "+"+str(percent_value)+"%"

#----------------------------------------
# 解析逻辑
#----------------------------------------
# 解析伤害类的详细信息
# 返回字符串
def analyze_damage(damage_data,prefix="",suffix=""):
    features = []
    # 伤害类型
    damage_type = damage_data["_damageType"]
    damage_type_name = anne_dictionary("damage_type",damage_type)
    # 攻击类型
    attack_type = "NONE"
    if "_attackType" in damage_data:
        attack_type = damage_data["_attackType"]
    attack_type_name = anne_dictionary("attack_type",attack_type)
    # 来源处理
    if "_noSource" in damage_data and damage_data["_noSource"]:
        prefix += "无来源的"
    elif "_onlyUseSourceOnCalculateDamage" in damage_data and damage_data["_onlyUseSourceOnCalculateDamage"]:
        features.append("仅在计算伤害时使用来源处理")
    # 特征处理
    if "_ignoreForSp" in damage_data and damage_data["_ignoreForSp"]:
        features.append("不触发受击回复")
    if "_forceUseProjectileCachedAtk" in damage_data and damage_data["_forceUseProjectileCachedAtk"]:
        features.append("强制使用弹道的缓存攻击力")
    elif "_getCachedAtkFromBlackboard" in damage_data and damage_data["_getCachedAtkFromBlackboard"]:
        if "_cachedAtkKey" in damage_data:
            features.append(f"使用黑板中({damage_data['_cachedAtkKey']})作为缓存攻击力")
    # 各种SharedFlags处理（两种写法都有，因此两种写法都判断一遍）
    if "_skipModifierEvent" in damage_data and damage_data["_skipModifierEvent"]:
        features.append("类生命流失(无计算/事件)")
    if "_isEnvDamage" in damage_data and damage_data["_isEnvDamage"]:
        features.append("环境伤害")
    if "_isUndeadable" in damage_data and damage_data["_isUndeadable"]:
        features.append("不会致命")
    if "_isUndeadable" in damage_data and damage_data["_instantKillLikeDamage"]:
        features.append("类斩杀伤害")
    if "_isNotChangeableValue" in damage_data and damage_data["_isNotChangeableValue"]:
        features.append("无法被其他方式增/减/免伤")
    if "_setSharedFlag" in damage_data and damage_data["_setSharedFlag"]:
        if "_sharedFlagIndex" in damage_data:
            shared_flag_name = anne_dictionary("sharedflag",damage_data["_sharedFlagIndex"])
            if shared_flag_name not in features:
                features.append(shared_flag_name)
    # 疑似是火陈的小巧思，限定伤害类型的无视闪避
    if "_ignoreMissFlag" in damage_data and damage_data["_ignoreMissFlag"] != "NONE":
        features.append("无视"+anne_dictionary("damage_type",damage_data["_ignoreMissFlag"])+"闪避")
    # 乘以黑板值
    if "_multiplierByKey" in damage_data and damage_data["_multiplierByKey"]:
        if "_multiplierKey" in damage_data and damage_data["_multiplierKey"]:
            features.append("乘以黑板值"+damage_data["_multiplierKey"])
    # 无视闪避/格挡那些的掩码，不过yj只用几个特定掩码，所以没必要做掩码解析
    if "_ignoreCancelReasonMask" in damage_data and damage_data["_ignoreCancelReasonMask"] != "NONE":
        features.append("无视"+anne_dictionary("cancel_reason",damage_data["_ignoreCancelReasonMask"]))
    if len(features) > 0:
        suffix += "（"+";".join(features)+"）"
    return prefix+damage_type_name+attack_type_name+"伤害"+suffix
    
# 统一解析Buff的详细信息
# 返回结构体
def analyze_buff(buff_data):
    buff_key = buff_data["buffKey"]
    # 读取自数据库，一般是眩晕、寒冷那些，不管他
    if buff_data["loadFromDB"]:
        return {"main" : buff_key+"(读取自数据库)"}
    # 开始解析
    results = []
    blackboard = {}
    has_resistable_flag = False
    
    # 检查模板
    if buff_data["templateKey"] != "empty" :
        results.append(f"使用{buff_data['templateKey']}模板")
    # 检查黑板
    if buff_data["blackboard"] and len(buff_data["blackboard"]) > 0:
        for bb_data in buff_data["blackboard"]:
            bb_key = bb_data["key"]
            if bb_data["value"]:
                blackboard[bb_key] = bb_data["value"]
            elif bb_data["valueStr"]:
                blackboard[bb_key] = bb_data["valueStr"]
        
    # 异常效果家族与属性增减
    attrs = buff_data["attributes"]
    features = []
    # 以下内容yj都写过[]和null的格式，泥岩的recharge居然同时两种都用，绝了
    # 异常效果
    if attrs["abnormalFlags"] != None and len(attrs["abnormalFlags"]) > 0:
        for flag in attrs["abnormalFlags"]:
            flag_name = anne_dictionary("abnormal",flag)
            features.append(flag_name)
            # 包含可抵抗状态
            if flag in ["STUNNED","COLD","FROZEN"]:
                has_resistable_flag = True
    # 异常免疫
    if attrs["abnormalImmunes"] != None and len(attrs["abnormalImmunes"]) > 0:
        for flag in attrs["abnormalImmunes"]:
            flag_name = anne_dictionary("abnormal",flag)
            features.append(flag_name+"免疫")
    # 异常反制
    if attrs["abnormalAntis"] != None and len(attrs["abnormalAntis"]) > 0:
        for flag in attrs["abnormalAntis"]:
            flag_name = anne_dictionary("abnormal",flag)
            features.append(flag_name+"反制")
    # 异常组合
    if attrs["abnormalCombos"] != None and len(attrs["abnormalCombos"]) > 0:
        for combo in attrs["abnormalCombos"]:
            combo_name = anne_dictionary("abnormal",combo)
            features.append(combo_name)
    # 异常组合免疫
    if attrs["abnormalComboImmunes"] != None and len(attrs["abnormalComboImmunes"]) > 0:
        for combo in attrs["abnormalComboImmunes"]:
            combo_name = anne_dictionary("abnormal",combo)
            features.append(combo_name+"免疫")
    # 属性加成（四 则 运 算）
    if attrs["attributeModifiers"] != None and len(attrs["attributeModifiers"]) > 0:
        for modify in attrs["attributeModifiers"]:
            attr_name = anne_dictionary("attribute",modify["attributeType"])
            formula = modify["formulaItem"]
            value = modify["value"]
            value_str = str(value)
            # 获取数据加成/减少的写法
            if modify["loadFromBlackboard"] or modify["fetchBaseValueFromSourceEntity"]: # 读取自黑板或本尊，那value本身没用了，写个未知数
                if modify["fetchBaseValueFromSourceEntity"]:
                    value_str = "(来源同值)"
                else:
                    value_str = "X"
                #
                if formula == "ADDITION":
                    value_str = "+"+value_str
                elif formula == "MULTIPLIER":
                    value_str = "+"+value_str+"%"
                elif formula == "FINAL_ADDITION":
                    value_str = "+"+value_str+"(终加)"
                elif formula == "FINAL_SCALER":
                    value_str = "×"+value_str+"%(终乘)"
            else:
                if formula == "FINAL_SCALER": # yj的小巧思会让终乘在负的情况下+1，实际徒增学习和排错成本
                    value_str = to_percent(value,True) + "(终乘)"
                elif formula == "MULTIPLIER": # 直乘就没有这种小巧思
                    value_str = to_delta_percent(value)
                elif formula == "ADDITION": # 剩下两个只看正负号
                    value_str = to_delta(value)
                elif formula == "FINAL_ADDITION": # 剩下两个只看正负号
                    value_str = to_delta(value) + "(终加)"
            # 根据算法
            features.append(attr_name+value_str)
    # 写入results
    if len(features) > 0:
        results.append("提供"+",".join(features))
    # 耐久buff
    if buff_data["isDurableBuff"]:
        results.append("不可清除")
    # 其伤害可未命中
    if buff_data["isDamageMissable"]:
        results.append("受命中率影响")
    # 几个失效条件，一起展示
    stopby = []
    if buff_data["isSilenceable"]:
        stopby.append("沉默")
    if buff_data["isStunnable"]:
        stopby.append("晕眩")
    if buff_data["isFreezable"]:
        stopby.append("冻结")
    if buff_data["isLevitatable"]:
        stopby.append("浮空")
    if len(stopby) > 0:
        results.append("/".join(stopby)+"期间失效")
    # 属于状态可抵抗Buff？
    if buff_data["statusResistable"] == "YES" or (buff_data["statusResistable"] == "AUTOMATIC" and has_resistable_flag):
        results.append("可抵抗")
    # 处理覆盖时使用的Key
    if buff_data["overrideKey"] and buff_data["overrideKey"] != "empty" :
        results.append(f"处理覆盖时视为{buff_data['overrideKey']}") 
    # 覆写事件优先级
    if buff_data["overrideOnEventPriority"]:
        results.append(f"事件优先级覆写为{buff_data['onEventPriority']}")
    # 持续时间配置
    if buff_data["lifeTimeType"] == "INFINITY" :
        results.append("永久")
    elif buff_data["lifeTimeType"] == "LIMITED" :
        if buff_data["durationKey"] != "none" :
            results.append(f"持续({buff_data['durationKey']})秒")
        elif buff_data["lifeTime"] == 0.0:
            results.append("持续一瞬间")
        else:
            results.append(f"持续{str(buff_data['lifeTime'])}秒")
    # 触发配置
    if buff_data["triggerLifeType"] == "IMMEDIATELY" : # 立即触发或不触发
        if buff_data["waitFirstTriggerInterval"] and buff_data["firstTriggerInterval"] >= 0:
            ticks = math.ceil(buff_data['firstTriggerInterval'] * 30)
            results.append(f"{ticks}帧后触发")
        elif buff_data["triggerInterval"] >= 0:
            ticks = math.ceil(buff_data['triggerInterval'] * 30)
            results.append(f"{ticks}帧后触发")
        #else:
        #    results.append("立即触发")
    elif buff_data["triggerLifeType"] == "INFINITY" : # 无限次触发
        if buff_data["waitFirstTriggerInterval"] and buff_data["firstTriggerInterval"] >= 0:
            start_ticks = buff_data["firstTriggerInterval"]
            if buff_data["triggerInterval"] >= 0:
                ticks = math.ceil(buff_data['triggerInterval'] * 30)
                results.append(f"{start_ticks}帧后及后续每{ticks}帧触发一次")
            else:
                results.append(f"{start_ticks}帧后触发")
        elif buff_data["triggerInterval"] >= 0:
            ticks = math.ceil(buff_data['triggerInterval'] * 30)
            results.append(f"每{ticks}帧触发一次")
    elif buff_data["triggerLifeType"] == "LIMITED" : # 有限次触发
        if buff_data["triggerCnt"] > 1:
            trigget_cnt = buff_data["triggerCnt"]
            if buff_data["waitFirstTriggerInterval"] and buff_data["firstTriggerInterval"] >= 0:
                start_ticks = buff_data["firstTriggerInterval"]
                if buff_data["triggerInterval"] >= 0:
                    ticks = math.ceil(buff_data['triggerInterval'] * 30)
                    results.append(f"{start_ticks}帧后及后续每{ticks}帧触发一次，上限{trigget_cnt}次")
                else:
                    results.append(f"{start_ticks}帧后触发")
            elif buff_data["triggerInterval"] >= 0:
                ticks = math.ceil(buff_data['triggerInterval'] * 30)
                results.append(f"{ticks}帧后触发")
        elif buff_data["triggerCnt"] == 1:
            if buff_data["waitFirstTriggerInterval"] and buff_data["firstTriggerInterval"] >= 0:
                ticks = math.ceil(buff_data['firstTriggerInterval'] * 30)
                results.append(f"{ticks}帧后触发")
            elif buff_data["triggerInterval"] >= 0:
                ticks = math.ceil(buff_data['triggerInterval'] * 30)
                results.append(f"{ticks}帧后触发")
    # 叠加类型配置
    if buff_data["overrideType"] != "DEFAULT" :
        if buff_data["overrideType"] == "STACK" :
            max_stack = buff_data['maxStackCnt']
            if buff_data["refreshRemainingTimeWhenStackMax"]:
                if buff_data["clearAllStackCntWhenTimeUp"]:
                    results.append(f"可叠加{max_stack}，叠满后仅刷新时间，到时间时Buff直接结束")
                else:
                    results.append(f"可叠加{max_stack}，叠满后仅刷新时间，到时间降低一层并刷新时间")
            else:
                if buff_data["clearAllStackCntWhenTimeUp"]:
                    results.append(f"可叠加{max_stack}，叠满后无法再施加，到时间时Buff直接结束")
                else:
                    results.append(f"可叠加{max_stack}，叠满后无法再施加，到时间降低一层并刷新时间")
            
        elif buff_data["overrideType"] == "EXTEND" :
            if buff_data["takeSnapshotWhenExtend"]:
                results.append(f"重复施加时仅延长原有Buff并更新数据")
            else:
                results.append(f"重复施加时仅延长原有Buff")
        else:
            results.append(f"叠加类型{buff_data['overrideType']}")
    # 暂时不知道有什么用的东西
    #if buff_data["independentCharacterSource"]:
    #    results.append("independentCharacterSource")
    #if buff_data["priority"]:
    #    results.append("priority")
    #if buff_data["priorityBBKeys"]:
    #    results.append("priorityBBKeys")
    #if buff_data["stripBlackboardParamsWithBuffKey"]:
    #    results.append("stripBlackboardParamsWithBuffKey")
    # 最后写入黑板数据
    if len(blackboard) > 0:
        results.append(str(blackboard))
    # 返回buff的各项属性
    return {
        "main" : buff_key, # 可能需翻译
        "description" : ";".join(results)
    }