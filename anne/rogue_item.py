#----------------------------------------
# 肉鸽物品（藏品、队伍、零件、通宝等）
#----------------------------------------
from anne.relic import Relic

RESOURCE_TYPES = [
    "GOLD","EXP","HP","HPMAX","SHIELD","SQUAD_CAPACITY",
    "SPECIAL_ZONE_AP","CUSTOM_TICKET","COPPER_DRAW_NUM",
    "STASH_RECRUIT_LIMIT","DIVINATION_KIT","POPULATION"
]

# 肉鸽的道具类，可能是藏品，可能是资源，甚至可能是排异反应/岁时之类的东西
class RogueItem:
    def __init__(self, season, item_key, item_info, item_data=None):
        self.item_key = item_key
        self.item_info = item_info
        self.item_data = item_data
        self.season = season
        self.display_name = item_info["name"].strip() # 猜猜为什么
        self.type = item_info["type"]
        self.catagory = ""
        self.hidden = False
        # 处理分类显示
        if self.type == "RELIC":
            self.catagory = "收藏品"
        elif self.type == "BAND":
            self.catagory = "分队"
        elif self.type == "RECRUIT_TICKET":
            self.catagory = "招募券"
        elif self.type == "UPGRADE_TICKET":
            self.catagory = "进阶券"
        elif self.type == "ACTIVE_TOOL":
            self.catagory = "支援装置"
        elif self.type == "FEATURE":
            self.catagory = "机制"
        elif self.type == "WRATH":
            self.catagory = "岁时"
            if item_data == None:
                self.hidden = True # 无效果则隐藏
        elif self.type == "COPPER_BUFF":
            self.catagory = "钱" # 这是骰出的钱
            if item_data == None:
                self.hidden = True # 无效果则隐藏
        elif self.type == "COPPER":
            self.catagory = "盒内的钱" # 这个没有数据，不需要展示
            #self.display_name += "(盒内)"
            self.hidden = True # 隐藏
        elif self.type == "MAX_WEIGHT":
            self.catagory = "容量"
        elif self.type == "LEGACY":
            self.catagory = "襁褓"
        elif self.type == "SCRAP":
            self.catagory = "零件"
        elif self.type == "NODE_BUOY":
            self.catagory = "节点强化"
        elif self.type == "CHARACTER":
            self.catagory = "应急干员"
            self.display_name += "（应急）"
            self.hidden = True # 隐藏
        elif self.type in RESOURCE_TYPES:
            self.catagory = "资源"
        else:
            self.catagory = self.type # "鸽物"
        # 如果是藏品或者类藏品，读取持有的buff数据
        self.effect_list = []
        self.has_effect = False
        if item_data != None and "buffs" in item_data:
            self.has_effect = True

    # 获取显示名
    def get_display_name(self):
        return self.display_name
    
    # 获取原文
    def get_raw_data(self):
        if self.item_data != None and "buffs" in self.item_data:
            return [self.item_info,self.item_data]
        else:
            return [self.item_info]

    # 翻译
    def translate(self):
        from bena import ask_bena

        print(f"[安妮]尝试翻译{self.catagory} {self.display_name}（{self.item_key}）")
        translation = {
            "main" : f"{self.display_name}（{self.item_key}）",
            "children" : []
        }
        # 展示原始的文案
        if self.item_info["description"] != None:
            translation["description"] = self.item_info["description"]
        
        # 类型和稀有度
        translation["children"].append({"main" : "类型 : " + self.catagory + "("+self.type+"）"})
        translation["children"].append({"main" : "稀有度 : " + self.item_info["rarity"]}) # 需翻译
        
        # 界园的钱始终有两套，加个超链接
        if self.type == "COPPER_BUFF":
            another_key = self.item_key.replace("copper_buff","copper")
            if ask_bena("RogueItem",another_key) != None:
                translation["children"].append({"main" : f"（这里的鹰文可能与游戏内有出入，文案用的钱请见  <RogueItem|{another_key}>）"})
        elif self.type == "COPPER":
            another_key = self.item_key.replace("copper","copper_buff")
            if ask_bena("RogueItem",another_key) != None:
                translation["children"].append({"main" : f"（这是展示文案用的钱，钱的实际效果请见 <RogueItem|{another_key}>）"})

        # 藏品效果或解释的原文
        if self.item_info["usage"] != None:
            usage = {"main" : self.catagory+"描述：","children": []}
            usage["children"].append({"main" : self.item_info["usage"]})
            translation["children"].append(usage)
        
        # 效果文本
        if self.has_effect:
            effect_translation = {"main" : "","children" : []}
            for relic_data in self.item_data["buffs"]:
                relic_translation = Relic(relic_data,self.type).translate()
                effect_translation["children"].append(relic_translation)
            effect_translation["main"] = self.catagory+"效果："
            translation["children"].append(effect_translation)

        return translation