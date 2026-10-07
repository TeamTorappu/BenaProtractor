#----------------------------------------
# 解析Buff
#----------------------------------------
import math

from .attribute import analyze_attribute_modifiers
from dictionary import anne_dictionary

STATUS_RESISTABLE_ABNORMAL = ["STUNNED","COLD","FROZEN","FEARED","PALSY","ATTRACTED"]

# 解析Buff的详细信息
# 返回结构体
def analyze_buff(buff_data: dict,blackboard: dict = {},full_information=False):
    buff_key = buff_data["buffKey"]
    # 开始解析
    features = []
    blackboard_dict = {"main" : "黑板数据：","children":[]}
    template = "empty"
    has_resistable_flag = False

    # 检查黑板
    if buff_data["blackboard"] and len(buff_data["blackboard"]) > 0:
        for bb_data in buff_data["blackboard"]:
            if bb_data["value"]:
                #blackboard[bb_data["key"]] = bb_data["value"]
                blackboard_dict["children"].append({"main" : f"[{bb_data['key']}] = {bb_data['value']}"})
            elif bb_data["valueStr"]:
                #blackboard[bb_data["key"]] = bb_data["valueStr"]
                blackboard_dict["children"].append({"main" : f"[{bb_data['key']}] = \"{bb_data['valueStr']}\""})

    # 读取自数据库，一般是眩晕、寒冷那些，不管他
    if buff_data["loadFromDB"]:
        if full_information:
            features.append("读取自数据库：[" + buff_key + "]")
        elif len(blackboard_dict["children"]) > 0:
            return {
                "main" : "<" + buff_key + "> (读取自数据库)",
                "children" : [blackboard_dict]
            }
        else:
            return {"main" : "<" + buff_key + "> (读取自数据库)"}
    
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

    # 持续时间配置
    if full_information: # 完整时间显示
        if buff_data["lifeTimeType"] == "INFINITY":
            features.append("持续时间：无限")
        elif buff_data["lifeTimeType"] == "LIMITED":
            if buff_data["durationKey"] != None and buff_data["durationKey"] != "none":
                features.append(f"持续时间：[{buff_data['durationKey']}] 秒")
            elif buff_data["lifeTime"] == 0.0:
                features.append("持续时间：0秒（即Buff开始后，执行完一部分事件立刻结束）")
            else:
                seconds = round(buff_data['lifeTime'],3)
                ticks = math.ceil(buff_data['lifeTime'] * 30)
                features.append(f"持续时间：{str(seconds)}秒（{str(ticks)}帧）")
    else: # 简短时间
        if buff_data["lifeTimeType"] == "INFINITY":
            features.append("永久")
        elif buff_data["lifeTimeType"] == "LIMITED":
            if buff_data["durationKey"] != None and buff_data["durationKey"] != "none":
                if buff_data["durationKey"] in blackboard:
                    features.append(f"持续 {blackboard[buff_data['durationKey']]} 秒")
                else:
                    features.append(f"持续 [{buff_data['durationKey']}] 秒")
            elif buff_data["durationKey"] != "none" and "duration" in blackboard:
                features.append(f"持续 {blackboard['duration']} 秒")
            elif buff_data["lifeTime"] == 0.0:
                features.append("瞬间效果")
            else:
                seconds = round(buff_data['lifeTime'],3)
                features.append(f"持续{str(seconds)}秒")

    # 异常效果家族与属性增减
    attrs = buff_data["attributes"]
    # 以下内容yj都写过[]和null的格式，泥岩的recharge居然同时两种都用，绝了
    # 异常效果
    if attrs["abnormalFlags"] != None and len(attrs["abnormalFlags"]) > 0:
        if full_information:
            flags = []
            for flag in attrs["abnormalFlags"]:
                flags.append(anne_dictionary("abnormal",flag))
                # 包含可状态抵抗的异常
                if flag in STATUS_RESISTABLE_ABNORMAL:
                    has_resistable_flag = True
            features.append("包含异常效果："+"、".join(flags))
        else:
            for flag in attrs["abnormalFlags"]:
                flag_name = anne_dictionary("abnormal",flag)
                features.append(flag_name)
                # 包含可状态抵抗的异常
                if flag in STATUS_RESISTABLE_ABNORMAL:
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
        features += analyze_attribute_modifiers(attrs["attributeModifiers"],blackboard)
            
    # 耐久buff
    if buff_data["isDurableBuff"]:
        if full_information:
            features.append("不可清除（重生、傀儡师切换等情况下的清除；仍能被结束）")
        else:
            features.append("不可清除")
    # 其伤害可未命中
    if buff_data["isDamageMissable"]:
        features.append("攻击未命中时失效")
    # 几个失效条件，一起展示
    stopby = []
    if buff_data.get("isSilenceable",False):
        stopby.append("沉默")
    if buff_data.get("isStunnable",False):
        stopby.append("晕眩")
    if buff_data.get("isFreezable",False):
        stopby.append("冻结")
    if buff_data.get("isLevitatable",False):
        stopby.append("浮空")
    if buff_data.get("isGroundBoundable",False):
        stopby.append("缚地")
    if len(stopby) > 0:
        features.append("/".join(stopby)+"期间失效")
    # 属于状态可抵抗Buff？
    if buff_data["statusResistable"] == "YES":
        if full_information:
            features.append("可状态抵抗（模式为YES）")
        else:
            features.append("可状态抵抗")
    elif (buff_data["statusResistable"] == "AUTOMATIC" and has_resistable_flag):
        if full_information:
            features.append("可状态抵抗（模式为AUTOMATIC；包含可状态抵抗的异常效果）")
        else:
            features.append("可状态抵抗")
    elif full_information:
        if buff_data["statusResistable"] == "AUTOMATIC": # and not has_resistable_flag
            features.append("不可状态抵抗（模式为AUTOMATIC；不包含可状态抵抗的异常效果）")
        else:
            features.append("不可状态抵抗（模式为NO）")
    # 处理覆盖时使用的Key
    if buff_data["overrideKey"] and buff_data["overrideKey"] != "empty" :
        if buff_data["independentCharacterSource"]: #每个来源独立OverrideKey
            features.append(f"处理覆盖时视为 (Buff来源名称)+<{buff_data['overrideKey']}>")
        else:
            features.append(f"处理覆盖时视为 <{buff_data['overrideKey']}>")
    elif "independentCharacterSource" in buff_data and buff_data["independentCharacterSource"]:
        features.append(f"处理覆盖时视为 (Buff来源名称)+<{buff_key}>")
    # 触发配置
    if buff_data["triggerLifeType"] == "INFINITY" : # 无限次触发
        if buff_data["waitFirstTriggerInterval"] and buff_data["firstTriggerInterval"] >= 0:
            start_ticks = math.ceil(buff_data["firstTriggerInterval"] * 30)
            if buff_data["triggerInterval"] >= 0:
                ticks = round(buff_data['triggerInterval'] * 30,3)
                features.append(f"{start_ticks}帧后及后续每{ticks}帧触发一次")
            else:
                features.append(f"{start_ticks}帧后触发仅一次")
        elif buff_data["triggerInterval"] >= 0:
            if buff_data["waitFirstTriggerInterval"]:
                ticks = round(buff_data['triggerInterval'] * 30,3)
                features.append(f"每{ticks}帧触发一次")
            else:
                ticks = round(buff_data['triggerInterval'] * 30,3)
                features.append(f"施加时及后续每{ticks}帧触发一次")
    else: #if buff_data["triggerLifeType"] in ["LIMITED","IMMEDIATELY"] : # 有限次触发
        trigget_cnt = buff_data["triggerCnt"]
        if trigget_cnt > 1:
            if buff_data["waitFirstTriggerInterval"] and buff_data["firstTriggerInterval"] >= 0:
                start_ticks = math.ceil(buff_data["firstTriggerInterval"] * 30)
                if buff_data["triggerInterval"] >= 0:
                    ticks = round(buff_data['triggerInterval'] * 30,3)
                    features.append(f"{start_ticks}帧后及后续每{ticks}帧触发一次，上限{trigget_cnt}次")
                else:
                    features.append(f"{start_ticks}帧后触发仅一次")
            elif buff_data["triggerInterval"] >= 0:
                ticks = round(buff_data['triggerInterval'] * 30,3)
                features.append(f"施加时及后续每{ticks}帧触发一次，上限{trigget_cnt}次")
        elif trigget_cnt == 1:
            if buff_data["waitFirstTriggerInterval"] and buff_data["firstTriggerInterval"] >= 0:
                ticks = round(buff_data['triggerInterval'] * 30,3)
                features.append(f"{ticks}帧后触发")
            else:
                features.append(f"施加后立刻触发")
    # 覆盖类型配置
    if buff_data["disableOverride"]:
        if full_information:
            features.append(f"不处理覆盖（同名效果间互相独立）")
        else:
            features.append(f"同名效果间互相独立")
    elif buff_data["overrideType"] != "DEFAULT":
        if buff_data["overrideType"] == "STACK" :
            stack_info = ""
            max_stack = int(buff_data['maxStackCnt'])
            if "max_stack_cnt" in blackboard: # 黑板覆写叠层上限
                max_stack = int(blackboard["max_stack_cnt"])
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
    # 叠加优先级，鼓舞之类的用的
    if buff_data["priorityBBKeys"] != None and len(buff_data["priorityBBKeys"]) > 0:
        bb_keys = "、".join(buff_data['priorityBBKeys'])
        features.append(f"根据黑板值 [{bb_keys}] 计算叠加优先级")
    elif buff_data["priority"] > 0:
        features.append(f"叠加优先级{buff_data['priority']}")
    # 黑板前缀
    if "stripBlackboardParamsWithBuffKey" in buff_data and buff_data["stripBlackboardParamsWithBuffKey"]:
        if full_information:
            features.append(f"使用有以Buff名称为前缀的黑板键")
        else:
            features.append(f"使用带前缀的黑板键")
    # 特效方向
    if "enableInitDirectionFromSource" in buff_data and buff_data["enableInitDirectionFromSource"]:
        features.append(f"根据来源位置旋转特效方向")

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
    if len(blackboard_dict["children"]) > 0:
        if "children" not in result:
            result["children"] = []
        result["children"].append(blackboard_dict)
    return result