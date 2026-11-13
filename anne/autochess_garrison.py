#----------------------------------------
# 卫戍协议 · 干员特质
#----------------------------------------
from analyzer.blackboard import analyze_blackboard
from dictionary import anne_dictionary

class AutochessGarrison:
    def __init__(self, garrison_id, garrison_data):
        self.garrison_id = garrison_id
        self.garrison_data = garrison_data
        self.display_name = ""
        self.hidden = False

    # 获取显示名
    def get_display_name(self):
        if self.display_name == "":
            return self.garrison_id
        return self.display_name

    # 获取原文
    def get_raw_data(self):
        return self.garrison_data
    
    # 获取翻译
    def translate(self):
        result = {
            "main" : self.get_display_name(),
            "children" : []
        }
        result["children"].append({"main" : "事件类型："+str(self.garrison_data["eventTypeDesc"])+"（"+str(self.garrison_data["eventType"])+"）"})
        result["children"].append({"main" : "效果类型："+str(self.garrison_data["effectType"])})

        bb = analyze_blackboard(self.garrison_data["blackboard"])
        # 盟约特效
        if "eventEffect" in self.garrison_data and self.garrison_data["eventEffect"] != None:
            result["children"].append({"main" : "满足条件时，提供：" + self.garrison_data["eventEffect"]})
        
        # 战斗中符文（两者理应是不兼容的）
        if "battleRuneKey" in self.garrison_data and self.garrison_data["battleRuneKey"] != None:
            result["children"].append({"main" : "战斗中，应用符文：" + self.garrison_data["battleRuneKey"]})

        if len(bb) > 0:
            result["children"].append({
                "main" : "黑板参数：",
                "children" : [(key + " : " + str(value)) for key,value in bb.items()],
                "style_closed" : True
            })
        return result
        