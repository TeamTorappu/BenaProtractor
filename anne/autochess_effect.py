#----------------------------------------
# 卫戍协议 · 效果
#----------------------------------------
from dictionary import anne_dictionary
from anne.relic import Relic

EFFECT_TYPE = {
    "BAND_SKILL" : "策略技能",
    "CHAR_MAP" : "干员养成加成",
    "BOND" : "盟约效果",
    "EQUIP" : "装备效果",
    "ENEMY_GAIN" : "悬赏决策",
    "ENEMY" : "敌方强化",
    "BUFF_GAIN" : "增益决策",
}

class AutochessEffect:
    def __init__(self, effect_id, effect_info, effect_buff_info = []):
        self.effect_id = effect_id
        self.effect_info = effect_info
        self.effect_buff_info = effect_buff_info
        self.effect_name = effect_info["effectName"]
        self.effect_type = effect_info["effectType"]
        self.effect_relics = [Relic(relic_data,"AUTOCHESS_"+self.effect_type) for relic_data in effect_buff_info]
        self.display_name = ""
        self.hidden = False

    # 获取显示名
    def get_display_name(self):
        if self.display_name == "":
            if self.effect_type in EFFECT_TYPE:
                self.display_name = EFFECT_TYPE[self.effect_type] + "："
            else:
                self.display_name = "卫戍效果："
            if self.effect_name != None and self.effect_name != "":
                self.display_name += self.effect_name
                if self.effect_type == "EQUIP" and self.effect_id.startswith("eff_acgarm"):
                    self.display_name += "（进阶）"
            else:
                self.display_name += self.effect_id
        return self.display_name

    # 获取原文
    def get_raw_data(self):
        return [self.effect_info,self.effect_buff_info]
    
    # 获取翻译
    def translate(self):
        result = {
            "main" : self.get_display_name() + "（" + self.effect_id + "）",
            "children" : []
        }
        result["children"].append({"main" : self.effect_info["effectDesc"].replace("\\n","\n")})
        for relic in self.effect_relics:
            result["children"].append(relic.translate())
        return result
