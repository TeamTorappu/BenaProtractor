#----------------------------------------
# 解析目标选项
#----------------------------------------
from .profession import analyze_profession
from dictionary import anne_dictionary

# 解析目标选项的详细信息
# 返回结构体
def analyze_target_options(option: dict,relative_side=True,base_by_side = "ALLY"):
    from bena import ask_bena_character, ask_bena_enemy

    conditions = []
    # 阵营
    side = analyze_target_options_side(option,relative_side,base_by_side)
    if side != "":
        conditions.append(side)
    # 实体类型
    if option["targetCategory"] != "DEFAULT":
        conditions.append(anne_dictionary("entity_category",option["targetCategory"]))
    # 行动方式
    if option["targetMotion"] != "ALL":
        conditions.append(anne_dictionary("motion",option["targetMotion"]))
    # 单位类型
    if option["checkUnitType"]:
        conditions.append(anne_dictionary("unit_type",option["unitTypeMask"]))

    # 开始处理进阶选项
    descriptions = []
    # 如果没有额外选项，一些选项就没意义了
    if option["enableAdvancedOptions"]:
        descriptions.append("目标必须可选")
        descriptions += analyze_target_options_advance_options(option)
    # 行为覆写
    if option["purposeMask"] != "NONE":
        purpose = anne_dictionary("purpose",option["purposeMask"])
        descriptions.append(f"视为一次{purpose}")
    unit_name = "单位"
    # 职业筛选
    if option["professionMask"] != "NONE":
        unit_name = analyze_profession(option["professionMask"])

    # 一些藏品相关的参数
    # 必须为特定部署类型的单位
    if "_buildableType" in option:
        buildable = anne_dictionary("buildable_type",option["_buildableType"])
        conditions.append(f"部署位为{buildable}")
    # 必须是含有特定id的角色类单位
    if "_charId" in option:
        char_name = ask_bena_character(option["_charId"])
        if char_name != option["_charId"]:
            char_name += f"（{option['_charId']}）"
        #descriptions.append(f"必须是名为 {char_name} 的角色类单位")
        conditions.append(f"ID为\"{char_name}\"")
        unit_name = "角色类" + unit_name
    # 必须是特定地位级别的单位
    if "_enemyLevelMask" in option:
        enemy_level = anne_dictionary("enemy_level",option["_enemyLevelMask"])
        conditions.append(f"地位级别为{enemy_level}")
    # 必须是含有特定id的敌人类单位
    if "_enemyId" in option:
        enemy_name = ask_bena_enemy(option["_enemyId"])
        if enemy_name != option["_enemyId"]:
            enemy_name += f"（{option['_enemyId']}）"
        conditions.append(f"ID为\"{enemy_name}\"")
        unit_name = "敌人类" + unit_name
    # 排除特定id的敌人类单位
    if "_excludeEnemyId" in option:
        enemy_name = ask_bena_enemy(option["_excludeEnemyId"])
        if enemy_name != option["_excludeEnemyId"]:
            enemy_name += f"（{option['_excludeEnemyId']}）"
        conditions.append(f"ID不为\"{enemy_name}\"")
        if "敌人类" not in unit_name:
            unit_name = "敌人类" + unit_name

    if len(descriptions) > 0:
        return {
            "main" : "".join(conditions)+unit_name,
            "description" : "；".join(descriptions)
        }
    #最朴实无华的选择，没有任何附加条件
    return {
        "main" : "".join(conditions)+unit_name
    }

# 解析目标选项的阵营条件
# 返回阵营前缀词
def analyze_target_options_side(option: dict,relative_side = True,base_by_side = "ALLY"):
    advanced = option["enableAdvancedOptions"]
    # 阵营
    if option["targetSide"] != "ALL":
        if not advanced:
            if base_by_side == "ENEMY" and relative_side:
                # 本质是绝对阵营处理
                if option["targetSide"] == "ALLY":
                    return anne_dictionary("side_type","ENEMY")
                elif option == "ENEMY":
                    return anne_dictionary("side_type","BOTH_ALLY_AND_NEUTRAL")
                #elif option == "BOTH_ALLY_AND_ENEMY":
                #    main_conditions.append(anne_dictionary("side_type","ALL")
            else:
                return anne_dictionary("side_type",option["targetSide"])
        elif not option["ignoreTargetSide"] and option["targetSide"] != "ALL":
            if relative_side:
                return anne_dictionary("side_type_relative",option["targetSide"])
            else:
                return anne_dictionary("side_type",option["targetSide"])
    return ""

# 解析目标选项阵营以外的所有条件（用于表述globalbuff）
# 返回列表
def analyze_target_options_conditions(option: dict):
    from bena import ask_bena_character, ask_bena_enemy

    conditions = []
    main_conditions = []
    # 职业筛选
    if option["professionMask"] != "NONE":
        conditions.append(analyze_profession(option["professionMask"],True))
    # 实体类型
    if option["targetCategory"] != "DEFAULT":
        conditions.append(anne_dictionary("entity_category",option["targetCategory"]))
    # 行动方式
    if option["targetMotion"] != "ALL":
        conditions.append(anne_dictionary("motion",option["targetMotion"]))
    # 单位类型
    if option["checkUnitType"]:
        conditions.append(anne_dictionary("unit_type",option["unitTypeMask"]))

    # 一些藏品相关的参数
    # 必须为特定部署类型的单位
    if "_buildableType" in option:
        buildable = anne_dictionary("buildable_type",option["_buildableType"])
        conditions.append(f"部署位为{buildable}")
    # 必须是含有特定id的角色类单位
    if "_charId" in option:
        char_name = ask_bena_character(option["_charId"])
        if char_name != option["_charId"]:
            char_name += f"（{option['_charId']}）"
        #descriptions.append(f"必须是名为 {char_name} 的角色类单位")
        conditions.append(f"ID为\"{char_name}\"")
        if "角色类" not in main_conditions:
            main_conditions.append(f"角色类")
    # 必须是特定地位级别的单位
    if "_enemyLevelMask" in option:
        enemy_level = anne_dictionary("enemy_level",option["_enemyLevelMask"])
        conditions.append(f"地位级别为{enemy_level}")
    # 必须是含有特定id的敌人类单位
    if "_enemyId" in option:
        enemy_name = ask_bena_enemy(option["_enemyId"])
        if enemy_name != option["_enemyId"]:
            enemy_name += f"（{option['_enemyId']}）"
        conditions.append(f"ID为\"{enemy_name}\"")
        if "敌人类" not in main_conditions:
            main_conditions.append(f"敌人类")
    # 排除特定id的敌人类单位
    if "_excludeEnemyId" in option:
        enemy_name = ask_bena_enemy(option["_excludeEnemyId"])
        if enemy_name != option["_excludeEnemyId"]:
            enemy_name += f"（{option['_excludeEnemyId']}）"
        conditions.append(f"ID不为\"{enemy_name}\"")
        if "敌人类" not in main_conditions:
            main_conditions.append(f"敌人类")

    return conditions + main_conditions

# 解析目标选项的所有进阶选项（或称可选性）
# 返回列表
def analyze_target_options_advance_options(option: dict):
    features = []
    # 无视无法选择
    if option["ignoreTargetFree"]:
        if option["onlyIgnoreSomeOfTargetFreeCase"]:
            if option["abnormalFlag"] != "E_NUM":
                abnormal_flag = anne_dictionary("abnormal",option["abnormalFlag"])
                if option["abnormalCombo"] != "E_NUM":
                    abnormal_combo = anne_dictionary("abnormal",option["abnormalCombo"])
                    features.append("无视"+abnormal_flag+"/"+abnormal_combo+"的可选性影响")
                else:
                    features.append("无视"+abnormal_flag+"的可选性影响")
            if option["abnormalCombo"] != "E_NUM":
                abnormal_combo = anne_dictionary("abnormal",option["abnormalCombo"])
                features.append("无视"+abnormal_combo+"的可选性影响")
        else:
            features.append("无视无法选择")
    # 无视孤立
    if option["ignoreAllyTargetFree"]:
        features.append("无视孤立")
    # 无视禁疗
    if option["ignoreHealFree"]:
        features.append("无视禁疗")
    # 排除特定有异常效果单位
    if "excludeSomeAbnormalFlags" in option and option["excludeSomeAbnormalFlags"]:
        abnormal_flag = anne_dictionary("abnormal",option["excludeAbnormalFlag"])
        features.append(f"不影响持有{abnormal_flag}异常的单位")
    # 必须含有特定异常效果单位
    if "containSomeAbnormalFlags" in option and option["containSomeAbnormalFlags"]:
        abnormal_flag = anne_dictionary("abnormal",option["containAbnormalFlag"])
        features.append(f"仅影响持有{abnormal_flag}异常的单位")
    return features