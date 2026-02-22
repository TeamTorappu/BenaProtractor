'''
安妮 - 翻译组件
将得到的topic类或buff的node类根据翻译数据转写成对应“人类语”
'''
import json
import math
from data_class import *

ANNE_NODE = None
ANNE_RELIC = None
ANNE_DICTIONARY_PATH = "./translation/anne_dictionary.json"
ANNE_DICTIONARY = None

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
            return buff_key+"(数据库)"
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
        # 异常效果
        if len(attrs["abnormalFlags"]) > 0:
            for flag in attrs["abnormalFlags"]:
                flag_name = read_dictionary("abnormal",flag)
                features.append(flag_name)
                # 包含可抵抗状态
                if flag in ["STUNNED","COLD","FROZEN"]:
                    has_resistable_flag = True
        # 异常免疫
        if len(attrs["abnormalImmunes"]) > 0:
            for flag in attrs["abnormalImmunes"]:
                flag_name = read_dictionary("abnormal",flag)
                features.append(flag_name+"免疫")
        # 异常反制
        if len(attrs["abnormalAntis"]) > 0:
            for flag in attrs["abnormalAntis"]:
                flag_name = read_dictionary("abnormal",flag)
                features.append(flag_name+"反制")
        # 异常组合
        if len(attrs["abnormalCombos"]) > 0:
            for combo in attrs["abnormalCombos"]:
                combo_name = read_dictionary("abnormal",combo)
                features.append(combo_name)
        # 异常组合免疫
        if len(attrs["abnormalImmunes"]) > 0:
            for combo in attrs["abnormalImmunes"]:
                combo_name = read_dictionary("abnormal",combo)
                features.append(combo_name+"免疫")
        # 属性加成（四 则 运 算）
        if len(attrs["attributeModifiers"]) > 0:
            for modify in attrs["attributeModifiers"]:
                attr_name = read_dictionary("attribute",modify["attributeType"])
                formula = modify["formulaItem"]
                value = modify["value"]
                value_str = ""
                # 获取数据加成/减少的写法
                if modify["loadFromBlackboard"]: # 读取自黑板，那value本身没用了
                    value_str = "X"
                elif modify["fetchBaseValueFromSourceEntity"]: # 自本尊，那value本身没用了
                    value_str = "(来源同值)"
                elif formula == "FINAL_SCALER": # yj的小巧思会让终乘在负的情况下+1，实际徒增学习和排错成本
                    value_str = to_hundred_percent(value,False,True)
                elif formula == "MULTIPLIER": # 直乘就没有这种小巧思
                    value_str = to_hundred_percent(value,True)
                else: # 剩下两个只看正负号
                    value_str = str(value) if value < 0 else f"+{value}"
                # 根据算法
                if formula == "ADDITION" :
                    features.append(attr_name+str(value))
                elif formula == "MULTIPLIER" :
                    features.append(attr_name+value_str)
                elif formula == "FINAL_ADDITION" :
                    features.append(attr_name+value_str+"(终加)")
                elif formula == "FINAL_SCALER" :
                    features.append(attr_name+"×"+value_str+"(终乘)")
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
    # 效果类Node
    #----------------------------------------
    # 创建Buff
    def node_CreateBuff(self,node):
        # 未解析参数：_useSpecialBuffSource _specialBuffSource _finishDerivedBuffIfParentFinish
        target_name = read_dictionary("target",node["_buffOwner"])
        if node["_isDerivedBuff"]:
            return {
                "main" : f"为{target_name}创建本Buff的子Buff：",
                "children" : [self.analyze_buff(node['_buff'])]
            }
        else:
            return {
                "main" : f"为{target_name}创建Buff：",
                "children" : [self.analyze_buff(node['_buff'])]
            }

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
        default_atk_scale = to_hundred_percent(node["_defaultAtkScale"])
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
            return {"main" : "（无效节点）"}

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
                method = getattr(self, "gbn_"+buff_key, "")
                if method != "" :
                    rogue_effect.translation = method(rogue_effect.blackboard)
                    return rogue_effect.translation
                else: # 无法翻译，把所有数据搓成可阅读的格式
                    rogue_effect.translation = {
                        "main" : "常规全局Buff - "+buff_key+"（未翻译）",
                        "style_closed" : True,
                        "children" : []
                    }
                    for key,bb in rogue_effect.blackboard.items():
                        rogue_effect.translation["children"].append({"main": str(key) + " : "+str(bb)})
            else: # 其他的效果
                method = getattr(self, "rogue_"+effect_key, "")
                if method != "" :
                    rogue_effect.translation = method(rogue_effect.blackboard)
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
    
    # 职业筛选的处理
    # 返回字符串。说明筛选的职业以及“干员”和“召唤物”这样的称呼
    def analyze_profession(self,profession_mask):
        profession_mask = profession_mask.upper()
        if "," in profession_mask:
            masked_list = profession.split(",")
            # 如果大于等于8职业的话有可能是用于筛所有干员的，进行缩减处理
            if len(masked_list) >= 8 and "PIONEER" in masked_list and "WARRIOR" in masked_list and "TANK" in masked_list and "SNIPER" in masked_list and "CASTER" in masked_list and "SUPPORT" in masked_list and "MEDIC" in masked_list and "SPECIAL" in masked_list:
                    if "TOKEN" in masked_list and "TRAP" in masked_list:
                        return "干员、召唤物、装置"
                    elif "TOKEN" in masked_list:
                        return "干员、召唤物"
                    else: #elif "TRAP" in masked_list:
                        return "干员、装置"
            else:
                professions = []
                objects = []
                for masked in masked_list:
                    if mask in ["TOKEN","TRAP"]:
                        objects.append(read_dictionary("profession",mask))
                    else:
                        professions.append(read_dictionary("profession",mask))
                return "、".join(["/".join(professions)+"干员"] + objects)
    
    #----------------------------------------
    # 普通效果
    #----------------------------------------
    def rogue_char_attribute_mul(self,blackboard):
        modifiers = []
        if "max_hp" in blackboard:
            power = to_hundred_percent(blackboard["max_hp"],True)
            modifiers.append(f"最大生命值{sign}{power}(藏品符文)")
        if "atk" in blackboard:
            power = to_hundred_percent(blackboard["atk"],True)
            modifiers.append(f"攻击力{sign}{power}(藏品符文)")
        if "def" in blackboard:
            power = to_hundred_percent(blackboard["def"],True)
            modifiers.append(f"防御力{sign}{power}(藏品符文)")
        if "magic_resistance" in blackboard:
            power = to_hundred_percent(blackboard["magic_resistance"],True)
            modifiers.append(f"法术抗性{sign}{power}(藏品符文)")
        # 职业筛选处理，没有默认全部我方单位
        if "profession" in blackboard:
            target_name = analyze_profession(blackboard.profession)
            return {"main" : "我方"+target_name+"、".join(modifiers)}
        return {"main" : "全部我方单位"+"、".join(modifiers)}
    
    #----------------------------------------
    # 常规全局Buff的拆分解析（gbn）
    #----------------------------------------
    # 敌方最大生命值最终下降
    def gbn_enemy_max_hp_down(self,blackboard):
        power = to_hundred_percent(blackboard["max_hp"],False,True)
        return {"main" : f"常规全局Buff - 敌方最大生命值×{power}"}   

    # 敌方防御力最终下降
    def gbn_enemy_def_down(self,blackboard):
        power = to_hundred_percent(blackboard["def"],False,True)
        return {"main" : f"常规全局Buff - 敌方防御力×{power}"}

    # 敌方攻击力最终下降
    def gbn_enemy_atk_down(self,blackboard):
        power = to_hundred_percent(blackboard["atk"],False,True)
        return {"main" : f"常规全局Buff - 敌方防御力×{power}"}

ANNE_NODE = AnneNode()
ANNE_RELIC = AnneRelic()
#----------------------------------------
#以下是供调用的方法
#----------------------------------------

# 查字典方法
# 如果查不到会返回原文
def read_dictionary(catalogue,type_str):
    return ANNE_DICTIONARY[catalogue].get(type_str,type_str)

# 将数值加成改成+/-百分比格式，如果结尾是.0还会自动删去
# 可以要求提供正负符号，当然负数本来就有符号。
def to_hundred_percent(power_value,need_sign=False,negative_need_plus_one=False):
    percent_value = power_value * 100
    # 如果为负则加一的可选项
    if negative_need_plus_one and percent_value < 0:
        percent_value += 100
    # 去无意义小数
    if percent_value == math.floor(percent_value): 
        percent_value = int(percent_value)
    # 检查正负
    if need_sign:
        # 提供符号
        if percent_value < 0:
            return str(percent_value)+"%"
        else:
            return "+"+str(percent_value)+"%"
    else:
        # 不提供符号，外部应该会自己加上符号，因此负数要打个括号
        if percent_value < 0:
            return "("+str(percent_value)+")%"
        else:
            return str(percent_value)+"%"

# 翻译一整个BuffTemplate
def translate_whole_buff_template(buff_template: BuffTemplate):
    print("[安妮]尝试翻译Buff模板 "+buff_template.buff_key)
    translation = {
        "main" : buff_template.buff_key,
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

# 翻译一整个RogueItem
def translate_whole_rogue_item(rogue_item: RogueItem):
    print("[安妮]尝试翻译肉鸽道具 "+rogue_item.item_key)
    translation = {
        "main" : f"{rogue_item.display_name}（{rogue_item.item_key}）",
        "children" : []
    }
    # 展示原始的文案
    translation["children"].append({"main" : rogue_item.item_info["description"]})
    translation["children"].append({"main" : "类型:"+rogue_item.display_type})
    translation["children"].append({"main" : "稀有度:"+rogue_item.item_info["rarity"]}) # 需翻译
    # 翻译藏品效果
    if rogue_item.is_relic:
        #原文
        effect_origin = {
            "main" : "藏品鹰文：",
            "children": []
        }
        useage_lines = rogue_item.item_info["usage"].splitlines()
        for useage_line in useage_lines:
            effect_origin["children"].append({"main" : useage_line})
        translation["children"].append(effect_origin)
        #翻译后
        effect_translation = {
            "main" : "藏品效果：",
            "children" : []
        }
        # 逐个效果翻译
        for effect in rogue_item.effect_list:
            effect_translation["children"].append(ANNE_RELIC.translate(effect))
        translation["children"].append(effect_translation)
    return translation