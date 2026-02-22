'''
类定义
'''
# 黑板本来也打算定义为类，发现不好用，就改回处理的结构体了
# 处理黑板，将黑板转化为更易于处理的格式
def process_blackboard(raw_bb_data):
    bb_data = {}
    for bb in raw_bb_data:
        if "key" in bb:
            bb_key = bb["key"]
            if "valueStr" in bb and bb["valueStr"] != None:
                bb_data[bb_key] = bb["valueStr"]
            elif "value" in bb:
                bb_data[bb_key] = bb["value"]
    return bb_data

# 伪代码节点类
class Node:
    def __init__(self, node_data):
        # 哎，神经空指针
        if node_data == None:
            self.node_name = "NULL"
            self.node_data = {}
            self.translation = {"main" : "YJ的棍木"}
            return
        # 去除Node前后缀方便解析
        node_name = node_data["$type"]
        if node_name.startswith("Torappu."):
            node_name = node_name[28:-17]
        self.node_name = node_name
        self.node_data = node_data
        self.translation = None
        #if node_data.has_key("_buff"):
        #    # 获取子buff
        #    self.node_config["_buff"] = Buff(node_data._buff)
        if node_name == "IfElse":
            self.node_data["condition_node"] = Node(node_data["_conditionNode"])
            self.node_data["succeed_nodes"] = []
            self.node_data["fail_nodes"] = []
            if node_data["_succeedNodes"] != None:
                for sub_node in node_data["_succeedNodes"]:
                    self.node_data["succeed_nodes"].append(Node(sub_node))
            if node_data["_failNodes"] != None:
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



# 肉鸽的Buff数据类，未来可能可以统一度量衡，目前还是算了
class RogueBuffData:
    def __init__(self, buff_data):
        self.key = buff_data["key"]
        self.blackboard = process_blackboard(buff_data["blackboard"])
        self.translation = None

# 肉鸽的道具类，可能是藏品，可能是资源，甚至可能是排异反应/岁时之类的东西
class RogueItem:
    def __init__(self, season, item_key, item_info, item_data=None):
        self.item_key = item_key
        self.item_info = item_info
        self.item_data = item_data
        self.season = season
        self.display_name = item_info["name"]
        self.type = item_info["type"]
        self.display_type = ""
        # 处理分类显示
        if self.type == "RELIC":
            self.display_type = "藏品"
        elif self.type == "BAND":
            self.display_type = "分队"
        elif self.type == "RECRUIT_TICKET":
            self.display_type = "招募券"
        elif self.type == "UPGRADE_TICKET":
            self.display_type = "进阶券"
        elif self.type == "ACTIVE_TOOL":
            self.display_type = "支援装置"
        elif self.type == "FEATURE":
            self.display_type = "精通"
        elif self.type == "COPPER_BUFF":
            self.display_type = "钱"
        else:
            self.display_type = "鸽物"
        # 如果是藏品或者类藏品，读取持有的buff数据
        self.effect_list = []
        self.has_effect = False
        if item_data != None and "buffs" in item_data:
            self.has_effect = True
            for buff in item_data["buffs"]:
                self.effect_list.append(RogueBuffData(buff))