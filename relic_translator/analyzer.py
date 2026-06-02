import json
import math
import os

from bena import ask_bena_enemy, ask_bena
from translator import anne_dictionary, is_anne_key
GAP = 0.000000001

# 获取key是否是属性值的方法
# 属性字典里存了所有属性类型，因此直接用了
def is_attribute_key(key: str):
    return is_anne_key("attribute",key.upper())
    
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
    if "trig_type" not in blackboard:
        return ""
    trig_type = blackboard["trig_type"]
    # 界园钱特殊处理
    if item_type == "COPPER_BUFF":
        return anne_dictionary("trig_type_copper",trig_type)+"，"
    # 返回时点文本
    return anne_dictionary("trig_type",trig_type)+"，"

# 职业筛选的处理
# 返回职业的字符串。说明筛选的职业以及“干员”和“召唤物”这样的称呼
def analyze_profession(profession_mask):
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
def analyze_selector(blackboard,prefix="",suffix=""):
    # 部署类型处理
    features = []
    target_name = "单位"
    # 部署类型
    if "selector.buildable" in blackboard:
        if blackboard["selector.buildable"] == "melee":
            features.append("部署类型为近战位")
        elif blackboard["selector.buildable"] == "ranged":
            features.append("部署类型为远程位")
    # 地位级别
    if "selector.enemy_level_type" in blackboard:
        if blackboard["selector.enemy_level_type"] == "NORMAL":
            features.append("地位级别为普通")
        elif blackboard["selector.enemy_level_type"] == "ELITE":
            features.append("地位级别为精英")
        elif blackboard["selector.enemy_level_type"] == "BOSS":
            features.append("地位级别为领袖")
    # 阵营筛选处理
    if "selector.side" in blackboard:
        if blackboard["selector.side"] == "enemy" and "敌方" not in prefix:
            prefix = "敌方"+prefix
        elif blackboard["selector.side"] == "ally" and "我方" not in prefix:
            prefix = "我方"+prefix
    # 职业筛选处理
    if "selector.profession" in blackboard:
        target_name = analyze_profession(blackboard["selector.profession"])
    # 敌人ID筛选
    if "selector.enemy" in blackboard:
        enemy_name = ask_bena_enemy(blackboard["selector.enemy"])
        if enemy_name != blackboard["selector.enemy"]:
            target_name = f" {enemy_name}（{blackboard['selector.enemy']}）"
        else:
            target_name = f" {blackboard['selector.enemy']} "
        if "敌方" in prefix:
            prefix = prefix.replace("敌方","")
    # 敌人ID反向筛选
    if "selector.enemy_exclude" in blackboard:
        enemy_excludes = []
        for enemy_id in blackboard["selector.enemy_exclude"].split("|"):
            enemy_name = ask_bena_enemy(enemy_id)
            if enemy_name != enemy_id:
                enemy_excludes.append(f"{enemy_name}（{enemy_id}）")
            else:
                enemy_excludes.append(f" {enemy_id} ")
        target_name = target_name + "（" + "；".join(enemy_excludes) + "除外）"
    if len(features) > 0:
        return f"{'、'.join(features)}的{prefix}{target_name}{suffix}"
    return f"{prefix}{target_name}{suffix}"

# 道具的处理
# 返回道具类
def analyze_item(blackboard):
    if "id" in blackboard:
        item = ask_bena("rogue_item",blackboard["id"])
        return item
    return None

# 道具奖励的处理
# 返回结构体，可能会带有链接
def analyze_item_reward(blackboard):
    item = analyze_item(blackboard)
    if item == None:
        if "id" in blackboard:
            if blackboard["id"].startswith("pool"):
                return {
                    "main" : f"给予玩家  {blackboard['id']} 奖池中的随机一个物品"
                }
            else:
                return {
                    "main" : f"给予玩家  {blackboard['id']} × {math.floor(blackboard.get('count',0))}",
                    "link" : blackboard['id']
                }
        else:
            return {
                "main" : "给予玩家 棍木",
                "link" : "minecraft.air"
            }
    if item.type == "COPPER": # 界园钱的特殊处理
        return {
            "main" : f"让 {item.display_name} 加入玩家钱盒",
            "link" : blackboard['id']
        }
    return {
        "main" : f"给予玩家 {item.display_name} × {math.floor(blackboard.get('count',0))}",
        "link" : blackboard['id']
    }
