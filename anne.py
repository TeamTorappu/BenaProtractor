#----------------------------------------
# 安妮 - 翻译组件
# 将得到的topic类或buff的node类根据翻译数据转写成对应“人类语”
#----------------------------------------
import math
import traceback
from data_class import *
from bena import ask_bena, translate_buff_name
from analyzer import analyze_selector_target_options_override, analyze_relic_timing, analyze_buff, analyze_deckbuff, analyze_target_options_side, analyze_target_options_conditions
from dictionary import anne_dictionary, get_anne_dictionary

ANNE_NODE = None
ANNE_RELIC = None
ANNE_RUNE = None

DEX = "①②③④⑤⑥⑦⑧⑨"


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
    import node_translator as translator
    def __init__(self):
        print("[安妮]嗯。")
        
    # 翻译重定向器，本质switch case
    # 翻译返回的结果始终是一层一层的结构体
    def translate(self,node,blackboard={}):
        node_name = node.node_name
        #print(f"[安妮]尝试翻译节点 {node_name}")
        method = getattr(self.translator, node_name, "")
        translation = None
        try:
            if method != "" :
                translation = method(node.node_data,blackboard)
                # 检查是否有需要嵌套翻译的内容
                if "sub_nodes" in translation:
                    sub_content_list = []
                    for sub_content in translation["sub_nodes"]:
                        sub_content_list.append(Node(sub_content))
                    if "children" not in translation:
                        translation["children"] = []
                    translation["children"] += self.translate_all(sub_content_list,blackboard)["children"]
                    del translation["sub_nodes"]
            else: # 无法翻译，把所有数据搓成可阅读的格式
                children = []
                for key,content in node.node_data.items():
                    if isinstance(content,dict): # 如果是子节点或者buff，还是要嵌套翻译一下试试的
                        if "attributes" in content: # buff
                            buff = analyze_buff(content,blackboard)
                            buff["main"] = str(key) + " : " + buff["main"]
                            children.append(buff)
                        elif "$type" in content: # 子节点
                            sub_node = self.translate(Node(content),blackboard)
                            sub_node["main"] = str(key) + " : " + sub_node["main"]
                            children.append(sub_node)
                        else: # 解析不了没办法
                            children_children = []
                            for skey,scontent in content.items():
                                children_children.append({"main" : str(skey) + " : " + str(scontent)})
                            if len(children_children) > 0:
                                children.append({
                                    "main" : str(key) + " : {",
                                    "children" : children_children
                                })
                                children.append({"main" : "}"})
                            else:
                                children.append({"main" : str(key) + " : {}"})
                    elif isinstance(content,list): # 可能是子节点列表或者buff列表？
                        if len(content) > 0 and "$type" in content[0]: # 子节点列表
                            sub_content_list = []
                            for sub_content in content:
                                new_node = Node(sub_content)
                                if new_node != None:
                                    sub_content_list.append(new_node)
                            sub_node_list = self.translate_all(sub_content_list,blackboard)
                            sub_node_list["main"] = str(key) + " : " + sub_node_list["main"]
                            children.append(sub_node_list)
                        elif len(content) > 0 and "attributes" in content[0]: # 附属Buff列表
                            children_children = []
                            for scontent in content:
                                children_children.append(self.translator.analyze_buff(scontent,blackboard))
                            children.append({
                                "main" : str(key) + " : [",
                                "children" : children_children
                            })
                            children.append({"main" : "]"})
                        elif len(content) > 0:
                            children_children = []
                            for scontent in content:
                                children_children.append({"main" : str(scontent)})
                            children.append({
                                "main" : str(key) + " : [",
                                "children" : children_children
                            })
                            children.append({"main" : "]"})
                        else:
                            children.append({"main" : str(key) + " : []"})
                    elif key == "$type":
                        children.append({"main": node.node_name})
                    else:
                        children.append({"main": str(key) + " : " + str(content)})
                translation = {
                    "main" : node_name+"（未翻译）",
                    "style_closed" : True,
                    "children" : children
                }
        except Exception as e:
            print(f"[安妮]... {node_name} 节点翻译失败了")
            traceback.print_exc()
            translation = {
                "main" : node_name+"（翻译失败）",
                "style_closed" : True,
            }
        # 返回译文
        return translation
    
    # 全部翻译，包含对一些上下文Node的特殊处理
    def translate_all(self,node_list,blackboard=None):
        children = []
        for node in node_list:
            # IfNot：反转前面的处理状态
            if len(children) > 0 and node.node_name == "IfNot" :
                if "reversed" not in children[-1] or not children[-1]["reversed"]: # 已经翻转过不要再反转
                    if "true" in children[-1] and "false" in children[-1]:
                        children[-1]["true"], children[-1]["false"] = children[-1]["false"], children[-1]["true"]
                        children[-1]["reversed"] = True
                    elif "true" in children[-1]:
                        children[-1]["false"] = children[-1]["true"] 
                        children[-1]["true"] = "若非\""+children[-1]["true"]+"\"" 
                        children[-1]["reversed"] = True
                    else: # 拿来检查前面处理不了？
                        children.append({"main" : "若前面的逻辑无法处理"})
            elif node.node_name == "IfElse":
                children.append(self.translate_ifelse(node,blackboard))
            elif node.node_name == "IfConditions":
                children.append(self.translate_ifconditions(node,blackboard))
            else:
                children.append(self.translate(node,blackboard))
        # 最后一项打上标记
        if len(children) > 0:
            children[len(children)-1]["last_one"] = True
        return {"main" : "","children" : children}
    
    # IfElse的特殊处理
    def translate_ifelse(self,node,blackboard):
        if node.translation == None:
            node_data = node.node_data
            # 判断节点
            true_flag = "如果是/有/可行/可处理："
            false_flag = "如果不是/没有/不可行/无法处理："
            if node.condition_nodes == None:
                return {"main" : "无效的判断节点"}
            struct = self.translate(node.condition_nodes[0],blackboard)
            if struct["main"].endswith("（未翻译）"): # 未翻译，增加标识符
                struct["main"] = "尝试判断: "+struct["main"]
            # 若main是空的，补一个尝试判断
            if struct["main"] == "":
                if "true" in struct:
                    struct["main"] = "尝试判断："+struct["true"]
                elif "false" in struct:
                    struct["main"] = "尝试判断："+struct["false"]
                else:
                    struct["main"] = "尝试进行未知的判断"
            # 因为IfElse只影响内圈，对外圈逻辑不影响，修改逻辑
            if "true" in struct:
                 true_flag = struct["true"]+"："
                 struct.pop("true") 
            if "false" in struct:
                 false_flag = struct["false"]+"："
                 struct.pop("false")
            if "children" not in struct:
                struct["children"] = []
            if "style_closed" in struct:
                del struct["style_closed"]
            # 成功时执行的节点
            if node.succeed_nodes != None and len(node.succeed_nodes) > 0:
                success_translation = self.translate_all(node.succeed_nodes,blackboard)
                if true_flag.endswith("时"):
                    success_translation["main"] = true_flag
                else:
                    success_translation["main"] = "若" + true_flag
                struct["children"].append(success_translation)
            # 失败时执行的节点
            if node.fail_nodes != None and len(node.fail_nodes) > 0:
                fail_translation = self.translate_all(node.fail_nodes,blackboard)
                if false_flag.endswith("时"):
                    fail_translation["main"] = false_flag
                else:
                    fail_translation["main"] = "若" + false_flag
                struct["children"].append(fail_translation)
            # 存储翻译
            node.translation = struct
            return struct
        else:
            return node.translation
    
    # IfConditions的特殊处理
    def translate_ifconditions(self,node,blackboard):
        if node.translation == None:
            node_data = node.node_data
            # 检查条件数量
            if node.condition_nodes == None:
                return {"main" : "无效的判断节点"}
            if len(node.condition_nodes) == 1: # 如果只有一个，那你tmd为什么不用IfElse呢？？？
                return self.translate_ifelse(node,blackboard)
            # 判断节点
            struct = {
                "main" : "",
                "children" : []
            }
            structs = []
            true_flag = "如果是/有/可行/可处理："
            false_flag = "如果不是/没有/不可行/无法处理："
            #开始处理
            for sub_node in node.condition_nodes:
                structs.append(self.translate(sub_node))
            true_flags = []
            false_flags = []
            index = 0
            for _struct in structs:
                if _struct["main"] == "":
                    if "true" in _struct:
                        _struct["main"] = "检查：" + _struct["true"]
                    elif "false" in _struct:
                        _struct["main"] = "检查：" + _struct["false"]
                    else:
                        _struct["main"] = "进行未知的检查"
                _struct["main"] = DEX[index] + _struct["main"]
                if "true" in _struct:
                    text = _struct["true"]
                    text = DEX[index] + text
                    true_flags.append(text)
                    del _struct["true"]
                else:
                    true_flags.append(_struct["main"]+"处理成功")
                if "false" in _struct:
                    text = _struct["false"]
                    text = DEX[index] + text
                    false_flags.append(text)
                    del _struct["false"]
                else:
                    false_flags.append(_struct["main"]+"处理成功")
                index += 1
            # IfConditions同样只影响内圈，对外圈逻辑不影响
            if node_data["_isAnd"]:
                struct["main"] = "尝试判断多个条件，是否同时满足："
                true_flag = "若 " + " 且 ".join(true_flags)+"："
                false_flag = "若 " + " 或 ".join(false_flags)+"："
            else:
                struct["main"] = "尝试判断多个条件，是否满足其中任意一个："
                true_flag = "若 " + " 或 ".join(true_flags)+"："
                false_flag = "若 " + " 且 ".join(false_flags)+"："
            # 条件节点
            struct["children"] += structs
            # 成功时执行的节点
            if node.succeed_nodes != None and len(node.succeed_nodes) > 0:
                success_translation = self.translate_all(node.succeed_nodes,blackboard)
                success_translation["main"] = true_flag
                struct["children"].append(success_translation)
            # 失败时执行的节点
            if node.fail_nodes != None and len(node.fail_nodes) > 0:
                fail_translation = self.translate_all(node.fail_nodes,blackboard)
                fail_translation["main"] = false_flag
                struct["children"].append(fail_translation)
            # 存储翻译
            node.translation = struct
            return struct
        else:
            return node.translation

'''
#----------------------------------------
# 安妮的藏品翻译器
#----------------------------------------
'''
class AnneRelic:
    import relic_translator as translator
    def __init__(self):
        _ = None
        
    # 翻译重定向器，本质switch case
    # 翻译返回的结果始终是一层一层的结构体
    def translate(self,rogue_effect):
        effect_key = rogue_effect.key
        print(f"[安妮]尝试翻译藏品 {effect_key}")
        method = getattr(self.translator, effect_key, "")
        if method != "" :
            translation = method(rogue_effect.type,rogue_effect.blackboard)
            if "global_buff" in translation: # 翻译全局Buff
                # 尝试寻找全局Buff
                gbuff = ask_bena("global_buff",translation["global_buff"])
                if gbuff != None:
                    gbuff_translation = translate_whole_global_buff(gbuff,rogue_effect.blackboard)
                    gbuff_translation["main"] = "战斗中："
                    if len(translation["children"]) > 0:
                        translation["children"][0]["style_closed"] = True
                        translation["children"] = gbuff_translation["children"] + translation["children"]
                    else:
                        translation["children"] += gbuff_translation["children"]
            return translation
        else: # 无法翻译，把所有数据搓成可阅读的格式
            prefix = analyze_relic_timing(rogue_effect.type,rogue_effect.blackboard)
            translation = {
                "main" : prefix+effect_key+"（未翻译）",
                "style_closed" : True,
                "children" : []
            }
            for key,bb in rogue_effect.blackboard.items():
                translation["children"].append({"main": str(key) + " : "+str(bb)})
        # 返回译文
        return translation
    
    # 全部翻译
    def translate_all(self,rogue_effect_list):
        children = []
        for rogue_effect in rogue_effect_list:
            translation = self.translate(rogue_effect)
            children.append(translation)
        return {"main" : "","children" : children}

'''
#----------------------------------------
# 安妮的符文翻译器
#----------------------------------------
'''
class AnneRune:
    import rune_translator as translator
    def __init__(self):
        _ = None
        
    # 翻译重定向器，本质switch case
    # 翻译返回的结果始终是一层一层的结构体
    def translate(self,rune_info):
        rune_key = rune_info.key
        print(f"[安妮]尝试翻译符文 {rune_key}")
        method = getattr(self.translator, rune_key, "")
        if method != "" :
            translation = method(rune_info.selector,rune_info.blackboard)
    
    # 全部翻译
    def translate_all(self,rune_info_list):
        children = []
        for rune_info in rune_info_list:
            translation = self.translate(rune_info)
            children.append(translation)
        return {"main" : "","children" : children}

ANNE_NODE = AnneNode()
ANNE_RELIC = AnneRelic()
ANNE_RUNE = AnneRune()
#----------------------------------------
#以下是供调用的方法
#----------------------------------------

# 翻译一整个Buff
def translate_whole_buff(buff: Buff,blackboard: dict = {}):
    print("[安妮]尝试翻译Buff "+buff.buff_key)
    translation = analyze_buff(buff.buff_data,blackboard,True)
    # 如果内部有自己的小巧思BuffKey
    if buff.buff_key != buff.buff_data["buffKey"]: 
        translation["description"] = "这个Buff的卡名在规则上被视为 <"+buff.buff_data["buffKey"]+"> "
        if "（" in translation["main"]:
            translation["main"] = buff.buff_key + "（" + translation["main"].split("（",1)[1]
        else:
            translation["main"] = buff.buff_key
    # 如果显示名不一样
    if buff.display_name != buff.buff_key:
        if "（" in translation["main"]:
            translation["main"] = f"{buff.display_name}（{buff.buff_key}；" + translation["main"].split("（",1)[1]
        else:
            translation["main"] = f"{buff.display_name}（{buff.buff_key}）"
    # 尝试把buff_template直接显示出来
    if buff.buff_data["templateKey"] != "empty":
        buff_template = ask_bena("buff_template",buff.buff_data["templateKey"])
        if buff_template != None:
            if "children" not in translation:
                translation["children"] = []
            buff_template_translation = translate_whole_buff_template(buff_template,blackboard)
            buff_template_translation["main"] = "机制&效果（Buff模板内容）："
            translation["children"].append(buff_template_translation)
        else:
            translation["children"].append({
                "main" : "机制&效果（Buff模板内容）：（未找到相应名称的Buff模板）"
            })
    return translation

# 翻译一整个GlobalBuff
def translate_whole_global_buff(gbuff: GlobalBuff,blackboard : dict = {}):
    print("[安妮]尝试翻译GlobalBuff "+gbuff.buff_key)
    # 处理翻译
    translation = {
        "main" : gbuff.buff_key,
        "children" : []
    }
    if gbuff.display_name != gbuff.buff_key:
        translation["main"] = f"{gbuff.display_name}（{gbuff.buff_key}）"
    
    # 主类
    if gbuff.prefab_data["m_Script"] == "MonoBehaviour":
        translation["children"].append({"main" : "类：未知"})
    elif gbuff.prefab_data["m_Script"] != "GlobalBuff":
        translation["children"].append({"main" : "类："+gbuff.prefab_data["m_Script"]})
    if gbuff.prefab_data["_overrideCameraEffect"] != "":
        translation["children"].append({"main" : "覆写镜头特效："+gbuff.prefab_data["_overrideCameraEffect"]})
    
    # 目标筛选逻辑
    target = "单位"
    target_options = analyze_selector_target_options_override(gbuff.target_options,blackboard)
    target_side = analyze_target_options_side(target_options,True,gbuff.prefab_data["_sourceType"])
    conditions_list = analyze_target_options_conditions(target_options)
    if target_side != "":
        conditions_list.append(target_side)
    if len(conditions_list) > 3: # 多条件的复杂筛选
        conditions_translation = {"main" : f"生效对象条件：","children" : []}
        for condition in conditions_list:
            if condition.endswith("干员"):
                target = target.replace("单位",condition)
            elif condition == "我方" or condition == "敌方" or condition == "我方/中立":
                target = condition + target
            elif condition == "相同阵营" or condition == "对立阵营":
                my_side = "敌方" if gbuff.prefab_data["_sourceType"] == "ENEMY" else "我方"
                prefixs.append(f"相对于{my_side}而言属"+condition+"且可选的")
            else:
                conditions_translation["children"].append({"main" : condition})
        translation["children"].append(conditions_translation)
        target = "符合条件的" + target
    elif len(conditions_list) > 0:
        prefixs = []
        for condition in conditions_list:
            if condition.endswith("干员"):
                target = target.replace("单位",condition)
            elif condition == "我方" or condition == "敌方" or condition == "我方/中立":
                target = condition + target
            elif condition == "相同阵营" or condition == "对立阵营":
                my_side = "敌方" if gbuff.prefab_data["_sourceType"] == "ENEMY" else "我方"
                prefixs.append(f"相对于{my_side}而言属"+condition+"且可选的")
            elif condition.endswith("的"):
                prefixs.append(condition)
            else:
                prefixs.append(condition+"的")
        target = "、".join(prefixs)+target
    else:
        target = "所有单位"
    # 逐Buff添加至列表
    if len(gbuff.buff_datas) > 0:
        buffs_translation = {
            "main" : f"{target}登场或重生时，获得以下Buff：",
            "children" : []
        }
        for buff_data in gbuff.buff_datas:
            _buff = analyze_buff(buff_data,blackboard)
            if not buff_data["loadFromDB"] and buff_data["templateKey"] != "empty":
                buff_template = ask_bena("buff_template",buff_data["templateKey"])
                if buff_template != None:
                    if "children" not in _buff:
                        _buff["children"] = []
                    buff_template_translation = translate_whole_buff_template(buff_template,blackboard)
                    for _child in buff_template_translation["children"]:
                        _buff["children"].append(_child)
            buffs_translation["children"].append(_buff)
        translation["children"].append(buffs_translation)
    # 逐DeckBuff添加至列表
    if len(gbuff.deck_buff_datas) > 0:
        deck_buffs_translation = {
            "main" : f"为待部署区中符合条件的卡施加以下DeckBuff：",
            "children" : []
        }
        for deck_buff_data in gbuff.deck_buff_datas:
            _buff = analyze_deckbuff(deck_buff_data,blackboard)
            buff_data = deck_buff_data["buff"]
            if not buff_data["loadFromDB"] and buff_data["templateKey"] != "empty":
                buff_template = ask_bena("buff_template",buff_data["templateKey"])
                if buff_template != None:
                    if "children" not in _buff:
                        _buff["children"] = []
                    buff_template_translation = translate_whole_buff_template(buff_template,blackboard)
                    for _child in buff_template_translation["children"]:
                        _buff["children"].append(_child)
            deck_buffs_translation["children"].append(_buff)
        translation["children"].append(deck_buffs_translation)
    # 额外Buff
    if "_extraBuff" in gbuff.prefab_data and len(gbuff.prefab_data["_extraBuff"]) > 0:
        buff_translation = {
            "main" : f"此外，在特定情况下，为所有{target}施加以下Buff：",
            "children" : []
        }
        buff_data = gbuff.prefab_data["_extraBuff"]
        _buff = analyze_buff(buff_data,blackboard)
        if not buff_data["loadFromDB"] and buff_data["templateKey"] != "empty":
            buff_template = ask_bena("buff_template",buff_data["templateKey"])
            if buff_template != None:
                if "children" not in _buff:
                    _buff["children"] = []
                buff_template_translation = translate_whole_buff_template(buff_template,blackboard)
                for _child in buff_template_translation["children"]:
                    _buff["children"].append(_child)
        buff_translation["children"].append(_buff)
        translation["children"].append(buff_translation)
    # Cardbuff
    if "_cardbuffKey" in gbuff.prefab_data:
        card_buff_translation = {
            "main" : f"为待部署区中符合条件的卡施加一个CardBuff：",
            "children" : [{"main" : gbuff.prefab_data["_cardbuffKey"]}]
        }
        translation["children"].append(card_buff_translation)
    # 剩下无法翻译的部分先直接展示
    for key, value in gbuff.prefab_data.items():
        if key not in ["m_Script","_key","_options","_buffs","_deckBuffs","_extraBuff","_cardbuffKey","_sourceType","_overrideCameraEffect"]:
            translation["children"].append(key+" : "+str(value))
    return translation

# 翻译一整个BuffTemplate
def translate_whole_buff_template(buff_template: BuffTemplate,blackboard : dict = {}):
    print("[安妮]尝试翻译Buff模板 "+buff_template.buff_key)
    translation = {
        "main" : buff_template.buff_key,
        "children" : []
    }
    if buff_template.display_name != buff_template.buff_key:
        translation["main"] = f"{buff_template.display_name}（{buff_template.buff_key}）"
    if buff_template.on_event_priority != "DEFAULT":
        priority = anne_dictionary("event_priority",buff_template.on_event_priority)
        translation["children"].append("事件优先级："+priority)
    if buff_template.effect_key != "":
        translation["children"].append("特效："+buff_template.effect_key)
    # 逐个事件进行翻译
    for event in buff_template.events:
        event_key = event.event_key
        event_name = anne_dictionary("buff_event",event_key)
        event_translation = ANNE_NODE.translate_all(event.node_list,blackboard)
        event_translation["main"] = f"{event_name}（{event_key}）"
        translation["children"].append(event_translation)
    return translation

LINE_LIMIT = 60
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
    translation["children"].append({"main" : "类型 : " + rogue_item.display_type + "("+rogue_item.type+"）"})
    translation["children"].append({"main" : "稀有度 : " + rogue_item.item_info["rarity"]}) # 需翻译
    
    # 界园的钱始终有两套，加个超链接
    if rogue_item.type == "COPPER_BUFF":
        another_key = rogue_item.item_key.replace("copper_buff","copper")
        if ask_bena("rogue_item",another_key) != None:
            translation["children"].append({"main" : f"（这里的鹰文可能与游戏内有出入，文案用的钱请见  <rogue_item|{another_key}>）"})
    elif rogue_item.type == "COPPER":
        another_key = rogue_item.item_key.replace("copper","copper_buff")
        if ask_bena("rogue_item",another_key) != None:
            translation["children"].append({"main" : f"（这是展示文案用的钱，钱的实际效果请见 <rogue_item|{another_key}>）"})

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
        effect_translation = ANNE_RELIC.translate_all(rogue_item.effect_list)
        effect_translation["main"] = rogue_item.display_type+"效果："
        translation["children"].append(effect_translation)

    return translation
