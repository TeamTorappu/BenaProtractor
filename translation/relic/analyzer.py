import json
import os

ANNE_DICTIONARY = None
GAP = 0.000000001

# 读取字典数据
def set_dictionary(dictionary):
    global ANNE_DICTIONARY
    ANNE_DICTIONARY = dictionary.copy()
        
# 安妮的查字典方法
# 如果查不到会返回原文
def anne_dictionary(catalogue,type_str):
    return ANNE_DICTIONARY[catalogue].get(type_str,type_str)
    
#----------------------------------------
# 数值文本化逻辑
#----------------------------------------
# 将数值加成改成+/-X的格式，如果结尾是.0还会自动删去
def to_delta(addition_value):
    # 去无意义小数
    if abs(addition_value - round(addition_value)) < GAP: 
        addition_value = round(addition_value)
    # 检查正负
    if addition_value < 0:
        return str(addition_value) # 负数本来就有符号
    else:
        return "+"+str(addition_value)

# 将数值加成改成X%格式，如果结尾是.0还会自动删去
# 可以要求提供正负符号，当然负数本来就有符号。
def to_percent(power_value,negative_need_plus_one=False):
    percent_value = power_value * 100
    # 如果为负则加一的可选项
    if negative_need_plus_one and percent_value < 0:
        percent_value += 100
    # 去无意义小数
    if abs(percent_value - round(percent_value)) < GAP: 
        percent_value = round(percent_value)
    # 检查正负（外部应该会自己加上符号，因此负数要打个括号）
    if percent_value < 0:
        return "("+str(percent_value)+")%"
    else:
        return str(percent_value)+"%"

# 将数值加成改成+/-X%格式，如果结尾是.0还会自动删去
# 可以要求提供正负符号，当然负数本来就有符号。
def to_delta_percent(power_value):
    percent_value = power_value * 100
    # 去无意义小数
    if abs(percent_value - round(percent_value)) < GAP: 
        percent_value = round(percent_value)
    # 检查正负
    if percent_value < 0:
        return str(percent_value)+"%" # 负数本来就有符号
    else:
        return "+"+str(percent_value)+"%"

#----------------------------------------
# 解析逻辑
#----------------------------------------
# 生效时点的处理
# 返回生效时间的字符串。
def analyze_timing(item_type,blackboard):
    # 根据触发类型...
    trig_type = "GAIN"
    if "trig_type" in blackboard:
        trig_type = blackboard["trig_type"]
    # 界园钱特殊处理
    if item_type == "COPPER_BUFF":
        return anne_dictionary("trig_type_copper",trig_type)
    # 返回时点文本
    return anne_dictionary("trig_type",trig_type)

# 职业筛选的处理
# 返回职业的字符串。说明筛选的职业以及“干员”和“召唤物”这样的称呼
def analyze_profession(self,profession_mask):
    profession_mask = profession_mask.upper()
    masked_list = [profession_mask]
    if "," in profession_mask:
        masked_list = profession_mask.split(",")
    elif "|" in profession_mask:
        masked_list = profession_mask.split("|")
    # 如果大于等于8职业的话有可能是用于筛所有干员的，进行缩减处理
    if len(masked_list) >= 8 and "PIONEER" in masked_list and "WARRIOR" in masked_list and "TANK" in masked_list and "SNIPER" in masked_list and "CASTER" in masked_list and "SUPPORT" in masked_list and "MEDIC" in masked_list and "SPECIAL" in masked_list:
        if "TOKEN" in masked_list and "TRAP" in masked_list:
            return "干员、召唤物、装置"
        elif "TOKEN" in masked_list:
            return "干员、召唤物"
        elif "TRAP" in masked_list:
            return "干员、装置"
        else:
            return "干员"
    else:
        professions = []
        objects = []
        for masked in masked_list:
            if masked in ["TOKEN","TRAP"]:
                objects.append(anne_dictionary("profession",masked))
            else:
                professions.append(anne_dictionary("profession",masked))
        return "、".join(["/".join(professions)+"干员"] + objects)

# 整个选择器的处理
# 返回选择器称呼的字符串。说明筛选的职业、部署类型以及“干员”和“召唤物”这样的称呼
def analyze_selector(self,blackboard,prefix="",suffix=""):
    # 部署类型处理
    place = ""
    if "selector.buildable" in blackboard:
        if blackboard["selector.buildable"] == "melee":
            place = "部署类型为近战位的"
        elif blackboard["selector.buildable"] == "ranged":
            place = "部署类型为远程位的"
    # 职业筛选处理，没有默认全部单位
    if "selector.profession" in blackboard:
        target_name = analyze_profession(blackboard["selector.profession"])
        return f"所有{place}{prefix}{target_name}{suffix}"
    else:
        return f"所有{place}{prefix}单位{suffix}"

# 道具的处理
# 返回结构体，可能会带有链接
def analyze_item(self,blackboard):
    if "id" in blackboard:
        item = ask_bena("rogue_item",blackboard["id"])
        if item != None:
            if item.type == "COPPER": # 界园钱的特殊处理
                return {
                    "main": f"让 {item.display_name} 加入玩家钱盒。",
                    "link": blackboard['id']
                }
            return {
                "main": f"给予玩家{item.display_type} {item.display_name} ×{math.floor(blackboard.get('count',0))}",
                "link": blackboard['id']
            }
        return {"main": f"给予玩家 {blackboard['id']} ×{math.floor(blackboard.get('count',0))}"}
    return {"main": f"尝试给予玩家物品，但因未配置物品ID，没有实际效果。"}