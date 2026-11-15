#----------------------------------------
# 合约词条
#----------------------------------------
from analyzer.blackboard import analyze_blackboard
from anne.rune import Rune

class Crisis:
    def __init__(self, crisis_key, crisis_data):
        self.crisis_key = crisis_key
        self.crisis_data = crisis_data
        self.crisis_score = crisis_data["score"]
        self.crisis_name = crisis_data["runeName"] if "runeName" in crisis_data else self.crisis_key
        self.display_name = self.crisis_name
        self.catagory = "合约词条"
        self.hidden = False

    # 获取显示名
    def get_display_name(self):
        if self.display_name == "":
            return self.rune_key
        return self.display_name

    # 获取原文
    def get_raw_data(self):
        return self.crisis_data

    # 翻译
    def translate(self):
        translation = {
            "main" : self.crisis_key,
            "description" : "分数："+str(self.crisis_score),
            "children" : []
        }
        translation["children"].append({"main" : self.crisis_data["packedRune"]["description"]})
        rune_translation = {"main" : "词条效果（符文）：","children":[]}
        for rune_data in self.crisis_data["packedRune"]["runes"]:
            rune_translation["children"].append(Rune(rune_data).translate())
        translation["children"].append(rune_translation)
        return translation