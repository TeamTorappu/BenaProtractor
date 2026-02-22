'''
类定义
'''

# 伪代码节点
class Node:
    def __init__(self, node_data):
        # 去除Node前后缀方便解析
        node_name = node_data["$type"]
        if node_name.startswith("Torappu."):
            node_name = node_name[28:-17]
        self.node_name = node_name
        self.node_data = node_data
        #if node_data.has_key("_buff"):
        #    # 获取子buff
        #    self.node_config["_buff"] = Buff(node_data._buff)
        if node_name == "IfElse":
            self.node_data["condition_node"] = Node(node_data["_conditionNode"])
            self.node_data["succeed_nodes"] = []
            self.node_data["fail_nodes"] = []
            for sub_node in node_data["_succeedNodes"]:
                self.node_data["succeed_nodes"].append(Node(sub_node))
            for sub_node in node_data["_failNodes"]:
                self.node_data["fail_nodes"].append(Node(sub_node))

# BuffTemplate类
class BuffTemplate:
    def __init__(self, buff_key, buff_data):
        self.buff_key = buff_key
        self.template_key = buff_data["templateKey"] # 虽然不知道有啥区别，总之留着吧
        #self.effect_key = buff_data["effectKey"] # 特效没啥处理的必要
        self.on_event_priority = buff_data["onEventPriority"]
        self.events = []
        for event_name in buff_data["eventToActions"].keys():
            self.events.append(BuffEvent(event_name,buff_data["eventToActions"][event_name]))
        self.display_name = ""
    
    # 获取显示名
    def display_name(self):
        if self.display_name == "":
            return self.buff_key
        return self.display_name
        

# Buff的伪代码承载类
class BuffEvent:
    def __init__(self, event_key, node_data_list):
        self.event_key = event_key
        self.event_name = event_key
        self.node_list = []
        for node_data in node_data_list:
            self.node_list.append(Node(node_data))