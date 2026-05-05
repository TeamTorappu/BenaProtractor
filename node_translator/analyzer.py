import json
import os
import math
from translator import anne_dictionary

GAP = 0.000000001
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
# 解析定点数
# 返回浮点数
def analyze_FP(FP: dict):
    if "_serializedValue" not in FP:
        return 0.
    serialized_value = FP["_serializedValue"]
    return float(serialized_value) / 4294967296.

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
        if "_considerUnhurtable" in damage_data and damage_data["_considerUnhurtable"]:
            features.append("生命流失+强制生命流失")
        else:
            features.append("生命流失")
    if "_isEnvDamage" in damage_data and damage_data["_isEnvDamage"]:
        features.append("环境伤害")
    if "_isUndeadable" in damage_data and damage_data["_isUndeadable"]:
        features.append("不会致命")
    if "_instantKillLikeDamage" in damage_data and damage_data["_instantKillLikeDamage"]:
        features.append("类斩杀伤害")
    if "_isNotChangeableValue" in damage_data and damage_data["_isNotChangeableValue"]:
        features.append("无法增/减/免伤/重设")
    elif "_forceDisplayDamageNum" in damage_data and damage_data["_forceDisplayDamageNum"]:
        features.append("强制红字")
    if "_noSource" in damage_data and damage_data["_noSource"]:
        features.append("无来源")
    elif "_isNoSourceDamage" in damage_data and damage_data["_isNoSourceDamage"]:
        features.append("无来源")
    elif "_noSourceDamage" in damage_data and damage_data["_noSourceDamage"]:
        features.append("无来源")
    #if "_damageWithoutModify" in damage_data and damage_data["_damageWithoutModify"]: #似乎没有任何用途
    #    features.append("damageWithoutModify")
    if "_setSharedFlag" in damage_data and damage_data["_setSharedFlag"]:
        if "_sharedFlagIndex" in damage_data:
            shared_flag_name = anne_dictionary("sharedflag",damage_data["_sharedFlagIndex"])
            if shared_flag_name not in features:
                features.append(shared_flag_name)
    # 疑似是火陈的小巧思，限定伤害类型的无视闪避
    if "_ignoreMissFlag" in damage_data and damage_data["_ignoreMissFlag"] != "NONE":
        features.append("无视"+anne_dictionary("damage_type",damage_data["_ignoreMissFlag"])+"闪避")
    # 乘以黑板值
    #if "_multiplierByKey" in damage_data and damage_data["_multiplierByKey"]:
    #    if "_multiplierKey" in damage_data and damage_data["_multiplierKey"]:
    #        features.append("乘以黑板值"+damage_data["_multiplierKey"])
    # 伤害标签
    if "_modifierKey" in damage_data and damage_data["_modifierKey"] != "":
        suffix = suffix + f"（具有 {damage_data['_modifierKey']} 标记）"
    # 无视闪避/格挡那些的掩码，不过yj只用几个特定掩码，所以没必要做掩码解析
    if "_ignoreCancelReasonMask" in damage_data and damage_data["_ignoreCancelReasonMask"] != "NONE":
        if damage_data["_ignoreCancelReasonMask"] == "MISS":
            features.append("无视闪避")
        elif damage_data["_ignoreCancelReasonMask"] == "BLOCK":
            features.append("无视格挡")
        elif damage_data["_ignoreCancelReasonMask"] == "HIT_FAILED":
            features.append("不受命中率判定影响")
        else: # 不行的话全展示吧
            reasons = []
            for reason in damage_data["_ignoreCancelReasonMask"]:
                reasons.append(anne_dictionary("cancel_reason",reason))
            features.append("不受"+"/".join(reasons)+"影响")
    if len(features) > 0:
        suffix += "（"+"；".join(features)+"）"
    return prefix + damage_type_name + attack_type_name + "伤害"+suffix
    
# 解析Buff的详细信息
# 返回结构体
def analyze_buff(buff_data,full_information=False):
    buff_key = buff_data["buffKey"]
    # 开始解析
    features = []
    blackboard = {}
    template = "empty"
    has_resistable_flag = False

    # 读取自数据库，一般是眩晕、寒冷那些，不管他
    if buff_data["loadFromDB"]:
        if full_information:
            features.append("读取自数据库：[" + buff_key + "]")
        else:
            return {"main" : "<" + buff_key + "> (读取自数据库)","link" : "buff." + buff_key}
    
    # 检查模板与事件优先级
    if buff_data["templateKey"] != "empty" :
        template = buff_data["templateKey"]
        priority = anne_dictionary("event_priority",buff_data['onEventPriority'])
        # 覆写事件优先级
        if buff_data["overrideOnEventPriority"]:
            if full_information:
                features.append(f"事件优先级：{priority}（覆盖模板的数据）")
            else:
                features.append(f"事件优先级覆写为 {priority}")
    elif buff_data["overrideOnEventPriority"] or buff_data['onEventPriority'] != "DEFAULT":
        priority = anne_dictionary("event_priority",buff_data['onEventPriority'])
        if full_information:
            features.append(f"事件优先级：{priority}")
        else:
            features.append(f"事件优先级为 {priority}")
    # 检查黑板
    if buff_data["blackboard"] and len(buff_data["blackboard"]) > 0:
        for bb_data in buff_data["blackboard"]:
            bb_key = bb_data["key"]
            if bb_data["value"]:
                blackboard[bb_key] = bb_data["value"]
            elif bb_data["valueStr"]:
                blackboard[bb_key] = bb_data["valueStr"]

    # 持续时间配置
    if full_information: # 完整时间显示
        if buff_data["lifeTimeType"] == "INFINITY":
            features.append("持续时间：无限")
        elif buff_data["lifeTimeType"] == "LIMITED":
            if buff_data["durationKey"] != None and buff_data["durationKey"] != "none":
                features.append(f"持续时间：{buff_data['durationKey']} 秒")
            elif buff_data["lifeTime"] == 0.0:
                features.append("持续时间：0秒（即Buff开始时事件结束后立刻结束）")
            else:
                seconds = math.floor(buff_data['lifeTime'])
                ticks = math.ceil((buff_data['lifeTime'] % 1.0) * 30)
                if seconds > 0:
                    features.append(f"持续时间：{str(seconds)}秒 {str(ticks)}帧")
                else:
                    features.append(f"持续时间：{str(ticks)}帧")
    else: # 简短时间
        if buff_data["lifeTimeType"] == "INFINITY":
            features.append("永久")
        elif buff_data["lifeTimeType"] == "LIMITED":
            if buff_data["durationKey"] != None and buff_data["durationKey"] != "none":
                features.append(f"持续 [{buff_data['durationKey']}] 秒")
            elif buff_data["lifeTime"] == 0.0:
                features.append("瞬间效果")
            else:
                seconds = math.floor(buff_data['lifeTime'])
                ticks = math.ceil((buff_data['lifeTime'] % 1.0) * 30)
                if seconds > 0:
                    features.append(f"持续{str(seconds)}秒 {str(ticks)}帧")
                else:
                    features.append(f"持续{str(ticks)}帧")
        
    # 异常效果家族与属性增减
    attrs = buff_data["attributes"]
    # 以下内容yj都写过[]和null的格式，泥岩的recharge居然同时两种都用，绝了
    # 异常效果
    if attrs["abnormalFlags"] != None and len(attrs["abnormalFlags"]) > 0:
        if full_information:
            flags = []
            for flag in attrs["abnormalFlags"]:
                flags.append(anne_dictionary("abnormal",flag))
                # 包含可抵抗状态
                if flag in ["STUNNED","COLD","FROZEN"]:
                    has_resistable_flag = True
            features.append("包含异常效果："+"、".join(flags))
        else:
            for flag in attrs["abnormalFlags"]:
                flag_name = anne_dictionary("abnormal",flag)
                features.append(flag_name)
                # 包含可抵抗状态
                if flag in ["STUNNED","COLD","FROZEN"]:
                    has_resistable_flag = True
    # 异常免疫
    if attrs["abnormalImmunes"] != None and len(attrs["abnormalImmunes"]) > 0:
        if full_information:
            flags = []
            for flag in attrs["abnormalImmunes"]:
                flags.append(anne_dictionary("abnormal",flag))
            features.append("包含异常免疫："+"、".join(flags))
        else:
            for flag in attrs["abnormalImmunes"]:
                flag_name = anne_dictionary("abnormal",flag)
                if full_information:
                    features.append("包含异常免疫："+flag_name)
                else:
                    features.append(flag_name+"免疫")
    # 异常反制
    if attrs["abnormalAntis"] != None and len(attrs["abnormalAntis"]) > 0:
        if full_information:
            flags = []
            for flag in attrs["abnormalAntis"]:
                flags.append(anne_dictionary("abnormal",flag))
            features.append("包含异常反制："+"、".join(flags))
        else:
            for flag in attrs["abnormalAntis"]:
                flag_name = anne_dictionary("abnormal",flag)
                features.append(flag_name+"反制")
    # 异常组合
    if attrs["abnormalCombos"] != None and len(attrs["abnormalCombos"]) > 0:
        if full_information:
            combos = []
            for combo in attrs["abnormalCombos"]:
                combos.append(anne_dictionary("abnormal",combo))
            features.append("包含异常组合："+"、".join(combos))
        else:
            for combo in attrs["abnormalCombos"]:
                combo_name = anne_dictionary("abnormal",combo)
                features.append(combo_name)
    # 异常组合免疫
    if attrs["abnormalComboImmunes"] != None and len(attrs["abnormalComboImmunes"]) > 0:
        if full_information:
            combos = []
            for combo in attrs["abnormalComboImmunes"]:
                combos.append(anne_dictionary("abnormal",combo))
            features.append("包含异常组合免疫："+"、".join(combos))
        else:
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
                    value_str = "[" + modify["attributeType"].lower() + "]" # 理论上是和type同名的黑板值
                #
                if formula == "ADDITION":
                    value_str = "+"+value_str+"(直加)"
                elif formula == "MULTIPLIER":
                    value_str = "+"+value_str+"%(直乘)"
                elif formula == "FINAL_ADDITION":
                    value_str = "+"+value_str+"(终加)"
                elif formula == "FINAL_SCALER":
                    value_str = "×"+value_str+"%(终乘)"
            else:
                if formula == "FINAL_SCALER": # yj的小巧思会让终乘在负的情况下+1，实际徒增学习和排错成本
                    value_str = to_percent(value,True) + "(终乘)"
                elif formula == "MULTIPLIER": # 直乘就没有这种小巧思
                    value_str = to_delta_percent(value) + "(直乘)"
                elif formula == "ADDITION": # 剩下两个只看正负号
                    value_str = to_delta(value) + "(直加)"
                elif formula == "FINAL_ADDITION": # 剩下两个只看正负号
                    value_str = to_delta(value) + "(终加)"
            # 根据算法
            features.append(attr_name+value_str)
    # 耐久buff
    if buff_data["isDurableBuff"]:
        if full_information:
            features.append("不可清除（重生、傀儡师切换等情况下的清除；仍能被结束）")
        else:
            features.append("不可清除")
    # 其伤害可未命中
    if buff_data["isDamageMissable"]:
        if full_information:
            features.append("该Buff的处理可能受命中率判定影响")
        else:
            features.append("受命中率判定影响")
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
        features.append("/".join(stopby)+"期间失效")
    # 属于状态可抵抗Buff？
    if buff_data["statusResistable"] == "YES":
        if full_information:
            features.append("可抵抗（模式为YES）")
        else:
            features.append("可抵抗")
    elif (buff_data["statusResistable"] == "AUTOMATIC" and has_resistable_flag):
        if full_information:
            features.append("可抵抗（模式为AUTOMATIC；因包含可抵抗异常效果而可抵抗）")
        else:
            features.append("可抵抗")
    elif full_information:
        if buff_data["statusResistable"] == "AUTOMATIC": # and not has_resistable_flag
            features.append("不可抵抗（模式为AUTOMATIC；但不包含可抵抗异常效果）")
        else:
            features.append("不可抵抗（模式为NO）")
    # 处理覆盖时使用的Key
    if buff_data["overrideKey"] and buff_data["overrideKey"] != "empty" :
        features.append(f"处理覆盖时视为{buff_data['overrideKey']}") 
    # 触发配置
    if buff_data["triggerLifeType"] == "INFINITY" : # 无限次触发
        if buff_data["waitFirstTriggerInterval"] and buff_data["firstTriggerInterval"] >= 0:
            start_ticks = buff_data["firstTriggerInterval"]
            if buff_data["triggerInterval"] >= 0:
                ticks = buff_data['triggerInterval'] * 30
                features.append(f"{start_ticks}帧后及后续每{ticks}帧触发一次")
            else:
                features.append(f"{start_ticks}帧后触发仅一次")
        elif buff_data["triggerInterval"] >= 0:
            if buff_data["waitFirstTriggerInterval"]:
                ticks = buff_data['triggerInterval'] * 30
                features.append(f"每{ticks}帧触发一次")
            else:
                ticks = buff_data['triggerInterval'] * 30
                features.append(f"施加时及后续每{ticks}帧触发一次")
    else: #if buff_data["triggerLifeType"] in ["LIMITED","IMMEDIATELY"] : # 有限次触发
        trigget_cnt = buff_data["triggerCnt"]
        if trigget_cnt > 1:
            if buff_data["waitFirstTriggerInterval"] and buff_data["firstTriggerInterval"] >= 0:
                start_ticks = math.ceil(buff_data["firstTriggerInterval"])
                if buff_data["triggerInterval"] >= 0:
                    ticks = buff_data['triggerInterval'] * 30
                    features.append(f"{start_ticks}帧后及后续每{ticks}帧触发一次，上限{trigget_cnt}次")
                else:
                    features.append(f"{start_ticks}帧后触发仅一次")
            elif buff_data["triggerInterval"] >= 0:
                ticks = buff_data['triggerInterval'] * 30
                features.append(f"施加时及后续每{ticks}帧触发一次，上限{trigget_cnt}次")
        elif trigget_cnt == 1:
            if buff_data["waitFirstTriggerInterval"] and buff_data["firstTriggerInterval"] >= 0:
                ticks = buff_data['firstTriggerInterval'] * 30
                features.append(f"{ticks}帧后触发")
            else:
                features.append(f"施加后立刻触发")
    # 覆盖类型配置
    if buff_data["disableOverride"]:
        features.append(f"多个buff间互相独立，不处理覆盖")
    elif buff_data["overrideType"] != "DEFAULT":
        if buff_data["overrideType"] == "STACK" :
            stack_info = ""
            max_stack = buff_data['maxStackCnt']
            if buff_data["refreshRemainingTimeWhenStackMax"]:
                if max_stack == 1:
                    stack_info = f"再次施加仅刷新时间"
                elif max_stack == 0:
                    stack_info = f"可无限叠加"
                else:
                    stack_info = f"可叠加{max_stack}层，溢出层数仅能刷新时间"
            elif max_stack > 1:
                stack_info = f"可叠加{max_stack}层，溢出层数无效"
            elif max_stack <= 0:
                stack_info = f"可无限叠加"
            if max_stack != 1 and buff_data["lifeTimeType"] != "INFINITY": # 对于1层和永久Buff而言，两者没区别
                if buff_data["clearAllStackCntWhenTimeUp"]:
                    stack_info += "，到时间失去全部层数"
                else:
                    stack_info += "，到时间失去一层并刷新时间"
            if stack_info != "":
                features.append(stack_info)
        elif buff_data["overrideType"] == "EXTEND" :
            if buff_data["takeSnapshotWhenExtend"]:
                features.append(f"重复施加时仅延长原有Buff并更新数据")
            else:
                features.append(f"重复施加时仅延长原有Buff")
        elif buff_data["overrideType"] == "UNIQUE" :
            features.append(f"若已存在则无法重复施加")
        else:
            features.append(f"叠加类型{buff_data['overrideType']}")
    # 暂时不知道有什么用的东西
    if buff_data["independentCharacterSource"]:
        features.append("independentCharacterSource")
    # 叠加优先级，鼓舞之类的用的
    if buff_data["priorityBBKeys"] != None and len(buff_data["priorityBBKeys"]) > 0:
        bb_keys = "、".join(buff_data['priorityBBKeys'])
        features.append(f"根据黑板值 [{bb_keys}] 计算叠加优先级")
    elif buff_data["priority"] > 0:
        features.append(f"叠加优先级{buff_data['priority']}")
    # 黑板前缀
    if buff_data["stripBlackboardParamsWithBuffKey"]:
        features.append(f"使用有以BuffKey为前缀的黑板Key")

    # 准备返回buff
    result = {"main" : "<" + buff_key + ">"}
    if buff_data["loadFromDB"]:
        result["link"] = "buff."+buff_key
    elif template != "empty":
        if full_information: # 完整显示
            result["children"] = [{
                "main" : f"Buff模板：<{template}>",
                "link" : "buff_template."+template
            }]
        else: # 简短显示
            if template == buff_key:
                result["main"] += "（使用同名模板）"
                result["link"] = "buff_template."+template
            elif template == "empty":
                result["main"] += "（不使用模板）"
            else:
                result["main"] += f"（模板：<{template}>）"
                result["link"] = "buff_template."+template
    if full_information: # 按需返回子列表
        if "children" not in result:
            result["children"] = []
        result["children"] += [{"main" : feature} for feature in features]
    else: # 按需返回合并后的列表
        result["description"] = "；".join(features)
    
    # 最后写入黑板数据
    if len(blackboard) > 0:
        bb_children = []
        for key,value in blackboard.items():
            if isinstance(value,str):
                bb_children.append({"main" : "[" + key + "] = \"" + value + "\""})
            else:
                bb_children.append({"main" : "[" + key + "] = " + str(value)})
        if "children" not in result:
            result["children"] = []
        result["children"].append({"main" : "黑板数据：","children" : bb_children})
    return result

# 解析Buff的详细信息
# 返回结构体
def analyze_deck_buff(deck_buff_data,full_information=False):
    # 未解析参数：showToastWhenAffect
    result = analyze_buff(deck_buff_data["buff"],full_information)
    if full_information:
        if deck_buff_data["lifeType"] == "ALL_THE_TIME":
            result["children"].append({"main" : "每次对象部署时生效"})
        else:
            result["children"].append({"main" : "下一次对象部署时生效，仅生效一次"})
        if deck_buff_data["affectInHand"]:
            result["children"].append({"main" : "仅生效于\"位于手卡中\"的对象（即未被隐藏的单位）"})
        if deck_buff_data["affectOutOfHand"]:
            result["children"].append({"main" : "仅生效于\"不位于手卡中\"的对象（即被隐藏的单位）"})
        if deck_buff_data["cardEffectType"] != "NONE":
            result["children"].append({"main" : "为对象增加头像特效" + deck_buff_data["cardEffectType"]})
        if deck_buff_data["cardAnimWhenDeckbuffAdd"] != "":
            result["children"].append({"main" : "添加时增加头像动画" + deck_buff_data["cardAnimWhenDeckbuffAdd"]})
        if deck_buff_data["wontSpawnWhenRallyPointSwitch"]:
            result["children"].append({"main" : "wontSpawnWhenRallyPointSwitch"})
        if deck_buff_data["ignoreSpecialBuild"]:
            result["children"].append({"main" : "ignoreSpecialBuild"})
    return result

# 解析目标选项的详细信息
# 返回结构体
def analyze_target_options(option,relative_side=True):
    conditions = []
    # 阵营
    if not option["enableAdvancedOptions"] or not option["ignoreTargetSide"]:
        if relative_side:
            conditions.append(anne_dictionary("side_type_relative",option["targetSide"]))
        else:
            conditions.append(anne_dictionary("side_type",option["targetSide"]))
    # 实体类型
    if option["targetCategory"] != "DEFAULT":
        conditions.append(anne_dictionary("entity_category",option["targetCategory"]))
    # 行动方式
    if option["targetMotion"] != "ALL":
        conditions.append(anne_dictionary("motion",option["targetMotion"]))
    # 单位类型
    if option["checkUnitType"]:
        conditions.append(anne_dictionary("unit_type",option["unitTypeMask"]))
    # 如果没有额外选项，这就是要展示的全部了
    if not option["enableAdvancedOptions"]:
        return {
            "main" : "".join(conditions)+"单位",
            "description" : "不启用额外判定"
        }
    # 开始处理剩下的所有
    descriptions = []
    # 无视无法选择
    if option["ignoreTargetFree"]:
        if option["onlyIgnoreSomeOfTargetFreeCase"]:
            abnormal_flag = anne_dictionary("abnormal",option["abnormalFlag"])
            abnormal_combo = anne_dictionary("abnormal",option["abnormalCombo"])
            descriptions.append("无视"+abnormal_flag+"/"+abnormal_combo)
        else:
            descriptions.append("无视无法选择")
    # 无视孤立
    if option["ignoreAllyTargetFree"]:
        descriptions.append("无视孤立")
    # 无视禁疗
    if option["ignoreHealFree"]:
        descriptions.append("无视禁疗")
    # 排除特定有异常效果单位
    if "excludeSomeAbnormalFlags" in option and option["excludeSomeAbnormalFlags"]:
        abnormal_flag = anne_dictionary("abnormal",option["excludeAbnormalFlag"])
        descriptions.append(f"不选择持有{abnormal_flag}异常的单位")
    # 必须特定有异常效果单位
    if "containSomeAbnormalFlags" in option and option["containSomeAbnormalFlags"]:
        abnormal_flag = anne_dictionary("abnormal",option["containAbnormalFlag"])
        descriptions.append(f"必须为持有{abnormal_flag}异常的单位")
    # 行为覆写
    if option["purposeMask"] != "NONE":
        purpose = anne_dictionary("purpose",option["purposeMask"])
        descriptions.append(f"视为一次{purpose}")
    unit_name = "单位"
    # 职业筛选
    if option["professionMask"] != "NONE":
        if option["professionMask"] == "WARRIOR, SNIPER, TANK, MEDIC, SUPPORT, CASTER, SPECIAL, PIONEER":
            #descriptions.append(f"必须是干员")
            unit_name = f"干员"
        elif option["professionMask"] == "WARRIOR, SNIPER, TANK, MEDIC, SUPPORT, CASTER, SPECIAL, TOKEN, PIONEER":
            #descriptions.append(f"必须是干员或召唤物")
            unit_name = f"干员/召唤物"
        elif option["professionMask"] == "WARRIOR, SNIPER, TANK, MEDIC, SUPPORT, CASTER, SPECIAL, TRAP, PIONEER":
            #descriptions.append(f"必须是干员或装置")
            unit_name = f"干员/装置"
        elif option["professionMask"] != "WARRIOR, SNIPER, TANK, MEDIC, SUPPORT, CASTER, SPECIAL, TOKEN, TRAP, PIONEER":
            classes = "/".join([anne_dictionary("profession",_cls) for _cls in option["professionMask"].split(", ")])
            #descriptions.append(f"必须是{classes}单位")
            unit_name = f"{classes}单位"
        
    if len(descriptions) > 0:
        return {
            "main" : "".join(conditions)+unit_name,
            "description" : "；".join(descriptions)
        }
    #最朴实无华的选择，没有任何附加条件
    return {
        "main" : "".join(conditions)+unit_name
    }
        