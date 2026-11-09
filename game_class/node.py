#----------------------------------------
# 伪代码节点
#----------------------------------------
import json

class Node:
    def __init__(self, node_data):
        # 哎，神经空指针
        if node_data == None:
            self.node_name = "NULL"
            self.node_data = {}
            self.translation = {"main" : "YJ的棍木"}
            return
        # 去除Node前后缀方便解析
        node_name = node_data.get("$type", "Unknown")
        if node_name.startswith("Torappu."):
            node_name = node_name.split(",", 1)[0].rsplit("+", 1)[-1]
        self.node_name = node_name
        self.node_data = node_data
        #self.node_data["$type"] = node_name
        self.translation = None
        self.condition_nodes = None
        self.succeed_nodes = None
        self.fail_nodes = None
        # 预处理
        #if node_data.has_key("_buff"):
        #    # 获取附属Buff
        #    self.node_config["_buff"] = Buff(node_data._buff)
        if node_name == "IfElse":
            self.condition_nodes = []
            self.succeed_nodes = []
            self.fail_nodes = []
            if node_data["_conditionNode"] != None:
                self.condition_nodes.append(Node(node_data["_conditionNode"]))
            if node_data["_succeedNodes"] != None:
                for sub_node in node_data["_succeedNodes"]:
                    self.succeed_nodes.append(Node(sub_node))
            if node_data["_failNodes"] != None:
                for sub_node in node_data["_failNodes"]:
                    self.fail_nodes.append(Node(sub_node))
        elif node_name == "IfConditions":
            self.condition_nodes = []
            self.succeed_nodes = []
            self.fail_nodes = []
            if node_data["_conditionsNode"] != None:
                for sub_node in node_data["_conditionsNode"]:
                    self.condition_nodes.append(Node(sub_node))
            if node_data["_succeedNodes"] != None:
                for sub_node in node_data["_succeedNodes"]:
                    self.succeed_nodes.append(Node(sub_node))
            if node_data["_failNodes"] != None:
                for sub_node in node_data["_failNodes"]:
                    self.fail_nodes.append(Node(sub_node))

    # 获取原文
    def get_raw_data(self):
        return json.dump(self.node_data,indent=4,ensure_ascii=False)