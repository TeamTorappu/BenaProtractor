#----------------------------------------
# 角色类符文
#----------------------------------------
from analyzer import is_attribute_key,to_delta,to_percent,to_delta_percent,analyze_profession
from dictionary import enum_dictionary

# 解析角色类使用的符文选择
# 返回角色称呼
def __char_selector(blackboard,selector):
    if selector == None:
        return "角色类单位"
    conditions = []
    name = "单位"
    if selector["professionMask"] != 1023: # 职业掩码
        name = analyze_profession(selector["professionMask"])
    if selector["buildableMask"] != "ALL": # 部署类型
        if selector["buildableMask"] == "MELEE":
            conditions.append("部署类型为近战位")
        elif selector["buildableMask"] == "RANGED":
            conditions.append("部署类型为远程位")
    if len(conditions) > 0:
        return "、".join(conditions) + "的角色类"+name
    return "角色类"+name

# 角色属性加法符文
def char_attribute_add(blackboard,selector=None):
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = enum_dictionary("attribute",key.upper())
            power = to_delta(value) # +X
            modifiers.append(f"{name}{power}")
    # 选择器目标处理
    selector_str = __char_selector(blackboard,selector)
    hint = "（均为加法符文）" if len(modifiers) > 1 else "（加法符文）"
    return {"main" : f"所有{selector_str}{'、'.join(modifiers)}{hint}"}

# 角色属性乘法符文
def char_attribute_mul(blackboard,selector=None):
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = enum_dictionary("attribute",key.upper())
            power = to_percent(value) # ×X%
            modifiers.append(f"{name}×{power}")
    # 选择器目标处理
    selector_str = __char_selector(blackboard,selector)
    hint = "（均为乘法符文）" if len(modifiers) > 1 else "（乘法符文）"
    return {"main" : f"所有{selector_str}{'、'.join(modifiers)}{hint}"}

# 角色属性加乘符文
def char_attribute_additive_mul(blackboard,selector=None):
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = enum_dictionary("attribute",key.upper())
            power = to_delta_percent(value) # +X%
            modifiers.append(f"{name}{power}")
    # 选择器目标处理
    selector_str = __char_selector(blackboard,selector)
    hint = "（均为加乘符文）" if len(modifiers) > 1 else "（加乘符文）"
    return {"main" : f"所有{selector_str}{'、'.join(modifiers)}{hint}"}

# 禁用角色
def char_exclude(blackboard,selector=None):
    selector_str = __char_selector(blackboard,selector)
    return {"main" : f"禁用玩家携带的所有{selector_str}（视为未携带对应干员）"}

# 角色费用增加
def char_cost_add(blackboard,selector=None):
    selector_str = __char_selector(blackboard,selector)
    value = int(blackboard["value"]) if "value" in blackboard else 0
    power = to_delta(value)
    return {"main" : f"玩家携带的所有{selector_str}基础部署费用{power}"}

# 给角色添加一个动态能力
def char_dynamic_ability_new(blackboard,selector=None):
    selector_str = __char_selector(blackboard,selector)
    if "key" in blackboard:
        return {"main" : f"为所有{selector_str}添加一个动态能力：{blackboard['key']}"}
    else:
        return {"main" : f"为所有{selector_str}添加零个动态能力"}