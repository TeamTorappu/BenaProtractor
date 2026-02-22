'''
贝娜 - 分析组件
将yj的json解读为可以阅读的格式，主要是node
'''
import json
from data_class import *

# 表格数据
BUFF_TEMPLATE_KEYS = []
BUFF_TEMPLATE_DATA = {}
BUFF_TEMPLATE_DATA_PATH = "./tables/buff_template_data.json"
CHARACTER_KEYS = []
CHARACTER_TABLE = {}
CHARACTER_TABLE_PATH = "./tables/character_data.json"
ROGUELIKE_TOPIC_SEASONS = ["rogue_5"]#["rogue_1","rogue_2","rogue_3","rogue_4","rogue_5"]
ROGUELIKE_TOPIC_KEYS = []
ROGUELIKE_TOPIC_TABLE = {}
ROGUELIKE_TOPIC_TABLE_PATH = "./tables/roguelike_topic_table.json"
print("[贝娜]我叫贝娜，来找一个出门就忘了回家的笨蛋。听说她还有些活要干，没办法，我也在这陪她一会好了。")

# 读取buff_template_data.json，并解析
def load_buff_template_data():
    print(f"[贝娜]开始读取buff_template_data.json")
    json_data = {}
    # 获取文件数据
    with open(BUFF_TEMPLATE_DATA_PATH,'r',encoding="UTF-8") as _f:
        json_data = json.load(_f)
    # 开始解析
    for buff_template_key in json_data.keys():
        BUFF_TEMPLATE_KEYS.append(buff_template_key)
        BUFF_TEMPLATE_DATA[buff_template_key] = BuffTemplate(buff_template_key,json_data[buff_template_key])
        print(f"[贝娜]已读取Buff模板 {buff_template_key}")
    print(f"[贝娜]已完成对buff_template_data.json的读取！")

# 读取roguelike_topic_table.json，并解析
def load_roguelike_topic_table():
    print(f"[贝娜]开始读取roguelike_topic_table.json")
    json_data = {}
    # 获取文件数据
    with open(ROGUELIKE_TOPIC_TABLE_PATH,'r',encoding="UTF-8") as _f:
        json_data = json.load(_f)
    # 按季度读取需要的数据表
    for season in ROGUELIKE_TOPIC_SEASONS:
        ROGUELIKE_TOPIC_TABLE[season] = {}
        # 需要的东西都在details里，其他部分就不需要解析了
        season_data = json_data["details"].get(season,None)
        if season_data == None:
            print(f"[贝娜]找不到肉鸽季度"+season)
            continue
        # 读取藏品数据
        item_data = season_data.get("relics",{})
        item_list = season_data.get("items",{})
        for item_key,item_info in item_list.items():
            item_name = item_info["name"]
            if item_key in item_data: # 有藏品数据，说明是藏品或者类似的东西
                item = RogueItem(season,item_key,item_info,item_data[item_key])
                ROGUELIKE_TOPIC_KEYS.append(season+"|"+item_key)
                ROGUELIKE_TOPIC_TABLE[season][item_key] = item
                print(f"[贝娜]已读取肉鸽藏品 {item_name}（{item_key}）")
            #else: 非藏品先不显示了
            #    item = RogueItem(season,item_key,item_info)
            #    ROGUELIKE_TOPIC_KEYS.append(season+"|"+item_key)
            #    ROGUELIKE_TOPIC_TABLE[season][item_key] = item
            #    print(f"[贝娜]已读取其他肉鸽物品 {item_name}（{item_key}）")
    print(f"[贝娜]已完成对roguelike_topic_table.json的读取！")