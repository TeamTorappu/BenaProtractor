#----------------------------------------
# 卫戍协议 · 策略
#----------------------------------------
from dictionary import anne_dictionary

class AutochessBand:
    def __init__(self, band_id, band_data, band_info = {}, band_effect = None):
        self.band_id = band_id
        self.band_data = band_data
        self.band_info = band_info
        self.band_effect = band_effect
        self.band_type = band_data["bandType"]
        self.band_hp = band_data["totalHp"] if band_data["totalHp"] else 0
        self.display_name = "策略：" + band_info.get("bandName", str(band_id))
        self.hidden = False

    # 获取显示名
    def get_display_name(self):
        return self.display_name

    # 获取原文
    def get_raw_data(self):
        return [self.band_info,self.band_data]
    
    # 获取翻译
    def translate(self):
        result = {
            "main" : self.get_display_name(),
            "description" : "♖" + str(self.band_hp),
            "children" : []
        }
        if self.band_type == "BONDRELEVANT":
            bonds = [anne_dictionary("bond_id",bond_id) for bond_id in self.band_data["relateBondList"]]
            result["description"] += " | " + "".join(bonds) + "专属策略"
        result["children"].append({"main" : self.band_data["bandDesc"]})
        result["children"].append({
            "main" : "解锁条件：",
            "children" : [{"main" : self.band_info["unlockDesc"]}]
        })
        # 策略效果（藏品）
        if self.band_effect != None:
            effect_translation = self.band_effect.translate()
            effect_translation["main"] = "策略效果（藏品）："
            result["children"].append(effect_translation)
        # 禁用模式/难度
        if len(self.band_data["inactiveModeIdList"]) > 0:
            result["children"].append({"main" : ""})
            result["children"].append({
                "main" : "在以下模式/难度中无法使用：",
                "children" : [mode_id for mode_id in self.band_data["inactiveModeIdList"]]
                #"children" : [anne_dictionary("auto_chess_mode_id",mode_id) for mode_id in self.band_data["inactiveModeIdList"]]
            })
        return result
