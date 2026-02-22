'''
安妮 - 翻译组件
将得到的topic类或buff的node类根据翻译数据转写成对应“人类语”
'''
import math
from data_class import *

ANNE_NODE = None

# 安妮的节点翻译器
class AnneNode:
    def __init__(self):
        print("安妮的节点翻译器已创建")
        
    # 翻译重定向器，本质switch case
    def translate(self,node):
        node_name = node.node_name
        method = getattr(self, "node_"+node_name, "")
        if method != "":
            return method(node.node_data)
        return node_name+"(无法翻译)"
    
    # 解析对象类型的信息
    def analyze_target_type(self,type_str):
        if type_str == "BUFF_OWNER":
            return "持有者"
        elif type_str == "BUFF_SOURCE":
            return "来源"
        else:
            return type_str

    # 解析子Buff的详细信息
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
        if buff_data["templateKey"] != "empty":
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
                flag_name = flag  # 待翻译
                features.append(flag_name)
                # 包含可抵抗状态
                if flag in ["STUNNED","COLD","FROZEN"]:
                    has_resistable_flag = True
        # 异常免疫
        if len(attrs["abnormalImmunes"]) > 0:
            for flag in attrs["abnormalImmunes"]:
                flag_name = flag  # 待翻译
                features.append(flag_name+"免疫")
        # 异常反制
        if len(attrs["abnormalAntis"]) > 0:
            for flag in attrs["abnormalAntis"]:
                flag_name = flag  # 待翻译
                features.append(flag_name+"反制")
        # 异常组合
        if len(attrs["abnormalCombos"]) > 0:
            for combo in attrs["abnormalCombos"]:
                combo_name = combo  # 待翻译
                features.append(combo_name)
        # 异常组合免疫
        if len(attrs["abnormalImmunes"]) > 0:
            for combo in attrs["abnormalImmunes"]:
                combo_name = combo  # 待翻译
                features.append(combo_name+"免疫")
        # 属性加成（四 则 运 算）
        if len(attrs["attributeModifiers"]) > 0:
            for modify in attrs["attributeModifiers"]:
                attr_name = modify["attributeType"]  # 待翻译
                formula = modify["formulaItem"]
                value = modify["value"]
                if formula == "FINAL_SCALER" and value < 0: # yj的小巧思，实际徒增学习和排错成本
                    value = value + 1
                if modify["loadFromBlackboard"]: # 读取自黑板，那value本身没用了
                    value = "X"
                if modify["fetchBaseValueFromSourceEntity"]: # 自本尊，那value本身没用了
                    value = "N"
                # 根据算法
                if formula == "ADDITION":
                    features.append(attr_name+"+"+str(value))
                elif formula == "MULTIPLIER":
                    features.append(attr_name+"+"+str(value)+"%")
                elif formula == "FINAL_ADDITION":
                    features.append(attr_name+"++"+str(value))
                elif formula == "FINAL_SCALER":
                    features.append(attr_name+"x"+str(value)+"%")
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
        if buff_data["overrideKey"] and buff_data["overrideKey"] != "empty":
            results.append(f"处理覆盖时视为{buff_data['overrideKey']}") 
        # 覆写事件优先级
        if buff_data["overrideOnEventPriority"]:
            results.append(f"事件优先级覆写为{buff_data['onEventPriority']}")
        # 持续时间配置
        if buff_data["lifeTimeType"] == "INFINITY":
            results.append("永久")
        elif buff_data["lifeTimeType"] == "LIMITED":
            if buff_data["durationKey"] != "none":
                results.append(f"持续({buff_data['durationKey']})秒")
            elif buff_data["lifeTime"] == 0.0:
                results.append("持续一瞬间")
            else:
                results.append(f"持续{str(buff_data['lifeTime'])}秒")
        # 触发配置
        if buff_data["triggerLifeType"] == "IMMEDIATELY": # 立即触发或不触发
            if buff_data["waitFirstTriggerInterval"] and buff_data["firstTriggerInterval"] >= 0:
                ticks = math.ceil(buff_data['firstTriggerInterval'] * 30)
                results.append(f"{ticks}帧后触发")
            elif buff_data["triggerInterval"] >= 0:
                ticks = math.ceil(buff_data['triggerInterval'] * 30)
                results.append(f"{ticks}帧后触发")
            #else:
            #    results.append("立即触发")
        elif buff_data["triggerLifeType"] == "INFINITY": # 无限次触发
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
        elif buff_data["triggerLifeType"] == "LIMITED": # 有限次触发
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
        if buff_data["overrideType"] != "DEFAULT":
            if buff_data["overrideType"] == "STACK":
                max_stack = buff_data['maxStackCnt']
                if buff_data["refreshRemainingTimeWhenStackMax"]:
                    if buff_data["clearAllStackCntWhenTimeUp"]:
                        results.append(f"可叠加{max_stack}(叠满后仅刷新时间，到时间一次掉完)")
                    else:
                        results.append(f"可叠加{max_stack}(叠满后仅刷新时间，一层一层掉)")
                else:
                    if buff_data["clearAllStackCntWhenTimeUp"]:
                        results.append(f"可叠加{max_stack}(叠满后无法再施加，到时间一次掉完)")
                    else:
                        results.append(f"可叠加{max_stack}(叠满后无法再施加，一层一层掉)")
                
            elif buff_data["overrideType"] == "EXTEND":
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
        # 返回字符串
        return buff_key+"（"+";".join(results)+"）"
    
    # 逻辑 如果+否则
    def node_IfElse(self,node):
        condition_line = ANNE_NODE.translate(node["condition_node"])
        success_node_lines = []
        fail_node_lines = []
        for sub_node in node["succeed_nodes"]:
            success_node_lines.append(ANNE_NODE.translate(sub_node))
        for sub_node in node["fail_nodes"]:
            fail_node_lines.append(ANNE_NODE.translate(sub_node))
        return condition_line+"：\n如果是/有/可行/可处理：\n"+"\n".join(success_node_lines)+"\n\n否则：\n"+"\n".join(fail_node_lines)
    
    # 创建Buff
    def node_CreateBuff(self,node):
        # 未解析参数：_useSpecialBuffSource _specialBuffSource _finishDerivedBuffIfParentFinish
        target_name = self.analyze_target_type(node["_buffOwner"])
        if node["_isDerivedBuff"]:
            return f"为{target_name}创建本Buff的子Buff：{self.analyze_buff(node['_buff'])}"
        else:
            return f"为{target_name}创建Buff：{self.analyze_buff(node['_buff'])}"
    
    # 否则
    def node_IfNot(self,node):
        return "若没有/不是/不行/无法处理"
    
    # 检查是否持有某Buff
    def node_CheckContainsBuff(self,node):
        # 未解析参数：_loadFromBlackboard _checkSourceHost
        target_name = self.analyze_target_type(node["_targetType"])
        if node["isAND"]: # 与模式
            if len(node["_buffKeys"]) > 1:
                if node["_checkBuffSource"]:
                    source_name = self.analyze_target_type(node["_buffSourceType"])
                    return f"检查{target_name}是否同时持有来自{source_name}的 {'、'.join(node['_buffKeys'])}"
                else:
                    return f"检查{target_name}是否同时持有 {'、'.join(node['_buffKeys'])}"
            elif len(node["_buffKeys"]) == 1:
                if node["_checkBuffSource"]:
                    source_name = self.analyze_target_type(node["_buffSourceType"])
                    return f"检查{target_name}是否持有来自{source_name}的 {node['_buffKeys'][0]}"
                else:
                    return f"检查{target_name}是否持有 {node['_buffKeys'][0]}"
        else: # 或模式
            if len(node["_buffKeys"]) > 1:
                if node["_checkBuffSource"]:
                    source_name = self.analyze_target_type(node["_buffSourceType"])
                    return f"检查{target_name}是否持有来自{source_name}的 {'、'.join(node['_buffKeys'])} 中的任意一个"
                else:
                    return f"检查{target_name}是否持有 {'、'.join(node['_buffKeys'])} 中的任意一个"
            elif len(node["_buffKeys"]) == 1:
                if node["_checkBuffSource"]:
                    source_name = self.analyze_target_type(node["_buffSourceType"])
                    return f"检查{target_name}是否持有来自{source_name}的 {node['_buffKeys'][0]}"
                else:
                    return f"检查{target_name}是否持有 {node['_buffKeys'][0]}"

        return "（无效节点）"

    # 触发某个能力
    def node_TriggerAbility(self,node):
        # 未解析参数：_checkCanUseAblityFlag
        target_name = self.analyze_target_type(node["_targetType"])
        ability_name = node["_abilityName"]
        if node["_ownerType"] == node["_targetType"]:
            return f"让{target_name}触发{ability_name}能力"
        else:
            owner_name = self.analyze_target_type(node["_ownerType"])
            return f"让{owner_name}向{target_name}触发{ability_name}能力"
    
    # 检查阵营
    def node_CheckCharacterGroupTag(self,node):
        target_name = self.analyze_target_type(node["_targetType"])
        group_name = node["_groupTag"] # 需要翻译
        return f"检查{target_name}是否具有{group_name}阵营标签"
        

ANNE_NODE = AnneNode()
#----------------------------------------
#以下是供调用的方法

def translate_whole_buff_template(buff_template: BuffTemplate):
    lines = [
        buff_template.buff_key+"：",
        "事件优先级："+buff_template.on_event_priority,
        ""
    ]
    for event in buff_template.events:
        lines.append(f" - 在 {event.event_key} 事件：")
        for node in event.node_list:
            line = ANNE_NODE.translate(node)
            lines += line.splitlines()
        lines.append(f"")
    return lines