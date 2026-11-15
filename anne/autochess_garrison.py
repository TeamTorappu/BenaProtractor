#----------------------------------------
# 卫戍协议 · 干员特质
#----------------------------------------
from analyzer.blackboard import analyze_blackboard
from anne.rune import Rune
from dictionary import enum_dictionary

class AutochessGarrison:
    def __init__(self, garrison_id, garrison_data):
        self.garrison_id = garrison_id
        self.garrison_data = garrison_data
        self.display_name = self.garrison_id
        self.catagory = str(self.garrison_data["eventTypeDesc"]) + "特质"
        self.hidden = False

    # 获取显示名
    def get_display_name(self):
        return self.display_name

    # 获取原文
    def get_raw_data(self):
        return self.garrison_data
    
    # 获取翻译
    def translate(self):
        result = {
            "main" : self.get_display_name(),
            "description" : str(self.garrison_data["eventType"])+" | "+str(self.garrison_data["effectType"]),
            "children" : []
        }

        bb = analyze_blackboard(self.garrison_data["blackboard"])
        # 盟约特效
        #if "eventEffect" in self.garrison_data and self.garrison_data["eventEffect"] != None:
        #    result["children"].append({"main" : "满足条件时，提供：" + self.garrison_data["eventEffect"]})
        
        # 战斗中符文（两者理应是不兼容的）
        if "battleRuneKey" in self.garrison_data and self.garrison_data["battleRuneKey"] != None:
            rune_translation = Rune({
                "key" : self.garrison_data["battleRuneKey"],
                "blackboard" : self.garrison_data["blackboard"]
            }).translate()
            rune_translation["main"] = "应用符文：" + rune_translation["main"]
            if "角色类单位" in rune_translation["main"]:
                rune_translation["main"] = rune_translation["main"].replace("所有角色类单位","此单位").replace("角色类单位","此单位")
            if "GlobalBuff" in rune_translation["main"] and "children" in rune_translation:
                rune_translation["children"][0]["main"] = rune_translation["children"][0]["main"].replace("我方单位","此单位")
            result["children"].append(rune_translation)

        if len(bb) > 0:
            result["children"].append({
                "main" : "黑板参数：",
                "children" : [(key + " : " + str(value)) for key,value in bb.items()],
                "style_closed" : True
            })
        return result
        