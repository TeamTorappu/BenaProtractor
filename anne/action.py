#----------------------------------------
# 操作（伪代码列表）
#----------------------------------------
import traceback
from analyzer.buff import analyze_buff
from anne import node_translator
from anne.node import Node

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
            else:
                children.append(node.translate(blackboard))
        # 最后一项打上标记
        if len(children) > 0:
            children[len(children)-1]["last_one"] = True
        return {"main" : "","children" : children}