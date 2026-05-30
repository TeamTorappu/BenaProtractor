#----------------------------------------
# 藏品符文效果
#----------------------------------------
import math

from bena import ask_bena
from .analyzer import analyze_timing, anne_dictionary, to_delta_percent, to_delta, analyze_selector, is_attribute_key, to_percent

# 角色属性乘法藏品符文
def rogue_char_attribute_mul(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = anne_dictionary("attribute",key.upper())
            power = to_delta_percent(value) # +/-X%
            modifiers.append(f"{name}{power}（藏品符文）")
    # 选择器目标处理
    selector = analyze_selector(blackboard,"我方")
    hint = "（均为藏品符文）" if len(modifiers) > 1 else "（藏品符文）"
    return {"main" : f"{timing}所有{selector}{'、'.join(modifiers)}{hint}"}

# 角色属性加法藏品符文
def rogue_char_attribute_add(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = anne_dictionary("attribute",key.upper())
            num = to_delta(value) # +/-X
            modifiers.append(f"{name}{num}（")
    # 选择器目标处理
    selector = analyze_selector(blackboard,"我方")
    hint = "（均为藏品符文）" if len(modifiers) > 1 else "（藏品符文）"
    return {"main" : f"{timing}所有{selector}{'、'.join(modifiers)}{hint}"}

# 依照层数增加角色属性
def rogue_layer_char_attribute_mul(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = anne_dictionary("attribute",key.upper())
            num = to_delta_percent(value) # +/-X%
            modifiers.append(f"{name}+{num}")
    # 选择器目标处理
    selector = analyze_selector(blackboard,"我方")
    hint = "（均为藏品符文）" if len(modifiers) > 1 else "（藏品符文）"
    # 依照持有的“物品”数量增加角色属性
    if "stack_by_res" in blackboard:
        need_item_key = blackboard["stack_by_res"]
        need_item = ask_bena("rogue_item",need_item_key)
        need_var = math.floor(blackboard["stack_by_res_cnt"])
        return {
            "main" : f"{timing}每有{need_var}个 {need_item.display_name}（向下取整），{selector}{'、'.join(modifiers)}{hint}",
            "link" : "rogue_item." + need_item_key
        }
    else: # 普通叠层
        return {"main" : f"{timing}每有一层叠加层数，所有{selector}{'、'.join(modifiers)}{hint}"}

# 依照层数增加角色属性
def rogue_layer_char_attribute_add(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = anne_dictionary("attribute",key.upper())
            power = to_delta(value) # +/-X
            modifiers.append(f"{name}{power}")
    # 选择器目标处理
    selector = analyze_selector(blackboard,"我方")
    hint = "（均为藏品符文）" if len(modifiers) > 1 else "（藏品符文）"
    # 依照持有的“物品”数量增加角色属性
    if "stack_by_res" in blackboard:
        need_item_key = blackboard["stack_by_res"]
        need_item = ask_bena("rogue_item",need_item_key)
        need_var = math.floor(blackboard["stack_by_res_cnt"])
        return {
            "main" : f"{timing}每有{need_var}个 {need_item.display_name}（向下取整），{selector}{'、'.join(modifiers)}{hint}",
            "link" : "rogue_item." + need_item_key
        }
    else: # 普通叠层
        return {"main" : f"{timing}每有一层叠加层数，所有{selector}{'、'.join(modifiers)}{hint}"}

# 敌人属性乘法藏品符文
def rogue_enemy_attribute_mul(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = anne_dictionary("attribute",key.upper())
            power = to_delta_percent(value) # +/-X%
            modifiers.append(f"{name}{power}")
    # 选择器目标处理
    selector = analyze_selector(blackboard,"敌方")
    hint = "（均为藏品符文）" if len(modifiers) > 1 else "（藏品符文）"
    return {"main" : f"{timing}所有{selector}{'、'.join(modifiers)}{hint}"}

# 敌人属性加法藏品符文
def rogue_enemy_attribute_add(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = anne_dictionary("attribute",key.upper())
            num = to_delta(value) # +/-X
            modifiers.append(f"{name}{num}")
    # 选择器目标处理
    selector = analyze_selector(blackboard,"敌方")
    hint = "（均为藏品符文）" if len(modifiers) > 1 else "（藏品符文）"
    return {"main" : f"{timing}所有{selector}{'、'.join(modifiers)}{hint}"}
