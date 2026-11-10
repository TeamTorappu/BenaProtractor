#----------------------------------------
# 贝娜 - 分析组件
# 将yj的json解读为可以阅读的格式，主要是node
#----------------------------------------





'''
#----------------------------------------
# 数据加载
#----------------------------------------
'''
'''
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

# 加载敌人名称表，若不存在将现场生成一个
def load_autochess_table():
    if not os.path.exists(AUTOCHESS_TABLE_PATH):
        print("[贝娜]不存在activity_table_autochess.json或已过时！开始重新生成该文件")
        split_activity_table();
    # 获取文件数据
    with open(AUTOCHESS_TABLE_PATH ,'r',encoding="UTF-8") as _f:
        AUTOCHESS_TABLE = json.load(_f)
    print("[贝娜]activity_table_autochess.json读取完毕！")

# 读取buff_table.json，并解析
def load_buff_table():
    if not os.path.exists(BUFF_TEMPLATE_DATA_PATH):
        print(f"[贝娜]未能找到buff_table.json，取消读取...")
        return
    print(f"[贝娜]开始读取buff_table.json...")
    json_data = {}
    # 获取文件数据
    with open(BUFF_TABLE_PATH,'r',encoding="UTF-8") as _f:
        json_data = json.load(_f)
    # 开始解析
    for buff_key in json_data.keys():
        buff = Buff(buff_key,json_data[buff_key])
        # 制作翻译版称呼
        buff.display_name = translate_buff_name(buff_key)
        BUFF_KEYS.append(buff_key)
        BUFF_TABLE[buff_key] = buff
        print(f"[贝娜]已读取Buff {buff.display_name}（{buff_key}）")
    print(f"[贝娜]已完成对buff_table.json的读取！")

# 读取buff_template_data.json，并解析
def load_buff_template_data():
    if not os.path.exists(BUFF_TEMPLATE_DATA_PATH):
        print(f"[贝娜]未能找到buff_template_data.json，取消读取...")
        return
    print(f"[贝娜]开始读取buff_template_data.json...")
    json_data = {}
    # 获取文件数据
    with open(BUFF_TEMPLATE_DATA_PATH,'r',encoding="UTF-8") as _f:
        json_data = json.load(_f)
    # 开始解析
    for buff_template_key in json_data.keys():
        # 测试用，仅加载部分内容
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
    if not os.path.exists(ROGUELIKE_TOPIC_TABLE_PATH):
        print(f"[贝娜]未能找到roguelike_topic_table.json，取消读取...")
        return
    print(f"[贝娜]开始读取roguelike_topic_table.json...")
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
    
# 读取global_buff_dummy.json，并解析
def load_global_buff_dummy():
    if not os.path.exists(GLOBAL_BUFF_DUMMY_PATH):
        print(f"[贝娜]未能找到global_buff_dummy.json，取消读取...")
        return
    print(f"[贝娜]开始读取global_buff_dummy.json...")
    json_data = {}
    # 获取文件数据
    with open(GLOBAL_BUFF_DUMMY_PATH,'r',encoding="UTF-8") as _f:
        json_data = json.load(_f)
    # 开始解析
    for buff_key in json_data.keys():
        buff = GlobalBuff(buff_key,json_data[buff_key])
        # 制作翻译版称呼
        buff.display_name = translate_buff_name(buff_key)
        GLOBAL_BUFF_KEYS.append(buff_key)
        GLOBAL_BUFF_DUMMY[buff_key] = buff
        print(f"[贝娜]已读取GBuff {buff.display_name}（{buff_key}）")
    print(f"[贝娜]已完成对global_buff_dummy.json的读取！")
'''