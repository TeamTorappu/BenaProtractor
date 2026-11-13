#----------------------------------------
# 藏品符文
#----------------------------------------
from analyzer.blackboard import analyze_blackboard
from analyzer.relic_timing import analyze_relic_timing
from anne import relic_translator
from bena import ask_bena

class Relic:
    def __init__(self, relic_data, item_type = "RELIC"):
        self.relic_data = relic_data
        self.key = relic_data["key"]
        self.type = item_type # 父级的类型，用于传参
        self.blackboard = analyze_blackboard(relic_data["blackboard"])
        self.display_name = ""
        self.hidden = False

    # 获取显示名
    def get_display_name(self):
        if self.display_name == "":
            return self.key
        return self.display_name

    # 获取原文
    def get_raw_data(self):
        return self.relic_data

    # 翻译
    def translate(self):
        #from anne.anne_relic import anne_relic_translate
        #return anne_relic_translate(self)
        effect_key = self.key
        print(f"[安妮]尝试翻译藏品 {effect_key}")
        method = getattr(relic_translator, effect_key, "")
        if method != "" :
            translation = method(self.type,self.blackboard)
            if "global_buff" in translation: # 翻译全局Buff
                # 尝试寻找全局Buff
                gbuff = ask_bena("global_buff",translation["global_buff"])
                if gbuff == None:
                    gbuff = ask_bena("global_buff",translation["global_buff"].lower()) #试试小写，Assetbundle的问题
                if gbuff != None:
                    gbuff_translation = gbuff.translate(self.blackboard)
                    gbuff_translation["main"] = "战斗中："
                    if len(translation["children"]) > 0:
                        translation["children"][0]["style_closed"] = True
                        translation["children"] = gbuff_translation["children"] + translation["children"]
                    else:
                        translation["children"] += gbuff_translation["children"]
            return translation
        else: # 无法翻译，把所有数据搓成可阅读的格式
            prefix = analyze_relic_timing(self.type,self.blackboard)
            translation = {
                "main" : prefix+effect_key+"（未翻译）",
                "style_closed" : True,
                "children" : []
            }
            for key,bb in self.blackboard.items():
                translation["children"].append({"main": str(key) + " : "+str(bb)})
        # 返回译文
        return translation