'''
贝娜 - 分析组件
将yj的json解读为可以阅读的格式，主要是node
'''
import os
import json
from data_class import *
from translator import bena_dictionary

# 表格数据
BUFF_KEYS = []
BUFF_TABLE = {}
BUFF_TABLE_PATH = "./tables/buff_table.json"
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
        

# 读取buff_table.json，并解析
def load_buff_table():
    print(f"[贝娜]开始读取buff_table.json")
    json_data = {}
    # 获取文件数据
    with open(BUFF_TABLE_PATH,'r',encoding="UTF-8") as _f:
        json_data = json.load(_f)
    # 开始解析
    for buff_key in json_data.keys():
        # 测试用，先不加载别的东西
        #if not buff_template_key.startswith("act1autochess") or not buff_template_key.startswith("act2autochess"):
        #    continue

        buff = Buff(buff_key,json_data[buff_key])
        # 制作翻译版称呼
        buff.display_name = translate_buff_name(buff_key)
        BUFF_KEYS.append(buff_key)
        BUFF_TABLE[buff_key] = buff
        print(f"[贝娜]已读取Buff模板 {buff.display_name}（{buff_key}）")
    print(f"[贝娜]已完成对buff_table.json的读取！")

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
        # 制作翻译版称呼
        buff_template.display_name = translate_buff_name(buff_template_key)
        BUFF_TEMPLATE_KEYS.append(buff_template_key)
        BUFF_TEMPLATE_DATA[buff_template_key] = buff_template
        print(f"[贝娜]已读取Buff模板 {buff_template.display_name}（{buff_template_key}）")
    print(f"[贝娜]已完成对buff_template_data.json的读取！")

# 读取roguelike_topic_table.json，并解析
def load_roguelike_topic_table(season=5):
    print(f"[贝娜]开始读取roguelike_topic_table.json")
    json_data = {}
    # 获取文件数据
    with open(ROGUELIKE_TOPIC_TABLE_PATH,'r',encoding="UTF-8") as _f:
        json_data = json.load(_f)
    # 按季度读取需要的数据表
    season = "rogue_" + str(season)
    # 需要的东西都在details里，其他部分就不需要解析了
    season_data = json_data["details"].get(season,None)
    if season_data == None:
        print(f"[贝娜]找不到肉鸽季度"+season)
        return
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

# 询问贝娜一个ID有没有对应的数据，若没有将原路返回
def ask_bena(_type,input_id):
    if _type == "buff":
        if input_id in BUFF_KEYS:
            return BUFF_TABLE[input_id]
    elif _type == "buff_template":
        if input_id in BUFF_TEMPLATE_KEYS:
            return BUFF_TEMPLATE_DATA[input_id]
    elif _type == "rogue_item":
        if input_id in ROGUELIKE_TOPIC_KEYS:
            return ROGUELIKE_TOPIC_TABLE[input_id]
    return None

# 询问贝娜一个ID有没有对应的数据，若没有将原路返回
def ask_bena_translation(_type,input_id):
    if _type == "buff":
        if input_id in BUFF_KEYS:
            return BUFF_TABLE[input_id].display_name
        else:
            return translate_buff_name(input_id) #现场进行翻译
    elif _type == "buff_template":
        if input_id in BUFF_TEMPLATE_KEYS:
            return BUFF_TEMPLATE_DATA[input_id].display_name
        else:
            return translate_buff_name(input_id) #现场进行翻译
    elif _type == "rogue_item":
        if input_id in ROGUELIKE_TOPIC_KEYS:
            return ROGUELIKE_TOPIC_TABLE[input_id]
    return ""

# 将一段文本中所有以<>框起来的文本进行“翻译”
def translate_buff_name_in_text(text: str):
    while "<" in text and ">" in text:
        left_place = text.find("<")
        right_place = text.find(">")
        middle = text[left_place+1:right_place]
        while "<" in middle:
            left_place = text.find("<",left_place+1)
            middle = text[left_place+1:right_place]
        if middle in BUFF_KEYS:
            middle = BUFF_TABLE[middle].display_name
        elif middle in BUFF_TEMPLATE_KEYS:
            middle = BUFF_TEMPLATE_DATA[middle].display_name
        else:
            middle = translate_buff_name(middle) #现场进行翻译
        text = text[:left_place] + middle + text[right_place+1:]
    return text



# 字典深查询
# 返回可处理部分和不可处理部分
def deep_translate(catalogue,keys):
    read_value = bena_dictionary(catalogue,keys[0])
    if read_value != "":
        index = 1 # 0号已经用掉了
        if isinstance(read_value,dict): # 字典，尝试遍历
            while(len(keys) > index):
                if keys[index] in read_value:
                    read_value = read_value[keys[index]] # 深入
                    index += 1
                    if isinstance(read_value,str): # 已是文本，返回
                        break
                elif "" in read_value: # 没有合适的key了，尝试取此处的默认值
                    read_value = read_value[""]
                    break
                else:
                    break
                
        if isinstance(read_value,dict) and "" in read_value: # 如果此时还是个结构体，尝试取此处的默认值
            read_value = read_value[""]

        if isinstance(read_value,str):
            if len(keys) > index:
                return (read_value,keys[index:])
            else:
                return (read_value,[])
    return ("",keys) # 原路返回
            

# 尝试翻译buff的名字
def translate_buff_name(buff_key: str):
    prefix = ""
    if buff_key.startswith("["): #大前缀，一般是[g]
        right = buff_key.find("]")+1
        prefix = buff_key[:right]
        buff_key = buff_key[right:]
    if buff_key == "empty": # 使用率最高的模板，给点排面
        return "空白"
    keys = []
    extras = []
    result = []
    extra_result = []
    if "[" in buff_key and "]" in buff_key:
        keys = buff_key.split("[",1)
        for extra in keys[1].replace("[","").split("]"):
            if extra != "":
                extras.append(extra)
        keys = keys[0].split("_")
    elif "_" in buff_key:
        keys = buff_key.split("_")
    else: # 单词语，直接查询一下返回
        read_value = bena_dictionary("buff_prefix",buff_key)
        if read_value == "":
            read_value = bena_dictionary("buff_element",buff_key)
        if read_value != "":
            if isinstance(read_value,dict):
                if "" in read_value:
                    return read_value[""]
            else:
                return read_value
        return buff_key
    
    # 开头部分
    if len(keys) > 0:
        if keys[0] == "enemy": # 敌人类单位名称前缀
            keys.pop(0)
            if len(keys) >= 2 and keys[0] == "rogue" and keys[1] == "football" : # 你是肉鸽单位吗？双持剑士：我觉得我是
                result.append("仅剩的创意")
            elif len(keys) >= 2 and keys[1] == "2" and keys[0]+"_"+keys[1] in ENEMY_NAMES: # 那种带_2的敌人名字，虽然一般不会存在
                result.append(ENEMY_NAMES[keys.pop(0)+"_"+keys.pop(0)])
            elif len(keys) >= 1 and keys[0] in ENEMY_NAMES: # 敌人名字
                result.append(ENEMY_NAMES[keys.pop(0)])
            elif len(keys) >= 1:
                trans, keys = deep_translate("buff_prefix",["enemy"] + keys)
                if trans != "":
                    result.append(trans)
        elif keys[0] == "trap" and len(keys) > 1 and keys[1] in CHARACTER_NAMES: # 一部分装置名称前缀
            keys.pop(0)
            result.append(CHARACTER_NAMES[keys.pop(0)])
        elif keys[0] in ENEMY_NAMES and keys[0] != "rogue": # 敌人类单位名称
            result.append(ENEMY_NAMES[keys.pop(0)])
        elif keys[0] in CHARACTER_NAMES: # 角色类单位名称
            # 检查是否是 主人+召唤物 格式的名字
            if len(keys) >= 2 and (keys[0] + "_" + keys[1]) in CHARACTER_NAMES:
                result.append(CHARACTER_NAMES[keys.pop(0)+"_"+keys.pop(0)])
            else:
                result.append(CHARACTER_NAMES[keys.pop(0)])
        else: # 尝试读取prefix字典
            trans, keys = deep_translate("buff_prefix",keys)
            if trans != "":
                result.append(trans)
    
    # 中间部分
    if len(keys) > 0:
        # 循环处理
        while(len(keys) > 0):
            trans, keys = deep_translate("buff_element",keys)
            if trans != "":
                result.append(trans)
            else: # 无法翻译了，将剩余部分返还回去
                result += keys
                break
    
    # 附加部分
    if len(extras) > 0:
        # 循环处理
        while(len(extras) > 0):
            extra = extras.pop(0)
            if "_" in extra:
                extra_split = extra.split("_")
                sub_result = []
                while(len(extra_split) > 0):
                    trans, extra_split = deep_translate("buff_element",extra_split)
                    if trans != "":
                        sub_result.append(trans)
                    else: # 无法翻译了，将剩余部分返还回去
                        sub_result += extra_split
                        break
                extra_result.append("_".join(sub_result))
            else:
                trans, rest = deep_translate("buff_element",[extra])
                if trans != "":
                    extra_result.append(trans+"_".join(rest))
                else:
                    extra_result.append(extra)
    
    # 最后，返回
    return prefix + "_".join(result) + "".join(["["+extra+"]" for extra in extra_result])