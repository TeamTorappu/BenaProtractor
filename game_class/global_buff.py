#----------------------------------------
# 全局Buff
#----------------------------------------
import json

from analyzer.buff import analyze_buff
from analyzer.deckbuff import analyze_deckbuff
from analyzer.selector import analyze_selector_target_options_override
from analyzer.target_options import analyze_target_options_conditions, analyze_target_options_side

NOT_SHOW_KEYS = [
    "m_Script","_key","_options","_buffs",
    "_deckBuffs","_extraBuff","_cardbuffKey","_sourceType",
    "_overrideCameraEffect"
]

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
    
    # 翻译
    def translate(self,blackboard : dict = {}):
        from bena import ask_bena

        print("[安妮]尝试翻译GlobalBuff "+self.buff_key)
        # 处理翻译
        translation = {
            "main" : self.buff_key,
            "children" : []
        }
        if self.display_name != self.buff_key:
            translation["main"] = f"{self.display_name}（{self.buff_key}）"
        
        # 主类
        if self.prefab_data["m_Script"] == "MonoBehaviour":
            translation["children"].append({"main" : "类：未知"})
        elif self.prefab_data["m_Script"] != "GlobalBuff":
            translation["children"].append({"main" : "类："+self.prefab_data["m_Script"]})
        if self.prefab_data["_overrideCameraEffect"] != "":
            translation["children"].append({"main" : "覆写镜头特效："+self.prefab_data["_overrideCameraEffect"]})
        
        # 目标筛选逻辑
        target = "单位"
        target_options = analyze_selector_target_options_override(self.target_options,blackboard)
        target_side = analyze_target_options_side(target_options,True,self.prefab_data["_sourceType"])
        conditions_list = analyze_target_options_conditions(target_options)
        if target_side != "":
            conditions_list.append(target_side)
        if len(conditions_list) > 3: # 多条件的复杂筛选
            conditions_translation = {"main" : f"生效对象条件：","children" : []}
            for condition in conditions_list:
                if condition.endswith("干员"):
                    target = target.replace("单位",condition)
                elif condition == "我方" or condition == "敌方" or condition == "我方/中立":
                    target = condition + target
                elif condition == "相同阵营" or condition == "对立阵营":
                    my_side = "敌方" if self.prefab_data["_sourceType"] == "ENEMY" else "我方"
                    prefixs.append(f"相对于{my_side}而言属"+condition+"且可选的")
                else:
                    conditions_translation["children"].append({"main" : condition})
            translation["children"].append(conditions_translation)
            target = "符合条件的" + target
        elif len(conditions_list) > 0:
            prefixs = []
            for condition in conditions_list:
                if condition.endswith("干员"):
                    target = target.replace("单位",condition)
                elif condition == "我方" or condition == "敌方" or condition == "我方/中立":
                    target = condition + target
                elif condition == "相同阵营" or condition == "对立阵营":
                    my_side = "敌方" if self.prefab_data["_sourceType"] == "ENEMY" else "我方"
                    prefixs.append(f"相对于{my_side}而言属"+condition+"且可选的")
                elif condition.endswith("的"):
                    prefixs.append(condition)
                else:
                    prefixs.append(condition+"的")
            target = "、".join(prefixs)+target
        else:
            target = "所有单位"
        # 逐Buff添加至列表
        if len(self.buff_datas) > 0:
            buffs_translation = {
                "main" : f"{target}登场或重生时，获得以下Buff：",
                "children" : []
            }
            for buff_data in self.buff_datas:
                _buff = analyze_buff(buff_data,blackboard)
                if not buff_data["loadFromDB"] and buff_data["templateKey"] != "empty":
                    buff_template = ask_bena("buff_template",buff_data["templateKey"])
                    if buff_template != None:
                        if "children" not in _buff:
                            _buff["children"] = []
                        buff_template_translation = buff_template.translate(blackboard)
                        for _child in buff_template_translation["children"]:
                            _buff["children"].append(_child)
                buffs_translation["children"].append(_buff)
            translation["children"].append(buffs_translation)
        # 逐DeckBuff添加至列表
        if len(self.deck_buff_datas) > 0:
            deck_buffs_translation = {
                "main" : f"为待部署区中符合条件的卡施加以下DeckBuff：",
                "children" : []
            }
            for deck_buff_data in self.deck_buff_datas:
                _buff = analyze_deckbuff(deck_buff_data,blackboard)
                buff_data = deck_buff_data["buff"]
                if not buff_data["loadFromDB"] and buff_data["templateKey"] != "empty":
                    buff_template = ask_bena("buff_template",buff_data["templateKey"])
                    if buff_template != None:
                        if "children" not in _buff:
                            _buff["children"] = []
                        buff_template_translation = buff_template.translate(blackboard)
                        for _child in buff_template_translation["children"]:
                            _buff["children"].append(_child)
                deck_buffs_translation["children"].append(_buff)
            translation["children"].append(deck_buffs_translation)
        # 额外Buff
        if "_extraBuff" in self.prefab_data and len(self.prefab_data["_extraBuff"]) > 0:
            buff_translation = {
                "main" : f"此外，在特定情况下，为所有{target}施加以下Buff：",
                "children" : []
            }
            buff_data = self.prefab_data["_extraBuff"]
            _buff = analyze_buff(buff_data,blackboard)
            if not buff_data["loadFromDB"] and buff_data["templateKey"] != "empty":
                buff_template = ask_bena("buff_template",buff_data["templateKey"])
                if buff_template != None:
                    if "children" not in _buff:
                        _buff["children"] = []
                    buff_template_translation = buff_template.translate(blackboard)
                    for _child in buff_template_translation["children"]:
                        _buff["children"].append(_child)
            buff_translation["children"].append(_buff)
            translation["children"].append(buff_translation)
        # Cardbuff
        if "_cardbuffKey" in self.prefab_data:
            card_buff_translation = {
                "main" : f"为待部署区中符合条件的卡施加一个CardBuff：",
                "children" : [{"main" : self.prefab_data["_cardbuffKey"]}]
            }
            translation["children"].append(card_buff_translation)
        # 剩下无法翻译的部分先直接展示
        for key, value in self.prefab_data.items():
            if key not in NOT_SHOW_KEYS:
                translation["children"].append(key+" : "+str(value))
        return translation
