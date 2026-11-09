#----------------------------------------
# 全局Buff
#----------------------------------------
import json

class GlobalBuff:
    def __init__(self, buff_key, prefab_data):
        self.buff_key = buff_key
        self.display_name = buff_key
        self.prefab_data = prefab_data
        self.target_options = prefab_data["_options"]
        self.buff_datas = prefab_data["_buffs"]
        self.deck_buff_datas = prefab_data["_deckBuffs"]
        self.hidden = False
    
    # 获取显示名
    def get_display_name(self):
        if self.display_name == "":
            return self.buff_key
        return self.display_name
    
    # 获取原文
    def get_raw_data(self):
        return json.dumps(self.prefab_data,indent=4,ensure_ascii=False)