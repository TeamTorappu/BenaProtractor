#----------------------------------------
# Buff
#----------------------------------------
from analyzer.buff import analyze_buff

class Buff:
    def __init__(self, buff_key, buff_data):
        self.buff_key = buff_key
        self.display_name = buff_key
        self.buff_data = buff_data
        self.hidden = False
    
    # 获取显示名
    def get_display_name(self):
        if self.display_name == "":
            return self.buff_key
        return self.display_name
    
    # 获取原文
    def get_raw_data(self):
        return self.buff_data

    # 翻译
    def translate(self,blackboard: dict = {}):
        from bena import ask_bena

        print("[安妮]尝试翻译Buff "+self.buff_key)
        translation = analyze_buff(self.buff_data,blackboard,True)
        # 如果内部有自己的小巧思BuffKey
        if self.buff_key != self.buff_data["buffKey"]: 
            translation["description"] = "这个Buff的卡名在规则上被视为 <buff|"+self.buff_data["buffKey"]+"> "
            if "（" in translation["main"]:
                translation["main"] = self.buff_key + "（" + translation["main"].split("（",1)[1]
            else:
                translation["main"] = self.buff_key
        # 如果显示名不一样
        if self.display_name != self.buff_key:
            if "（" in translation["main"]:
                translation["main"] = f"{self.display_name}（{self.buff_key}；" + translation["main"].split("（",1)[1]
            else:
                translation["main"] = f"{self.display_name}（{self.buff_key}）"
        # 尝试把buff_template直接显示出来
        if self.buff_data["templateKey"] != "empty":
            buff_template = ask_bena("buff_template",self.buff_data["templateKey"])
            if buff_template != None:
                if "children" not in translation:
                    translation["children"] = []
                buff_template_translation = buff_template.translate(blackboard)
                buff_template_translation["main"] = "机制&效果（Buff模板内容）："
                translation["children"].append(buff_template_translation)
            else:
                translation["children"].append({
                    "main" : "机制&效果（Buff模板内容）：（未找到相应名称的Buff模板）"
                })
        return translation