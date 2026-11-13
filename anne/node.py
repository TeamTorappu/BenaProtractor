#----------------------------------------
# 伪代码节点
#----------------------------------------
import traceback

from analyzer.buff import analyze_buff
from anne import node_translator

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
        self.condition_nodes = None
        self.succeed_nodes = None
        self.fail_nodes = None
        self.hidden = False

    # 获取原文
    def get_raw_data(self):
        return self.node_data

    # 翻译
    def translate(self,blackboard={}):
        #print(f"[安妮]尝试翻译节点 {node_name}")
        method = getattr(node_translator, self.node_name, "")
        translation = None
        try:
            if method != "" :
                translation = method(self.node_data,blackboard)
            else: # 无法翻译，把所有数据搓成可阅读的格式
                translation = self.fake_translate(blackboard)
        except Exception as e:
            print(f"[安妮]... {self.node_name} 节点翻译失败了")
            traceback.print_exc()
            translation = {
                "main" : self.node_name+"（翻译失败）",
                "style_closed" : True,
            }
        # 返回译文
        return translation
    
    # 假翻译（仅把结构保留下来，通常是因为还没翻译）
    def fake_translate(self,blackboard={}):
        children = []
        for key,content in self.node_data.items():
            if isinstance(content,dict): # 如果是子节点或者buff，还是要嵌套翻译一下试试的
                if "attributes" in content and isinstance(content["attributes"],dict): # 看着像buff
                    buff = analyze_buff(content,blackboard)
                    buff["main"] = str(key) + " : " + buff["main"]
                    children.append(buff)
                elif "$type" in content: # 子节点
                    sub_node = Node(content).translate(blackboard)
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
                    sub_node_list = Node.translate_list(sub_content_list,blackboard)
                    sub_node_list["main"] = str(key) + " : " + sub_node_list["main"]
                    children.append(sub_node_list)
                elif len(content) > 0 and "attributes" in content[0]: # 附属Buff列表
                    children_children = []
                    for scontent in content:
                        children_children.append(analyze_buff(scontent,blackboard))
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
            elif key != "$type":
                children.append({"main": str(key) + " : " + str(content)})
        return {
            "main" : self.node_name+"（未翻译）",
            "style_closed" : True,
            "children" : children
        }