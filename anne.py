'''
安妮 - 翻译组件
将得到的topic类或buff的node类根据翻译数据转写成对应“人类语”
'''
import json
import math
from data_class import *
from bena import ask_bena

ANNE_NODE = None
ANNE_RELIC = None
ANNE_DICTIONARY_PATH = "./translation/anne_dictionary.json"
ANNE_DICTIONARY = None

GAP = 0.000000001

# 读取字典数据
if ANNE_DICTIONARY == None:
    with open(ANNE_DICTIONARY_PATH,'r',encoding="UTF-8") as _f:
        ANNE_DICTIONARY = json.load(_f)

# 任何翻译器的返回数据结构大概都长这样：
#{
#    "main" : 核心显示文本,
#    "description" : [备注(可选)],
#    "true" : [逻辑真时怎么称呼(可选)],
#    "false" : [逻辑假时怎么称呼(可选)],
#    "children" : [
#        {"main" : ... , "children" : ...},
#        {"main" : ...}
#    ],
#}

'''
#----------------------------------------
# 安妮的节点翻译器
#----------------------------------------
'''
class AnneNode:
    def __init__(self):
        print("[安妮]嗯。")
        
    # 翻译重定向器，本质switch case
    # 翻译返回的结果始终是一层一层的结构体
    def translate(self,node):
        node_name = node.node_name
        if node.translation == None:
            print(f"[安妮]尝试翻译节点 {node_name}")
            method = getattr(self, "node_"+node_name, "")
            if method != "" :
                node.translation = method(node.node_data)
            else: # 无法翻译，把所有数据搓成可阅读的格式
                node.translation = {
                    "main" : node_name+"（未翻译）",
                    "style_closed" : True,
                    "children" : [{"main": str(key) + " : "+str(content)} for key,content in node.node_data.items()]
                }
        # 返回译文
        return node.translation
    

    # 统一解析伤害类的详细信息
    # 返回字符串
    def analyze_damage(self,damage_data,prefix="",suffix=""):
        features = []
        # 伤害类型
        damage_type = damage_data["_damageType"]
        damage_type_name = read_dictionary("damage_type",damage_type)
        # 攻击类型
        attack_type = "NONE"
        if "_attackType" in damage_data:
            attack_type = damage_data["_attackType"]
        attack_type_name = read_dictionary("attack_type",attack_type)
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
                shared_flag_name = read_dictionary("sharedflag",damage_data["_sharedFlagIndex"])
                if shared_flag_name not in features:
                    features.append(shared_flag_name)
        # 疑似是火陈的小巧思，限定伤害类型的无视闪避
        if "_ignoreMissFlag" in damage_data and damage_data["_ignoreMissFlag"] != "NONE":
            features.append("无视"+read_dictionary("damage_type",damage_data["_ignoreMissFlag"])+"闪避")
        # 乘以黑板值
        if "_multiplierByKey" in damage_data and damage_data["_multiplierByKey"]:
            if "_multiplierKey" in damage_data and damage_data["_multiplierKey"]:
                features.append("乘以黑板值"+damage_data["_multiplierKey"])
        # 无视闪避/格挡那些的掩码，不过yj只用几个特定掩码，所以没必要做掩码解析
        if "_ignoreCancelReasonMask" in damage_data and damage_data["_ignoreCancelReasonMask"] != "NONE":
            features.append("无视"+read_dictionary("cancel_reason",damage_data["_ignoreCancelReasonMask"]))
        if len(features) > 0:
            suffix += "（"+";".join(features)+"）"
        return prefix+damage_type_name+attack_type_name+"伤害"+suffix
        
    # 统一解析Buff的详细信息
    # 返回结构体
    def analyze_buff(self,buff_data):
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
                flag_name = read_dictionary("abnormal",flag)
                features.append(flag_name)
                # 包含可抵抗状态
                if flag in ["STUNNED","COLD","FROZEN"]:
                    has_resistable_flag = True
        # 异常免疫
        if attrs["abnormalImmunes"] != None and len(attrs["abnormalImmunes"]) > 0:
            for flag in attrs["abnormalImmunes"]:
                flag_name = read_dictionary("abnormal",flag)
                features.append(flag_name+"免疫")
        # 异常反制
        if attrs["abnormalAntis"] != None and len(attrs["abnormalAntis"]) > 0:
            for flag in attrs["abnormalAntis"]:
                flag_name = read_dictionary("abnormal",flag)
                features.append(flag_name+"反制")
        # 异常组合
        if attrs["abnormalCombos"] != None and len(attrs["abnormalCombos"]) > 0:
            for combo in attrs["abnormalCombos"]:
                combo_name = read_dictionary("abnormal",combo)
                features.append(combo_name)
        # 异常组合免疫
        if attrs["abnormalComboImmunes"] != None and len(attrs["abnormalComboImmunes"]) > 0:
            for combo in attrs["abnormalComboImmunes"]:
                combo_name = read_dictionary("abnormal",combo)
                features.append(combo_name+"免疫")
        # 属性加成（四 则 运 算）
        if attrs["attributeModifiers"] != None and len(attrs["attributeModifiers"]) > 0:
            for modify in attrs["attributeModifiers"]:
                attr_name = read_dictionary("attribute",modify["attributeType"])
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
    
    #----------------------------------------
    # 逻辑类Node（都需要特别处理）
    #----------------------------------------
    # 逻辑 如果+否则
    def node_IfElse(self,node):
        # 判断节点
        struct = ANNE_NODE.translate(node["condition_node"])
        true_flag = "如果是/有/可行/可处理："
        false_flag = "如果不是/没有/不可行/无法处理："
        if "true" in struct:
             true_flag = struct["true"]+"："
             struct.pop("true") # 因为IfElse只影响内圈，对外圈逻辑不影响
        if "false" in struct:
             false_flag = struct["false"]+"："
             struct.pop("false") # 因为IfElse只影响内圈，对外圈逻辑不影响
        if "children" not in struct:
            struct["children"] = []
        # 成功时执行的节点
        success_node_lines = []
        if len(node["succeed_nodes"]) > 0:
            for sub_node in node["succeed_nodes"]:
                success_node_lines.append(ANNE_NODE.translate(sub_node))
            struct["children"].append({"main" : true_flag,"children" : success_node_lines})
        # 失败时执行的节点
        fail_node_lines = []
        if len(node["succeed_nodes"]) > 0:
            for sub_node in node["fail_nodes"]:
                fail_node_lines.append(ANNE_NODE.translate(sub_node))
            struct["children"].append({"main" : false_flag,"children" : fail_node_lines})
        return struct
    
    # 否则（但不在这里翻译）
    def node_IfNot(self,node):
        return {"main" : "否则"}
    
    # 始终执行
    def node_AlwaysNext(self,node):
        return {"main" : "不论前一个节点是否成功，始终继续执行"}
    
    #----------------------------------------
    # 计算类Node
    #----------------------------------------
    # 用各种参数计算黑板值(self,node):
    def node_CalculateBlackboardValueViaParams(self,node):
        # 未解析参数：
        place_name = ""
        input_key = node["_inputKey"]
        output_key = node["_outputKey"]
        formula = input_key
        # 确认处理上下文
        if node["_useAbilityBlackboard"] and node["_abilityName"] != "":
            place_name = f"在能力{node['_abilityName']}的黑板中，"
        # 解析计算方式
        if node["_multiplyParamKey"] != None and node["_multiplyParamKey"] != "": # 乘法运算
            formula += " × " + node["_multiplyParamKey"]
        if node["_dividedParamKey"] != None and node["_dividedParamKey"] != "": # 除法运算
            if node["_useRemainder"]: # 取余
                formula += " rem " + node["_dividedParamKey"]
            else:
                formula += " ÷ " + node["_dividedParamKey"]
        if node["_addParamKey"] != None and node["_addParamKey"] != "": # 加法运算
            formula += " + " + node["_addParamKey"]
        if node["_minusParamKey"] != None and node["_minusParamKey"] != "": # 减法运算
            formula += " - " + node["_minusParamKey"]
        # 上下限
        if node["_minValueKey"] != None and node["_minValueKey"] != "": # 下限
            if node["_maxValueKey"] != None and node["_maxValueKey"] != "":
                formula = "clamp("+formula+","+node["_minValueKey"]+","+node["_maxValueKey"]+")"
            else:
                formula = "max("+formula+","+node["_minValueKey"]+")"
        elif node["_maxValueKey"] != None and node["_maxValueKey"] != "": # 上限
            formula = "min("+formula+","+node["_maxValueKey"]+")"
        # 后续处理
        if node["_finalAbs"]: # 绝对值
            formula = "| "+formula+" |"
        if node["_finalCeil"]: # 向上取整
            formula += "（向上取整）"
        elif node["_finalFloor"]: # 向上取整
            formula += "（向下取整）"
        elif node["_finalRound"]: # 向上取整
            formula += "（就近取整，四舍六入五成双）"
        # 返回完整公式
        return {"main" : f"{place_name}计算黑板值。将 {output_key} 设置为 {formula}"}
    
    # 将召唤物的数量或最大数量记录到黑板中
    def node_AssignTokenCardCntToBB(self,node):
        target_name = read_dictionary("target",node["_targetType"])
        count_key = node["_countKey"]
        if node["_assignMaxCount"]:
            return {"main" : f"在黑板上将{target_name}的召唤物最大持有数记录为 {count_key}"}
        else:
            return {"main" : f"在黑板上将{target_name}的召唤物当前持有数记录为 {count_key}"}
    
    #----------------------------------------
    # 效果类Node
    #----------------------------------------
    # 创建Buff
    def node_CreateBuff(self,node):
        # 未解析参数：_useSpecialBuffSource _specialBuffSource _finishDerivedBuffIfParentFinish
        target_name = read_dictionary("target",node["_buffOwner"])
        buff_name = "Buff"
        if node["_isDerivedBuff"]: # 属于子Buff
            buff_name = "本Buff的子Buff"
        return {
            "main" : f"为{target_name}创建一个{buff_name}：",
            "children" : [self.analyze_buff(node['_buff'])]
        }
        
    # 创建Buff，带召唤物主人处理
    def node_CreateBuffUseHostAsSource(self,node):
        # 未解析参数：_finishDerivedBuffIfParentFinish
        target_name = read_dictionary("target",node["_targetType"])
        source_name = read_dictionary("target",node["_sourceType"])
        buff_name = "Buff"
        if node["_isDerivedBuff"]: # 属于子Buff
            buff_name = "本Buff的子Buff",
        if node["_createOnTargetHost"]: # 对目标召唤物的本尊
            target_name = target_name + "(召唤物)的持有者"
        return {
            "main" : f"让{source_name}为{target_name}创建一个{buff_name}：",
            "children" : [self.analyze_buff(node['_buffData'])]
        }
    
    # 结束Buff
    def node_FinishBuff(self,node):
        # 未解析参数：_updateOverrideMap
        if node["_decCntIfStack"]:
            return {"main" : "此Buff叠层减少一层；若减少至0层则此Buff结束"}
        else:
            return {"main" : "此Buff结束"}
        
    # 结束此Buff的所有子Buff
    def node_FinishDerivedBuff(self,node):
        # 未解析参数：_updateOverrideMap
        return {"main" : "结束此Buff的所有子Buff"}
        
    # 结束某Buff的所有子Buff
    def node_FinishDerivedBuffById(self,node):
        # 未解析参数：_updateOverrideMap _decCntIfStack
        if node["_decCntIfStack"]:
            return {"main" : f"结束{node['_buffKey']}的所有无叠层的子Buff；可叠层的子Buff减少一层叠层，若减少至0层则其结束"}
        else:
            return {"main" : f"结束{node['_buffKey']}的所有子Buff"}

    # 造成无来源伤害
    def node_NoSourceDamage(self,node):
        damage_name = self.analyze_damage(node,"无来源的") # 直接把整个node传参进去
        return {"main" : "对持有者造成X点"+damage_name}
        
    # 造成伤害
    def node_AdvancedApplyDamage(self,node):
        # 未解析参数：_modifierKey _emitSourceOnCalculateDamage
        source_name = read_dictionary("target",node["_sourceType"])
        target_name = read_dictionary("target",node["_targetType"])
        damage_name = self.analyze_damage(node) # 直接把整个node传参进去
        default_atk_scale = to_percent(node["_defaultAtkScale"])
        return {
            "main" : f"让{source_name}对{target_name}造成{str(default_atk_scale)}{damage_name}",
            "description" : f"会读取黑板中的{node['_atkScaleVar']}作为攻击力倍率使用"
        }
        
    # 触发某个能力
    def node_TriggerAbility(self,node):
        # 未解析参数：_checkCanUseAblityFlag
        target_name = read_dictionary("target",node["_targetType"])
        ability_name = node["_abilityName"]
        if node["_ownerType"] == node["_targetType"]:
            return {"main" :f"让{target_name}触发{ability_name}能力"}
        else:
            owner_name = read_dictionary("target",node["_ownerType"])
            return {"main" :f"让{owner_name}向{target_name}触发{ability_name}能力"}
    
    # 格挡/护盾/屏障（还得具体情况具体分析）
    def node_BlockDamage(self,node):
        # 未解析参数：_useSource _sourceType
        #source_name = read_dictionary("target",node["_sourceType"])
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
    
    # 中断召唤物的技能(self,node):
    def node_InterruptTokenSkill(self,node):
        host_name = read_dictionary("target",node["_hostType"])
        return {"main" : f"由{host_name}终止Buff持有者的技能（通常来说，持有者应该是{host_name}的召唤物）"}
    
    # 补充召唤物数量
    def node_RechargeToken(self,node):
        # 未解析参数：_rechargeTiming
        if node["_refreshRemainingCnt"]:
            return {"main" : "将Buff持有者的召唤物数量恢复至默认值"}
        else:
            return {"main" : f"根据黑板上 {node['_cntKey']} 的数值，为Buff持有者补充召唤物（不会超过上限）"}
    
    # 临时提升攻击力倍率
    def node_AtkScaleUp(self,node):
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
    
    # 切换模式
    def node_SwitchMode(self,node):
        # 未解析参数：_restartFSM
        target_name = read_dictionary("target",node["_targetType"])
        action = ""
        if node["_restoreDefault"]:
            action = "切换回默认模式"
        elif node["_loadModeFromBlackboard"]:
            action = "切换至第X号模式"
        else:
            action = f"切换至第{node['_modeIndex']}号模式"
        return {"main" : f"令{target_name}{action}"}
    
    # 结束特定Buff(s)
    def node_FinishBuffsById(self,node):
        # 未解析参数：_updateOverrideMap _finishHostBuff
        target_name = read_dictionary("target",node["_targetType"])
        buff_name = "特定Buff（取决于黑板）" if node["_loadFromBlackboard"] else node["_buffKey"]
        # 仅限某人的buff
        if node["_checkBuffSource"]:
            source_name = read_dictionary("target",node["_sourceType"])
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
    def node_DamageSplit(self,node):
        target_name = read_dictionary("target",node["_targetType"])
        attack_type = read_dictionary("attack_type",node["_attackType"])
        return {"main" : f"将本次伤害的X%以同类型{attack_type}伤害的形式传递给{target_name}（原伤害不会变化）"}
    
    # 伤害倍率
    def node_DamageScale(self,node):
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
            conditions.append("伤害类型为"+read_dictionary("damage_type",node["_damageMask"]))
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
    def node_PlayAudio(self,node):
        target_name = read_dictionary("target",node["_target"])
        return {"main" : f"让{target_name}播放音效 {node['_audioSignal']}"}
        
    # 创建特效
    def node_CreateEffect(self,node):
        return {"main" : "创建特效（暂不翻译）"}
            
    #----------------------------------------
    # 检查类Node
    #----------------------------------------
    # 检查阵营
    def node_CheckCharacterGroupTag(self,node):
        target_name = read_dictionary("target",node["_targetType"])
        group_name = node["_groupTag"] # 需要翻译
        return {
            #"main" : f"检查{target_name}阵营标签：{group_name}",
            "main" : f"检查{target_name}阵营标签",
            "true" : f"若其为{group_name}阵营",
            "false" : f"若其不为{group_name}阵营"
        }
    
    # 检查重量
    def node_FilterByTargetMassLevel(self,node):
        target_name = read_dictionary("target",node["_target"])
        compare = read_dictionary("compare",node["_condType"])
        compare_not = read_dictionary("compare_not",node["_condType"])
        return {
            #"main" : f"检查{target_name}的重量是否{compare}X",
            "main" : f"检查{target_name}的重量",
            "true" : f"若其重量{compare}X",
            "false" : f"若其重量{compare_not}X"
        }

    # 检查是否持有某Buff
    def node_CheckContainsBuff(self,node):
        # 未解析参数：_loadFromBlackboard _checkSourceHost
        target_name = read_dictionary("target",node["_targetType"])
        condition = f"检查{target_name}是否"
        true_flag = "若其持有"
        false_flag = "若其没有"
        if node["isAND"]: # 与模式
            if len(node["_buffKeys"]) > 1:
                if node["_checkBuffSource"]:
                    source_name = read_dictionary("target",node["_buffSourceType"])
                    condition += f"同时持有来自{source_name}的 {'、'.join(node['_buffKeys'])}"
                else:
                    condition += f"同时持有 {'、'.join(node['_buffKeys'])}"
                true_flag = "若其全部持有"
                false_flag = "若其少了其中任意一个"
            elif len(node["_buffKeys"]) == 1:
                if node["_checkBuffSource"]:
                    source_name = read_dictionary("target",node["_buffSourceType"])
                    condition += f"持有来自{source_name}的 {node['_buffKeys'][0]}"
                else:
                    condition += f"持有 {node['_buffKeys'][0]}"
        else: # 或模式
            if len(node["_buffKeys"]) > 1:
                if node["_checkBuffSource"]:
                    source_name = read_dictionary("target",node["_buffSourceType"])
                    condition += f"持有来自{source_name}的 {'、'.join(node['_buffKeys'])} 中的任意一个"
                else:
                    condition += f"持有 {'、'.join(node['_buffKeys'])} 中的任意一个"
                true_flag = "若其持有其中任意一个"
                false_flag = "若其全部都没有"
            elif len(node["_buffKeys"]) == 1:
                if node["_checkBuffSource"]:
                    source_name = read_dictionary("target",node["_buffSourceType"])
                    condition += f"持有来自{source_name}的 {node['_buffKeys'][0]}"
                else:
                    condition += f"持有 {node['_buffKeys'][0]}"
        if condition != "" :
            return {
                "main" : condition,
                "true" : true_flag,
                "false" : false_flag
            }
        else:
            return {
                "main" : "检查Buff，但给定条件无法检查（写法有误？）",
                "true" : "（始终不执行）",
                "true" : "（始终不执行）"
            }

'''
#----------------------------------------
# 安妮的藏品翻译器
#----------------------------------------
'''
class AnneRelic:
    def __init__(self):
        print("[安妮]好的。")
        
    # 翻译重定向器，本质switch case
    # 翻译返回的结果始终是一层一层的结构体
    def translate(self,rogue_effect):
        if rogue_effect.translation == None:
            effect_key = rogue_effect.key
            print(f"[安妮]尝试翻译藏品效果 {effect_key}")
            # 全局buff有二级结构所以拆开来解析
            if effect_key == "global_buff_normal": 
                buff_key = rogue_effect.blackboard["key"] # 这个才是buff的名字
                method = getattr(self, "gbn_"+buff_key.replace("[","_").replace("]",""), "")
                if method != "" :
                    rogue_effect.translation = method(rogue_effect.type,rogue_effect.blackboard)
                    return rogue_effect.translation
                else: # 无法翻译，把所有数据搓成可阅读的格式
                    rogue_effect.translation = {
                        "main" : "环境效果："+buff_key+"（未翻译）",
                        "style_closed" : True,
                        "children" : []
                    }
                    for key,bb in rogue_effect.blackboard.items():
                        rogue_effect.translation["children"].append({"main": str(key) + " : "+str(bb)})
            else: # 其他的效果
                method = getattr(self, "rogue_"+effect_key, "")
                if method != "" :
                    rogue_effect.translation = method(rogue_effect.type,rogue_effect.blackboard)
                    return rogue_effect.translation
                else: # 无法翻译，把所有数据搓成可阅读的格式
                    rogue_effect.translation = {
                        "main" : effect_key+"（未翻译）",
                        "style_closed" : True,
                        "children" : []
                    }
                    for key,bb in rogue_effect.blackboard.items():
                        rogue_effect.translation["children"].append({"main": str(key) + " : "+str(bb)})
        # 返回译文
        return rogue_effect.translation
    
    # 生效时点的处理
    # 返回生效时间的字符串。
    def analyze_timing(self,item_type,blackboard):
        # 根据触发类型...
        trig_type = "GAIN"
        if "trig_type" in blackboard:
            trig_type = blackboard["trig_type"]
        # 界园钱特殊处理
        if item_type == "COPPER_BUFF":
            return read_dictionary("trig_type_copper",trig_type)
        # 返回时点文本
        return read_dictionary("trig_type",trig_type)

    # 职业筛选的处理
    # 返回职业的字符串。说明筛选的职业以及“干员”和“召唤物”这样的称呼
    def analyze_profession(self,profession_mask):
        profession_mask = profession_mask.upper()
        masked_list = [profession_mask]
        if "," in profession_mask:
            masked_list = profession_mask.split(",")
        elif "|" in profession_mask:
            masked_list = profession_mask.split("|")
        # 如果大于等于8职业的话有可能是用于筛所有干员的，进行缩减处理
        if len(masked_list) >= 8 and "PIONEER" in masked_list and "WARRIOR" in masked_list and "TANK" in masked_list and "SNIPER" in masked_list and "CASTER" in masked_list and "SUPPORT" in masked_list and "MEDIC" in masked_list and "SPECIAL" in masked_list:
            if "TOKEN" in masked_list and "TRAP" in masked_list:
                return "干员、召唤物、装置"
            elif "TOKEN" in masked_list:
                return "干员、召唤物"
            elif "TRAP" in masked_list:
                return "干员、装置"
            else:
                return "干员"
        else:
            professions = []
            objects = []
            for masked in masked_list:
                if masked in ["TOKEN","TRAP"]:
                    objects.append(read_dictionary("profession",masked))
                else:
                    professions.append(read_dictionary("profession",masked))
            return "、".join(["/".join(professions)+"干员"] + objects)
    
    # 整个选择器的处理
    # 返回选择器称呼的字符串。说明筛选的职业、部署类型以及“干员”和“召唤物”这样的称呼
    def analyze_selector(self,blackboard,prefix="",suffix=""):
        # 部署类型处理
        place = ""
        if "selector.buildable" in blackboard:
            if blackboard["selector.buildable"] == "melee":
                place = "部署类型为近战位的"
            elif blackboard["selector.buildable"] == "ranged":
                place = "部署类型为远程位的"
        # 职业筛选处理，没有默认全部单位
        if "selector.profession" in blackboard:
            target_name = self.analyze_profession(blackboard["selector.profession"])
            return f"所有{place}{prefix}{target_name}{suffix}"
        else:
            return f"所有{place}{prefix}单位{suffix}"
    
    # 道具的处理
    # 返回结构体，可能会带有链接
    def analyze_item(self,blackboard):
        if "id" in blackboard:
            item = ask_bena("rogue_item",blackboard["id"])
            if item != None:
                if item.type == "COPPER": # 界园钱的特殊处理
                    return {
                        "main": f"让 {item.display_name} 加入玩家钱盒。",
                        "link": blackboard['id']
                    }
                return {
                    "main": f"给予玩家{item.display_type} {item.display_name} ×{math.floor(blackboard.get('count',0))}",
                    "link": blackboard['id']
                }
            return {"main": f"给予玩家 {blackboard['id']} ×{math.floor(blackboard.get('count',0))}"}
        return {"main": f"尝试给予玩家物品，但因未配置物品ID，没有实际效果。"}

    #----------------------------------------
    # 局外效果
    #----------------------------------------
    # 关卡内的可部署人数上限增减
    def rogue_level_char_limit_add(self,item_type,blackboard):
        value = blackboard.get("value",0)
        if value < 0:
            return {"main": f"战斗中的可部署人数上限{to_delta(value)}（不会低于1）"}
        else:
            return {"main": f"战斗中的可部署人数上限{to_delta(value)}"}
    
    # 立即奖励
    def rogue_immediate_reward(self,item_type,blackboard):
        timing = self.analyze_timing(item_type,blackboard)
        translation = self.analyze_item(blackboard)
        translation["main"] = timing+"，"+translation["main"]
        return translation
    
    # 进入特殊节点奖励一次？
    def rogue_secret_into_reward_once(self,item_type,blackboard):
        timing = self.analyze_timing(item_type,blackboard)
        translation = self.analyze_item(blackboard)
        translation["main"] = timing+"，"+translation["main"]
        return translation
    
    # 钱的自变化
    def rogue_copper_exchange(self,item_type,blackboard):
        timing = self.analyze_timing(item_type,blackboard)
        if "id" in blackboard:
            if blackboard["id"] == "pool_reroll_copper":
                return {"main" : f"{timing}，尝试将钱盒内的该钱替换为随机的钱"}
            elif blackboard["id"] == "pool_reroll_copper_high":
                return {"main" : f"{timing}，尝试将钱盒内的该钱替换为随机的花钱"}
            elif blackboard["id"] == "pool_reroll_copper_low":
                return {"main" : f"{timing}，尝试将钱盒内的该钱替换为随机的厉钱"}
            else:
                item = ask_bena("rogue_item",blackboard["id"])
                if item != None:
                    # 变成指定通宝
                    if item.type != "COPPER": # 界园钱的特殊处理
                        return {"main" : f"{timing}，尝试将钱盒内的该钱替换为 {item.display_name}（非通宝，无法正常运作）"}
                    return {
                        "main": f"{timing}，尝试将钱盒内的该钱替换为 {item.display_name} 。",
                        "link": blackboard['id']
                    }
        return {"main" : f"{timing}，尝试将钱盒内的该钱替换为空气。"}
        
    # 战斗后额外掉落随机招募券
    def rogue_battle_extra_recruit_ticket(self,item_type,blackboard):
        return {"main": f"每次战斗结束时，在掉落物中增加{math.floor(blackboard['count'])}个随机招募券。"}
    
    # 战斗中获得临时生命值
    def rogue_level_life_point_add(self,item_type,blackboard):
        if "trig_type" in blackboard:
            timing = self.analyze_timing(item_type,blackboard)
            return {"main" : f"{timing}，战斗开始时获得{blackboard['value']}点本局专用的生命值（会影响国王套判断）"}
        return {"main" : f"战斗开始时获得{blackboard['value']}点本局专用的生命值（会影响国王套判断）"}
    #----------------------------------------
    # 普通效果
    #----------------------------------------
    # 角色属性乘法藏品符文
    def rogue_char_attribute_mul(self,item_type,blackboard):
        modifiers = []
        for key,value in blackboard.items():
            if key.upper() in ANNE_DICTIONARY["attribute"]: # 属性字典里存了所有属性类型
                name = read_dictionary("attribute",key.upper())
                power = to_delta_percent(value) # +/-X%
                modifiers.append(f"{name}{power}(藏品符文)")
        # 选择器目标处理
        selector = self.analyze_selector(blackboard,"我方")
        return {"main" : f"{selector}"+"、".join(modifiers)}

    # 角色属性加法藏品符文
    def rogue_char_attribute_add(self,item_type,blackboard):
        modifiers = []
        for key,value in blackboard.items():
            if key.upper() in ANNE_DICTIONARY["attribute"]: # 属性字典里存了所有属性类型
                name = read_dictionary("attribute",key.upper())
                num = to_delta(value) # +/-X
                modifiers.append(f"{name}{num}(藏品符文)")
        # 选择器目标处理
        selector = self.analyze_selector(blackboard,"我方")
        return {"main" : f"{selector}"+"、".join(modifiers)}

    # 依照持有的“物品”数量增加角色属性
    def rogue_layer_char_attribute_add(self,item_type,blackboard):
        need_item_key = blackboard["stack_by_res"]
        need_item = ask_bena("rogue_item",need_item)
        need_var = math.floor(blackboard["stack_by_res_cnt"])
        modifiers = []
        for key,value in blackboard.items():
            if key.upper() in ANNE_DICTIONARY["attribute"]: # 属性字典里存了所有属性类型
                name = read_dictionary("attribute",key.upper())
                num = to_delta(value) # +/-X
                modifiers.append(f"{name}{num}(藏品符文)")
        # 选择器目标处理
        selector = self.analyze_selector(blackboard,"我方")
        return {
            "main" : f"每有{need_var}个 {need_item}（向下取整），{selector}"+"、".join(modifiers),
            "link" : need_item_key
        }

    # 特定情况下的奖励增加
    #def rogue_up_reward(self,item_type,blackboard):
    #    timing = "未知时机"
    #    if blackboard["mask"] == "battle":
    #        timing = "战斗胜利时"
    
    #----------------------------------------
    # 常规全局Buff的拆分解析（gbn）
    #----------------------------------------
    # 敌方最大生命值最终下降
    def gbn_enemy_max_hp_down(self,item_type,blackboard):
        power = to_delta_percent(blackboard["max_hp"])
        return {"main" : f"环境效果：敌方最大生命值×{power}(终乘)"}   

    # 敌方防御力最终下降
    def gbn_enemy_def_down(self,item_type,blackboard):
        power = to_percent(blackboard["def"],True)
        return {"main" : f"环境效果：敌方防御力×{power}(终乘)"}

    # 敌方攻击力最终下降
    def gbn_enemy_atk_down(self,item_type,blackboard):
        power = to_percent(blackboard["atk"],True)
        return {"main" : f"环境效果：敌方攻击力×{power}(终乘)"}

    # 敌方变轻
    def gbn_enemy_lighter(self,item_type,blackboard):
        power = to_delta(blackboard["mass_level"])
        return {"main" : f"环境效果：敌方重量等级{power}(直加)"}

    # 湖中神盾
    def gbn_rogue_3_increaseMaxHPWhenHavingShield(self,item_type,blackboard):
        power = to_delta_percent(blackboard["mass_level"])
        return {"main" : f"环境效果：开始战斗时若有护盾，所有我方单位{power}(直乘)"}

    # 城墙之子
    def gbn_rogue_4_finalDefense_end_tile(self,item_type,blackboard):
        hp_power = to_delta_percent(blackboard["max_hp"])
        block_power = to_delta(blackboard["block_cnt"])
        target = self.analyze_selector(blackboard,"我方")
        return {
            "main" : f"环境效果：给予位于保护目标点及其周围八格的{target}增益Buff：",
            "children" : [
                {"main" : f"最大生命值{hp_power}(直乘)、阻挡数{block_power}(直加)、"}
            ]
        }

ANNE_NODE = AnneNode()
ANNE_RELIC = AnneRelic()
#----------------------------------------
#以下是供调用的方法
#----------------------------------------

# 查字典方法
# 如果查不到会返回原文
def read_dictionary(catalogue,type_str):
    return ANNE_DICTIONARY[catalogue].get(type_str,type_str)

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

# 翻译一整个BuffTemplate
def translate_whole_buff_template(buff_template: BuffTemplate):
    print("[安妮]尝试翻译Buff模板 "+buff_template.buff_key)
    translation = {
        "main" : f"{buff_template.display_name}（{buff_template.buff_key}）",
        "children" : []
    }
    if buff_template.on_event_priority != "DEFAULT":
        translation["description"] = "事件优先级："+buff_template.on_event_priority
    # 逐个事件进行翻译
    for event in buff_template.events:
        event_key = event.event_key
        event_name = read_dictionary("event",event_key)
        event_translation = {
            "main" : f"{event_name}（{event_key}）",
            "children" : []
        }
        # 逐个节点翻译
        for node in event.node_list:
            # 特别处理一下这个Node：IfNot，效果是反转前面的处理状态
            if len(event_translation["children"]) > 0 and node.node_name == "IfNot" :
                if "true" in event_translation["children"][-1] and "false" in event_translation["children"][-1]:
                    true_flag = event_translation["children"][-1]["true"]
                    false_flag = event_translation["children"][-1]["false"]
                    event_translation["children"][-1]["true"] = false_flag
                    event_translation["children"][-1]["false"] = true_flag
                elif "true" in event_translation["children"][-1]:
                    event_translation["children"][-1]["false"] = event_translation["children"][-1]["true"] 
                    event_translation["children"][-1]["true"] = "若非\""+event_translation["children"][-1]["true"]+"\"" 
                else: # 拿来检查前面处理不了？
                    event_translation["children"].append({"main" : "若前面的逻辑无法处理"})
            else:
                event_translation["children"].append(ANNE_NODE.translate(node))
        translation["children"].append(event_translation)
    return translation

LINE_LIMIT = 40
# 翻译一整个RogueItem
def translate_whole_rogue_item(rogue_item: RogueItem):
    print(f"[安妮]尝试翻译{rogue_item.display_type} {rogue_item.display_name}（{rogue_item.item_key}）")
    translation = {
        "main" : f"{rogue_item.display_name}（{rogue_item.item_key}）",
        "children" : []
    }
    # 展示原始的文案
    if rogue_item.item_info["description"] != None:
        description_lines = rogue_item.item_info["description"].splitlines()
        for description_line in description_lines:
            if len(description_line) > LINE_LIMIT:
                while(len(description_line) > LINE_LIMIT): #强制自动换行
                    translation["children"].append({"main" : description_line[:LINE_LIMIT]})
                    description_line = description_line[LINE_LIMIT:]
            translation["children"].append({"main" : description_line})
    
    # 类型和稀有度
    translation["children"].append({"main" : "类型 : " + rogue_item.display_type + " | "+rogue_item.type})
    translation["children"].append({"main" : "稀有度 : " + rogue_item.item_info["rarity"]}) # 需翻译
    
    # 界园的钱始终有两套，加个超链接
    if rogue_item.type == "COPPER_BUFF":
        another_key = rogue_item.item_key.replace("copper_buff","copper")
        if ask_bena(rogue_item,another_key) != None:
            translation["children"].append({"main" : f"（这里的鹰文可能与游戏内有出入，文案用的钱请见  {another_key}）","link" : another_key})
    elif rogue_item.type == "COPPER":
        another_key = rogue_item.item_key.replace("copper","copper_buff")
        if ask_bena(rogue_item,another_key) != None:
            translation["children"].append({"main" : f"（这是展示文案用的钱，钱的实际效果请见 {another_key}）","link" : another_key})

    # 藏品效果或解释的原文
    if rogue_item.item_info["usage"] != None:
        usage = {"main" : rogue_item.display_type+"鹰文：","children": []}
        usage_lines = rogue_item.item_info["usage"].splitlines()
        for usage_line in usage_lines:
            if len(usage_line) > LINE_LIMIT:
                while(len(usage_line) > LINE_LIMIT): #强制自动换行
                    usage["children"].append({"main" : usage_line[:LINE_LIMIT]})
                    usage_line = usage_line[LINE_LIMIT:]
            usage["children"].append({"main" : usage_line})
        translation["children"].append(usage)
    
    # 效果文本
    if rogue_item.has_effect:
        effect_translation = {
            "main" : rogue_item.display_type+"效果：",
            "children" : []
        }
        # 逐个效果翻译
        for effect in rogue_item.effect_list:
            effect_translation["children"].append(ANNE_RELIC.translate(effect))
        translation["children"].append(effect_translation)

    return translation