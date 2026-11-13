#----------------------------------------
# 操作（伪代码列表）
#----------------------------------------
import traceback
from analyzer.buff import analyze_buff
from anne import node_translator
from anne.node import Node

DEX = "①②③④⑤⑥⑦⑧⑨"

class Action:
    def __init__(self, action_data):
        self.action_data = action_data
        self.node_list = [Node(node_data) for node_data in action_data]
        self.display_name = ""
        self.hidden = False

    # 获取原文
    def get_raw_data(self):
        return self.action_data

    # 翻译
    def translate(self,blackboard={}):
        children = []
        for node in self.node_list:
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
                children.append(self.translate_ifelse_node(node,blackboard))
            elif node.node_name == "IfConditions":
                children.append(self.translate_ifconditions_node(node,blackboard))
            else:
                children.append(node.translate(blackboard))
        # 最后一项打上标记
        if len(children) > 0:
            children[len(children)-1]["last_one"] = True
        return {"main" : "","children" : children}

    # IfElse的特殊处理
    @staticmethod
    def translate_ifelse_node(node,blackboard):
        node_data = node.node_data
        # 判断节点
        true_flag = "如果是/有/可行/可处理："
        false_flag = "如果不是/没有/不可行/无法处理："
        if node_data["_conditionNode"] == None:
            return {"main" : "无效的判断节点"}
        struct = Node(node_data["_conditionNode"]).translate(blackboard)
        if struct["main"].endswith("（未翻译）"): # 未翻译，增加标识符
            struct["main"] = "尝试判断: "+struct["main"]
        # 若main是空的，补一个尝试判断
        elif struct["main"] == "":
            struct["main"] = "尝试判断："

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
        if node_data["_succeedNodes"] != None and len(node_data["_succeedNodes"]) > 0:
            success_translation = Action(node_data["_succeedNodes"]).translate(blackboard)
            if true_flag.endswith("时"):
                success_translation["main"] = true_flag
            else:
                success_translation["main"] = "若" + true_flag
            success_translation["role"] = "condition"
            struct["children"].append(success_translation)
        # 失败时执行的节点
        if node_data["_failNodes"] != None and len(node_data["_failNodes"]) > 0:
            fail_translation = Action(node_data["_failNodes"]).translate(blackboard)
            if false_flag.endswith("时"):
                fail_translation["main"] = false_flag
            else:
                fail_translation["main"] = "若" + false_flag
            fail_translation["role"] = "condition"
            struct["children"].append(fail_translation)
        
        return struct

    # IfConditions的特殊处理
    def translate_ifconditions_node(node,blackboard):
        node_data = node.node_data
        # 检查条件数量
        if node_data["_conditionNodes"] == None or len(node_data["_conditionNodes"]) == 0:
            return {"main" : "无效的判断节点"}
        # 判断节点
        struct = {
            "main" : "",
            "children" : []
        }
        structs = []
        true_flag = "如果是/有/可行/可处理："
        false_flag = "如果不是/没有/不可行/无法处理："
        #开始处理
        for sub_node_data in node_data["_conditionNodes"]:
            structs.append(Node(sub_node_data).translate(blackboard))
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
        if node_data["_succeedNodes"] != None and len(node_data["_succeedNodes"]) > 0:
            success_translation = Action(node_data["_succeedNodes"]).translate(blackboard)
            success_translation["main"] = true_flag
            success_translation["role"] = "condition"
            struct["children"].append(success_translation)
        # 失败时执行的节点
        if node_data["_failNodes"] != None and len(node_data["_failNodes"]) > 0:
            fail_translation = Action(node_data["_failNodes"]).translate(blackboard)
            fail_translation["main"] = false_flag
            fail_translation["role"] = "condition"
            struct["children"].append(fail_translation)

        return struct