'''
安妮 - 翻译组件
将得到的topic类或buff的node类根据翻译数据转写成对应“人类语”
'''
import math
from data_class import *
from bena import ask_bena
from translator import anne_dictionary, get_anne_dictionary

ANNE_NODE = None
ANNE_RELIC = None


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
        self.translator.set_dictionary(get_anne_dictionary())
        print("[安妮]嗯。")
        
    # 翻译重定向器，本质switch case
    # 翻译返回的结果始终是一层一层的结构体
    def translate(self,node):
        node_name = node.node_name
        if node.translation == None:
            print(f"[安妮]尝试翻译节点 {node_name}")
            method = getattr(self.translator, "node_"+node_name, "")
            try:
                if method != "" :
                    node.translation = method(node.node_data)
                else: # 无法翻译，把所有数据搓成可阅读的格式
                    children = []
                    for key,content in node.node_data.items():
                        if isinstance(content,dict): # 如果是子节点或者buff，还是要嵌套翻译一下试试的
                            if "attributes" in content: # buff
                                buff = self.translator.analyze_buff(content)
                                buff["main"] = str(key) + " : " + buff["main"]
                                children.append(buff)
                            elif "$type" in content: # 子节点
                                sub_node = self.translate(Node(content))
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
                                sub_node_list = self.translate_all(sub_content_list)
                                sub_node_list["main"] = str(key) + " : " + sub_node_list["main"]
                                children.append(sub_node_list)
                            elif len(content) > 0 and "attributes" in content[0]: # 子buff列表
                                children_children = []
                                for scontent in content:
                                    children_children.append(self.translator.analyze_buff(scontent))
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
                        else:
                            children.append({"main": str(key) + " : "+str(content)})
                    node.translation = {
                        "main" : node_name+"（未翻译）",
                        "style_closed" : True,
                        "children" : children
                    }
            except Exception as e:
                print(f"[安妮]... {node_name} 节点翻译失败了",e)
                node.translation = {
                    "main" : node_name+"（翻译失败）",
                    "style_closed" : True
                }
        # 返回译文
        return node.translation
    
    # 全部翻译，包含对一些上下文Node的特殊处理
    # 可以选择性的要求返回一个列表
    def translate_all(self,node_list,return_list = False):
        children = []
        for node in node_list:
            # IfNot：反转前面的处理状态
            if len(children) > 0 and node.node_name == "IfNot" :
                if "true" in children[-1] and "false" in children[-1]:
                    true_flag = children[-1]["true"]
                    false_flag = children[-1]["false"]
                    children[-1]["true"] = false_flag
                    children[-1]["false"] = true_flag
                elif "true" in children[-1]:
                    children[-1]["false"] = children[-1]["true"] 
                    children[-1]["true"] = "若非\""+children[-1]["true"]+"\"" 
                else: # 拿来检查前面处理不了？
                    children.append({"main" : "若前面的逻辑无法处理"})
            elif node.node_name == "IfElse":
                children.append(self.translate_ifelse(node))
            else:
                children.append(self.translate(node))
        if return_list:
            return children
        else:
            return {"main" : "","children" : children}
    
    # IfElse的特殊处理
    def translate_ifelse(self,node):
        if node.translation == None:
            node_data = node.node_data
            # 判断节点
            struct = self.translate(node_data["condition_node"])
            if struct["main"].endswith("（未翻译）"): # 未翻译，增加标识符
                struct["main"] = "尝试判断: "+struct["main"]
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
            if len(node_data["succeed_nodes"]) > 0:
                success_translation = self.translate_all(node_data["succeed_nodes"])
                success_translation["main"] = true_flag
                struct["children"].append(success_translation)
            # 失败时执行的节点
            fail_node_lines = []
            if len(node_data["fail_nodes"]) > 0:
                fail_translation = self.translate_all(node_data["fail_nodes"])
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
        self.translator.set_dictionary(get_anne_dictionary())
        #print("[安妮]好的。")
        
    # 翻译重定向器，本质switch case
    # 翻译返回的结果始终是一层一层的结构体
    def translate(self,rogue_effect):
        if rogue_effect.translation == None:
            effect_key = rogue_effect.key
            print(f"[安妮]尝试翻译藏品效果 {effect_key}")
            # 全局buff有二级结构所以拆开来解析
            if effect_key == "global_buff_normal": 
                buff_key = rogue_effect.blackboard["key"] # 这个才是buff的名字
                method = getattr(self.translator, "gb_"+buff_key.replace("[","_").replace("]",""), "")
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
                method = getattr(self.translator, "rogue_"+effect_key, "")
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
    
    # 全部翻译
    # 可以选择性的要求返回一个列表
    def translate_all(self,rogue_effect_list,return_list = False):
        children = []
        for rogue_effect in rogue_effect_list:
            children.append(self.translate(rogue_effect))
        if return_list:
            return children
        else:
            return {"main" : "","children" : children}


ANNE_NODE = AnneNode()
ANNE_RELIC = AnneRelic()
#----------------------------------------
#以下是供调用的方法
#----------------------------------------

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
        event_name = anne_dictionary("event",event_key)
        event_translation = ANNE_NODE.translate_all(event.node_list);
        event_translation["main"] = f"{event_name}（{event_key}）"
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
        effect_translation = ANNE_RELIC.translate_all(rogue_item.effect_list)
        effect_translation["main"] = rogue_item.display_type+"效果："
        translation["children"].append(effect_translation)

    return translation