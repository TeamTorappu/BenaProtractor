#----------------------------------------
# 事件与操作
#----------------------------------------
import json
from gameclasses.node import Node

# Buff的伪代码承载类
class EventToAction:
    def __init__(self, event_key, node_data_list):
        self.event_key = event_key
        self.event_name = event_key
        self.node_list = []
        for node_data in node_data_list:
            self.node_list.append(Node(node_data))
    
    # 获取原文
    def get_raw_data(self):
        new_dict = {}
        new_dict[self.event_key] = [node.node_data for node in self.node_list]
        return json.dumps(new_dict,indent=4,ensure_ascii=False)