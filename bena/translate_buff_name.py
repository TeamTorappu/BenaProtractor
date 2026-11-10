#----------------------------------------
# 翻译Buff名
#----------------------------------------
from dictionary import bena_dictionary

# 字典深查询
# 返回可处理部分和不可处理部分
def deep_translate(catalogue,keys):
    key_num = len(keys)
    read_value = bena_dictionary(catalogue,keys[0])
    if read_value != "":
        # 单项匹配
        if key_num == 1:
            if isinstance(read_value,dict) and "" in read_value: # 如果此时还是个结构体，尝试取此处的默认值
                return (read_value[""],[])
            elif isinstance(read_value,str): # 如果是字符串，直接返回
                return (read_value,[])
            else:
                return ("",keys) # 原路返回，表示无法翻译

        # 深度翻译
        index = 1 # 0号已经用掉了
        if isinstance(read_value,dict): # 字典，尝试遍历
            while(key_num > index):
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
            if key_num > index:
                return (read_value,keys[index:])
            else:
                return (read_value,[])
    return ("",keys) # 原路返回，表示无法翻译
            

# 尝试翻译buff的名字
def translate_buff_name(buff_key: str):
    from bena import CATALOG
    # 直接匹配
    read_value = bena_dictionary("buff_name",buff_key)
    if read_value != "":
        return read_value
    
    # 拆分翻译
    prefix = ""
    if buff_key.startswith("["): #大前缀，一般是[g]
        right = buff_key.find("]")+1
        prefix = buff_key[:right]
        buff_key = buff_key[right:]
    keys = []
    extras = []
    result = []
    extra_result = []
    if "[" in buff_key and "]" in buff_key:
        keys = buff_key.split("[",1)
        extras = keys[1].replace("]","").split("[")
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

    # 获取角色名与敌人名
    character_names = CATALOG.character_display_names
    enemy_names = CATALOG.enemy_display_names
    
    # 开头部分
    if len(keys) > 0:
        if keys[0] == "enemy": # 敌人类单位名称前缀
            keys.pop(0)
            if len(keys) >= 2 and keys[1] == "2" and keys[0]+"_"+keys[1] in enemy_names: # 那种带_2的敌人名字，虽然一般不会存在
                result.append(enemy_names[keys.pop(0)+"_"+keys.pop(0)])
            elif len(keys) >= 1 and keys[0] in enemy_names: # 敌人名字
                result.append(enemy_names[keys.pop(0)])
            elif len(keys) >= 1:
                trans, keys = deep_translate("buff_prefix",["enemy"] + keys)
                if trans != "":
                    result.append(trans)
        elif keys[0] == "trap" and len(keys) > 1 and keys[1] in enemy_names: # 一部分装置名称前缀
            keys.pop(0)
            character_key = keys.pop(0)
            result.append(character_names.get(character_key, enemy_names.get(character_key, character_key)))
        elif keys[0] in enemy_names and keys[0] != "rogue": # 敌人类单位名称
            result.append(enemy_names[keys.pop(0)])
        elif keys[0] in character_names: # 角色类单位名称
            # 检查是否是 主人+召唤物 格式的名字
            if len(keys) >= 2 and (keys[0] + "_" + keys[1]) in character_names:
                result.append(character_names[keys.pop(0)+"_"+keys.pop(0)])
            else:
                result.append(character_names[keys.pop(0)])
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
            else: # 无法翻译了，返还回去
                result.append(keys.pop(0))
    
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
                    else: # 无法翻译了，返还回去
                        sub_result.append(extra_split.pop(0))
                extra_result.append("_".join(sub_result))
            else:
                trans, rest = deep_translate("buff_element",[extra])
                if trans != "":
                    extra_result.append(trans)
                else:
                    extra_result.append(extra)
    
    # 最后，返回
    return prefix + "_".join(result) + "".join(["["+extra+"]" for extra in extra_result])