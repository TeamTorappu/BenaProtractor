'''
贝娜 - 分析组件
将yj的json解读为可以阅读的格式，主要是node
'''
import os
import json
from data_class import *

# 表格数据
BUFF_TEMPLATE_KEYS = []
BUFF_TEMPLATE_DATA = {}
BUFF_TEMPLATE_DATA_PATH = "./tables/buff_template_data.json"
CHARACTER_KEYS = []
CHARACTER_TABLE = {}
CHARACTER_TABLE_PATH = "./tables/character_table.json"
CHARACTER_SHORT_NAMES = {}
CHARACTER_NAMES = {}
CHARACTER_NAMES_PATH = "./tables/character_names.json"
ENEMY_DATABASE_KEYS = []
ENEMY_DATABASE = {}
ENEMY_DATABASE_PATH = "./tables/enemy_database.json"
ENEMY_SHORT_NAMES = {}
ENEMY_NAMES = {}
ENEMY_NAMES_PATH = "./tables/enemy_names.json"
ROGUELIKE_TOPIC_SEASONS = ["rogue_5"]#["rogue_1","rogue_2","rogue_3","rogue_4","rogue_5"]
ROGUELIKE_TOPIC_KEYS = []
ROGUELIKE_TOPIC_TABLE = {}
ROGUELIKE_TOPIC_TABLE_PATH = "./tables/roguelike_topic_table.json"
print("[贝娜]我叫贝娜，来找一个出门就忘了回家的笨蛋。听说她还有些活要干，没办法，我也在这陪她一会好了。")

# 读取character_table.json，将获取到的名称制作成一个单独的json以供使用。
def make_character_name_table():
    print(f"[贝娜]开始读取character_table.json")
    json_data = {}
    # 获取文件数据
    with open(CHARACTER_TABLE_PATH,'r',encoding="UTF-8") as _f:
        json_data = json.load(_f)
    # 开始解析
    for character_key in json_data.keys():
        character_name = json_data[character_key].get("name","未知")
        if "_" in character_key: # 为了方便，只保留翻译器需要的最后一部分
            character_key = "_".join(character_key.split("_")[2:])
        CHARACTER_NAMES[character_key] = character_name
        print(f"[贝娜]已读取到干员 {character_name}（{character_key}）")
    print(f"[贝娜]已完成对character_table.json的读取！")
    # 写入文件供未来使用
    print(f"[贝娜]现在开始将干员的ID与名称对照记录至character_names.json")
    with open(CHARACTER_NAMES_PATH ,'w',encoding="UTF-8") as _f:
        _f.write(json.dumps(CHARACTER_NAMES,indent=4,ensure_ascii=False))
    print(f"[贝娜]character_names.json记录完毕！")

# 加载角色名称表，若不存在将现场生成一个
def load_character_names():
    if not os.path.exists(CHARACTER_NAMES_PATH):
        print("[贝娜]不存在character_names.json或已过时！开始重新生成该文件")
        make_character_name_table()
    else:
        # 获取文件数据
        with open(CHARACTER_NAMES_PATH,'r',encoding="UTF-8") as _f:
            json_data = json.load(_f)
        for key,name in json_data.items():
            CHARACTER_NAMES[key] = name
        print("[贝娜]character_names.json读取完毕！")

# 读取enemy_database.json，将获取到的名称制作成一个单独的json以供使用。
def make_enemy_name_table():
    print(f"[贝娜]开始读取enemy_database.json")
    json_data = {}
    # 获取文件数据
    with open(ENEMY_DATABASE_PATH,'r',encoding="UTF-8") as _f:
        json_data = json.load(_f)
    # 开始解析
    for enemy_struct in json_data["enemies"]:
        enemy_key = enemy_struct.get("Key")
        enemy_name = enemy_struct.get("Value")[0]["enemyData"]["name"]["m_value"]
        if "_" in enemy_key: # 为了方便，只保留翻译器需要的最后一部分
            enemy_key = "_".join(enemy_key.split("_")[2:])
        ENEMY_NAMES[enemy_key] = enemy_name
        print(f"[贝娜]已读取到敌人 {enemy_name}（{enemy_key}）")
    print(f"[贝娜]已完成对enemy_table.json的读取！")
    # 写入文件供未来使用
    print(f"[贝娜]现在开始将干员的ID与名称对照记录至enemy_names.json")
    with open(ENEMY_NAMES_PATH ,'w',encoding="UTF-8") as _f:
        _f.write(json.dumps(ENEMY_NAMES,indent=4,ensure_ascii=False))
    print(f"[贝娜]enemy_names.json记录完毕！")

# 加载敌人名称表，若不存在将现场生成一个
def load_enemy_names():
    if not os.path.exists(ENEMY_NAMES_PATH):
        print("[贝娜]不存在enemy_names.json或已过时！开始重新生成该文件")
        make_enemy_name_table()
    else:
        # 获取文件数据
        with open(ENEMY_NAMES_PATH,'r',encoding="UTF-8") as _f:
            json_data = json.load(_f)
        for key,name in json_data.items():
            ENEMY_NAMES[key] = name
        print("[贝娜]enemy_names.json读取完毕！")

# 读取buff_template_data.json，并解析
def load_buff_template_data():
    print(f"[贝娜]开始读取buff_template_data.json")
    json_data = {}
    # 获取文件数据
    with open(BUFF_TEMPLATE_DATA_PATH,'r',encoding="UTF-8") as _f:
        json_data = json.load(_f)
    # 开始解析
    for buff_template_key in json_data.keys():
        # 测试用，先不加载别的东西
        #if not buff_template_key.startswith("act1autochess") or not buff_template_key.startswith("act2autochess"):
        #    continue

        buff_template = BuffTemplate(buff_template_key,json_data[buff_template_key])
        # 制作翻译版称呼，先处理特征明显的
        if buff_template_key.startswith("act1autochess_"): # 卫戍协议：盟约
            buff_template.display_name = "卫戍盟约_"+buff_template.display_name[14:]
        elif buff_template_key.startswith("act2autochess_"): # 卫戍协议：盟约 下半
            buff_template.display_name = "卫戍下半_"+buff_template.display_name[14:]
        elif buff_template_key.startswith("enemy_"): # 敌人类
            display_name = ""
            keys = buff_template_key[6:].replace("[","_[").split("_")
            rest = []
            processed = False
            # 处理敌方单位名称的使用
            if len(keys) > 1 and keys[1] == "2": # 那种名字带_2的敌人，不过一般不会出现
                info_key = keys[0]+"_"+keys[1]
                if info_key in ENEMY_NAMES:
                    display_name = "敌_" + ENEMY_NAMES[info_key]
                    processed = True
                    if len(keys) > 2:
                        rest = keys[2:]
            if not processed and len(keys) > 0 and keys[0] in ENEMY_NAMES: # 敌人名字为首的buff
                display_name = "敌_" + ENEMY_NAMES[keys[0]]
                processed = True
                if len(keys) > 1:
                    rest = keys[1:]
            
            if processed and len(rest) > 0: # 处理剩下的部分，可能是天赋或技能？
                if rest[0] == "t":
                    display_name += "天赋"
                    rest.pop(0)
                elif rest[0] == "s":
                    if len(rest) > 1 and rest[1] in ["1","2","3"]:
                        display_name += rest[1]+"技能"
                        rest.pop(0)
                        rest.pop(0)
                    else:
                        display_name += "技能"
                        rest.pop(0)
                # 无法翻译的部分退回去
                if len(rest) > 0:
                    display_name += "_" + "_".join(rest)
                buff_template.display_name = display_name
        elif "_" in buff_template_key: # 然后碰碰运气，看看是不是干员的
            display_name = ""
            keys = buff_template_key.replace("[","_[").split("_")
            # 名字为首的buff
            if keys[0] in CHARACTER_NAMES:
                display_name = CHARACTER_NAMES[keys[0]]
                if len(keys) > 1: # 处理剩下的部分，可能是天赋或技能？
                    rest = keys[1:]
                    if rest[0] == "t":
                        if len(rest) > 1 and rest[1] in ["1","2","3"]:
                            display_name += rest[1]+"天赋"
                            rest.pop(0)
                            rest.pop(0)
                        else:
                            display_name += "天赋"
                            rest.pop(0)
                    elif rest[0] == "t1":
                        display_name += "1天赋"
                        rest.pop(0)
                    elif rest[0] == "t2":
                        display_name += "2天赋"
                        rest.pop(0)
                    elif rest[0] == "tr":
                        display_name += "特性"
                        rest.pop(0)
                    elif rest[0] == "trait":
                        display_name += "特性"
                        rest.pop(0)
                    elif rest[0] == "s":
                        if len(rest) > 1 and rest[1] in ["1","2","3"]:
                            display_name += rest[1]+"技能"
                            rest.pop(0)
                            rest.pop(0)
                        else:
                            display_name += "技能"
                            rest.pop(0)
                    elif rest[0] == "s1":
                        display_name += "1技能"
                        rest.pop(0)
                    elif rest[0] == "s2":
                        display_name += "2技能"
                        rest.pop(0)
                    elif rest[0] == "s3":
                        display_name += "3技能"
                        rest.pop(0)
                    elif rest[0] == "e":
                        if len(rest) > 1:
                            display_name += "模组"+rest[1]
                            rest.pop(0)
                            rest.pop(0)
                        else:
                            display_name += "模组"
                            rest.pop(0)
                # 无法翻译的部分退回去
                if len(rest) > 0:
                    if rest[0].startswith("["):
                        display_name += "_".join(rest)
                    else:
                        display_name += "_" + "_".join(rest)
                buff_template.display_name = display_name
        BUFF_TEMPLATE_KEYS.append(buff_template_key)
        BUFF_TEMPLATE_DATA[buff_template_key] = buff_template
        print(f"[贝娜]已读取Buff模板 {buff_template.display_name}（{buff_template_key}）")
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
        # 需要的东西都在details里，其他部分就不需要解析了
        season_data = json_data["details"].get(season,None)
        if season_data == None:
            print(f"[贝娜]找不到肉鸽季度"+season)
            continue
        # 读取藏品数据
        item_data = season_data.get("relics",{})
        item_list = season_data.get("items",{})
        for item_key,item_info in item_list.items():
            if item_key in item_data: # 有藏品数据，说明是藏品或者类似的东西
                item = RogueItem(season,item_key,item_info,item_data[item_key])
                ROGUELIKE_TOPIC_KEYS.append(item_key)
                ROGUELIKE_TOPIC_TABLE[item_key] = item
                print(f"[贝娜]已读取肉鸽{item.display_type} {item.display_name}（{item_key}）")
            else: # 非藏品
                item = RogueItem(season,item_key,item_info)
                ROGUELIKE_TOPIC_KEYS.append(item_key)
                ROGUELIKE_TOPIC_TABLE[item_key] = item
                print(f"[贝娜]已读取肉鸽{item.display_type} {item.display_name}（{item_key}）")
    print(f"[贝娜]已完成对roguelike_topic_table.json的读取！")

# 询问贝娜一个ID有没有对应的译名，若没有将原路返回
def ask_bena(_type,input_id):
    if _type == "buff_template":
        if input_id in BUFF_TEMPLATE_KEYS:
            return BUFF_TEMPLATE_DATA[input_id]
    elif _type == "rogue_item":
        if input_id in ROGUELIKE_TOPIC_KEYS:
            return ROGUELIKE_TOPIC_TABLE[input_id]
    return None