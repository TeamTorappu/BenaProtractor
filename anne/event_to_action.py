#----------------------------------------
# 事件→操作
#----------------------------------------
from dictionary import anne_dictionary
from anne.action import Action

# Buff的伪代码承载类
class EventToAction:
    def __init__(self, event_key, action_data):
        self.event_key = event_key
        self.action = Action(action_data)
        self.display_name = ""
        self.hidden = False
    
    # 获取原文
    def get_raw_data(self):
        return [node.node_data for node in self.node_list]

    # 翻译
    def translate(self,blackboard={}):
        print("[安妮]尝试翻译事件 "+self.event_key)
        translation = self.action.translate(blackboard)
        translation["main"] = self.event_key
        translation["role"] = "section"
        event_name = anne_dictionary("buff_event",self.event_key)
        if event_name != self.event_key:
            translation["main"] = f"{event_name}（{self.event_key}）"
        return translation