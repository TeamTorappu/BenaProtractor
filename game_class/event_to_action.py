#----------------------------------------
# 事件与操作
#----------------------------------------
from dictionary import anne_dictionary
from game_class.node import Node

# Buff的伪代码承载类
class EventToAction:
    def __init__(self, event_key, node_data_list):
        self.event_key = event_key
        self.node_list = []
        for node_data in node_data_list:
            self.node_list.append(Node(node_data))
        self.hidden = False
    
    # 获取原文
    def get_raw_data(self):
        return [node.node_data for node in self.node_list]

    # 翻译
    def translate(self,blackboard={}):
        from anne.anne_node import anne_node_translate_all

        print("[安妮]尝试翻译事件 "+self.event_key)
        translation = anne_node_translate_all(self.node_list,blackboard)
        translation["main"] = self.event_key
        translation["role"] = "section"
        event_name = anne_dictionary("buff_event",self.event_key)
        if event_name != self.event_key:
            translation["main"] = f"{event_name}（{self.event_key}）"
        return translation