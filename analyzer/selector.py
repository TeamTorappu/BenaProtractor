#----------------------------------------
# 解析选择器
#----------------------------------------
from .profession import analyze_profession

# 整个选择器的处理
# 返回选择器称呼的字符串。说明筛选的职业、部署类型以及“干员”和“召唤物”这样的称呼
def analyze_selector(blackboard,prefix="",suffix=""):
    from bena import ask_bena_character, ask_bena_enemy

    # 部署类型处理
    features = []
    target_name = "单位"
    # 部署类型
    if "selector.buildable" in blackboard:
        if blackboard["selector.buildable"] == "melee":
            features.append("部署类型为近战位")
        elif blackboard["selector.buildable"] == "ranged":
            features.append("部署类型为远程位")
        elif blackboard["selector.buildable"] == "all":
            features.append("部署类型为全部位")
    # 地位级别
    if "selector.enemy_level_type" in blackboard:
        if blackboard["selector.enemy_level_type"] == "NORMAL":
            features.append("地位级别为普通")
        elif blackboard["selector.enemy_level_type"] == "ELITE":
            features.append("地位级别为精英")
        elif blackboard["selector.enemy_level_type"] == "BOSS":
            features.append("地位级别为领袖")
    elif "selector.boss_option" in blackboard: # 另一种写法
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
    # 角色类单位ID筛选
    if "selector.char" in blackboard:
        char_name = ask_bena_character(blackboard["selector.char"])
        if char_name != blackboard["selector.char"]:
            target_name = f" {char_name}（{blackboard['selector.char']}）"
        else:
            target_name = f" {blackboard['selector.char']} "
    # 敌人类单位ID筛选
    if "selector.enemy" in blackboard:
        enemy_name = ask_bena_enemy(blackboard["selector.enemy"])
        if enemy_name != blackboard["selector.enemy"]:
            target_name = f" {enemy_name}（{blackboard['selector.enemy']}）"
        else:
            target_name = f" {blackboard['selector.enemy']} "
        if "敌方" in prefix:
            prefix = prefix.replace("敌方","")
    # 敌人类ID反向筛选
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

# 藏品Gbuff选择器的覆写
def analyze_selector_target_options_override(target_options: dict,blackboard: dict={}):
    new_target_options = target_options.copy()
    # 部署类型
    if "selector.buildable" in blackboard:
        new_target_options["_buildableType"] = blackboard["selector.buildable"].upper()
    # 地位级别
    if "selector.enemy_level_type" in blackboard:
        new_target_options["_enemyLevelMask"] = blackboard["selector.enemy_level_type"]
    elif "selector.boss_option" in blackboard: # 另一种写法
        new_target_options["_enemyLevelMask"] = "BOSS"
    # 阵营筛选处理
    if "selector.side" in blackboard:
        new_target_options["targetSide"] = blackboard["selector.side"].upper()
    # 角色类单位ID筛选
    if "selector.char" in blackboard:
        new_target_options["_charId"] = blackboard["selector.char"]
    # 敌人类单位ID筛选
    if "selector.enemy" in blackboard:
        new_target_options["_enemyId"] = blackboard["selector.enemy"]
    # 敌人ID反向筛选
    if "selector.enemy_exclude" in blackboard:
        new_target_options["_excludeEnemyId"] = blackboard["selector.enemy_exclude"]
    # 职业筛选
    if "selector.profession" in blackboard:
        new_target_options["professionMask"] = blackboard["selector.profession"].upper().replace("|",", ")
    return new_target_options