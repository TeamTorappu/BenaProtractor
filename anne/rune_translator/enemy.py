#----------------------------------------
# 敌人类符文
#----------------------------------------
from analyzer import is_attribute_key,to_delta,to_percent,to_delta_percent,analyze_profession
from dictionary import enum_dictionary

# 解析敌人类使用的符文选择
# 返回敌人称呼
def __enemy_selector(blackboard,selector):
    from bena import ask_bena_enemy
    if selector == None:
        return "敌人类单位"
    conditions = []
    name = "单位"
    #if selector["professionMask"] != 1023: # 职业掩码
    #    name = analyze_profession(selector["professionMask"])
    if "enemy" in blackboard:
        enemy_ids = blackboard["enemy"].split("|")
        enemies = []
        for enemy_id in enemy_ids:
            enemy_name = ask_bena_enemy(enemy_id)
            if enemy_name != enemy_id:
                enemies.append(f"{enemy_name}（{enemy_id}）")
            else:
                enemies.append(f"{enemy_id}")
        return "、".join(enemies)
    if len(conditions) > 0:
        return "、".join(conditions) + "的敌人类"+name
    return "敌人类"+name

# 角色属性加法符文
def enemy_attribute_add(blackboard,selector=None):
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = enum_dictionary("attribute",key.upper())
            power = to_delta(value) # +X
            modifiers.append(f"{name}{power}")
    # 选择器目标处理
    selector_str = __enemy_selector(blackboard,selector)
    hint = "（均为加法符文）" if len(modifiers) > 1 else "（加法符文）"
    return {"main" : f"所有{selector_str}{'、'.join(modifiers)}{hint}"}

# 敌人属性乘法符文
def enemy_attribute_mul(blackboard,selector=None):
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = enum_dictionary("attribute",key.upper())
            power = to_percent(value) # ×X%
            modifiers.append(f"{name}×{power}")
    # 选择器目标处理
    selector_str = __enemy_selector(blackboard,selector)
    hint = "（均为乘法符文）" if len(modifiers) > 1 else "（乘法符文）"
    return {"main" : f"所有{selector_str}{'、'.join(modifiers)}{hint}"}

# 敌人属性加乘符文
def enemy_attribute_additive_mul(blackboard,selector=None):
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = enum_dictionary("attribute",key.upper())
            power = to_delta_percent(value) # +X%
            modifiers.append(f"{name}{power}")
    # 选择器目标处理
    selector_str = __enemy_selector(blackboard,selector)
    hint = "（均为加乘符文）" if len(modifiers) > 1 else "（加乘符文）"
    return {"main" : f"所有{selector_str}{'、'.join(modifiers)}{hint}"}

# 敌人的敌用技能冷却修改
def enemy_skill_cd_mul(blackboard,selector=None):
    selector_str = __enemy_selector(blackboard,selector)
    scale = float(blackboard["scale"]) if "scale" in blackboard else 1.0
    power = to_percent(scale)
    return {"main" : f"关卡配置中所有{selector_str}的所有技能冷却×{power}"}

# 敌人的攻击半径修改
def enemy_attackradius_mul(blackboard,selector=None):
    selector_str = __enemy_selector(blackboard,selector)
    scale = float(blackboard["scale"]) if "scale" in blackboard else 1.0
    power = to_percent(scale)
    return {"main" : f"关卡配置中所有{selector_str}的基础攻击范围半径×{power}"}

# 给敌人添加一个动态能力
def enemy_dynamic_ability_new(blackboard,selector=None):
    selector_str = __enemy_selector(blackboard,selector)
    if "key" in blackboard:
        return {"main" : f"为所有{selector_str}添加一个动态能力：{blackboard['key']}"}
    else:
        return {"main" : f"为所有{selector_str}添加零个动态能力"}

# 替换敌人
def level_enemy_replace(blackboard,selector=None):
    from bena import ask_bena_enemy
    if "key" in blackboard and "value" in blackboard:
        from_enemy_name = ask_bena_enemy(blackboard["key"])
        if from_enemy_name != blackboard["key"]:
            from_enemy_name = f"{from_enemy_name}（{blackboard['key']}）"
        to_enemy_name = ask_bena_enemy(blackboard["value"])
        if to_enemy_name != blackboard["value"]:
            to_enemy_name = f"{to_enemy_name}（{blackboard['value']}）"
        return {
            "main" : f"将关卡出怪中的所有 {from_enemy_name} 替换为 {to_enemy_name}",
            "description" : "仅替换出怪，数据采用配置中的新单位配置，同一编号的敌人路径不发生变化"
        }
    return {"main" : f"尝试将关卡出怪中的敌人替换，但未配置替换对象"}
    