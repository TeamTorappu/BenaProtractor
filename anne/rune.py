#----------------------------------------
# 藏品符文
#----------------------------------------
from analyzer.blackboard import analyze_blackboard
from anne import rune_translator
from bena import ask_bena

class Rune:
    def __init__(self, rune_data, selector = {}):
        self.rune_data = rune_data
        self.rune_key = rune_data["key"]
        self.blackboard_data = rune_data["blackboard"]
        self.blackboard = analyze_blackboard(self.blackboard_data)
        self.selector = selector
        self.display_name = ""
        self.hidden = False

    # 获取显示名
    def get_display_name(self):
        if self.display_name == "":
            return self.rune_key
        return self.display_name

    # 获取原文
    def get_raw_data(self):
        return self.rune_data

    # 翻译
    def translate(self):
        effect_key = self.rune_key
        print(f"[安妮]尝试翻译符文 {effect_key}")
        method = getattr(rune_translator, effect_key, "")
        if method != "" :
            translation = method(self.selector,self.blackboard)
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
            translation = {
                "main" : effect_key+"（未翻译）",
                "style_closed" : True,
                "children" : []
            }
            for key,bb in self.blackboard.items():
                translation["children"].append({"main": str(key) + " : "+str(bb)})
        # 返回译文
        return translation