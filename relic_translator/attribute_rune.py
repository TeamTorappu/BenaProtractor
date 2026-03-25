#----------------------------------------
# 藏品符文效果
#----------------------------------------
from .analyzer import anne_dictionary, to_delta_percent, to_delta, analyze_selector, is_attribute_key

# 角色属性乘法藏品符文
def rogue_char_attribute_mul(item_type,blackboard):
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = anne_dictionary("attribute",key.upper())
            power = to_delta_percent(value) # +/-X%
            modifiers.append(f"{name}{power}(藏品符文)")
    # 选择器目标处理
    selector = analyze_selector(blackboard,"我方")
    return {"main" : f"{selector}"+"、".join(modifiers)}

# 角色属性加法藏品符文
def rogue_char_attribute_add(item_type,blackboard):
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = anne_dictionary("attribute",key.upper())
            num = to_delta(value) # +/-X
            modifiers.append(f"{name}{num}(藏品符文)")
    # 选择器目标处理
    selector = analyze_selector(blackboard,"我方")
    return {"main" : f"{selector}"+"、".join(modifiers)}

# 依照持有的“物品”数量增加角色属性
def rogue_layer_char_attribute_add(item_type,blackboard):
    need_item_key = blackboard["stack_by_res"]
    need_item = ask_bena("rogue_item",need_item)
    need_var = math.floor(blackboard["stack_by_res_cnt"])
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = anne_dictionary("attribute",key.upper())
            num = to_delta(value) # +/-X
            modifiers.append(f"{name}{num}(藏品符文)")
    # 选择器目标处理
    selector = analyze_selector(blackboard,"我方")
    return {
        "main" : f"每有{need_var}个 {need_item}（向下取整），{selector}"+"、".join(modifiers),
        "link" : need_item_key
    }