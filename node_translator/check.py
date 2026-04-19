#----------------------------------------
# 检查类Node
#----------------------------------------
from bena import ENEMY_NAMES

from .analyzer import analyze_FP, anne_dictionary

# 检查异常效果（带免疫）
def node_CheckAbnormalFlag(node):
    target_name = anne_dictionary("target",node["_targetType"])
    abnormal_flag = ""
    if node["_abnormalFlagKey"]:
        abnormal_flag = f"记录在黑板({node['_abnormalFlagKey']})的异常效果"
    else:
        abnormal_flag = anne_dictionary("abnormal",node["_abnormalFlag"])+"异常"
    if node["_isUnset"]:
        return {
            "main" : f"检查{target_name}是否持有{abnormal_flag}（考虑免疫）",
            "true" : f"若不持有{abnormal_flag}",
            "false" : f"若持有{abnormal_flag}"
        }
    else:
        return {
            "main" : f"检查{target_name}是否持有{abnormal_flag}（考虑免疫）",
            "true" : f"若持有{abnormal_flag}",
            "false" : f"若不持有{abnormal_flag}"
        }

# 检查异常免疫
def node_CheckAbnormalImmune(node):
    target_name = anne_dictionary("target",node["_targetType"])
    abnormal = anne_dictionary("abnormal",node["_abnormalFlag"])
    if node["_isUnset"]:
        return {
            "main" : f"检查{target_name}的异常免疫",
            "true" : f"若{target_name}没有{abnormal}免疫",
            "false" : f"若{target_name}具有{abnormal}免疫"
        }
    else:
        return {
            "main" : f"检查{target_name}的异常免疫",
            "true" : f"若{target_name}具有{abnormal}免疫",
            "false" : f"若{target_name}没有{abnormal}免疫"
        }

# 检查持有多个异常效果之一（带免疫）
def node_CheckAbnormalFlags(node):
    target_name = anne_dictionary("target",node["_targetType"])
    abnormal_flags = []
    if node["_abnormalFlags"] != None:
        for abf in node["_abnormalFlags"]:
            abnormal_flags.append(anne_dictionary("abnormal",abf))
    if len(abnormal_flags) > 1:
        return {
            "main" : f"检查{target_name}是否持有"+"、".join(abnormal_flags[:-1]) + "或" + abnormal_flags[-1]+"异常（考虑免疫）",
            "true" : f"若持有上述异常之一",
            "false" : f"若不持有这些异常"
        }
    else:
        return {
            "main" : f"检查{target_name}是否持有{abnormal_flags[0]}异常（考虑免疫）",
            "true" : f"若持有{abnormal_flags[0]}",
            "false" : f"若不持有{abnormal_flags[0]}"
        }

# 检查异常组合（带免疫）
def node_CheckAbnormalCombo(node):
    target_name = anne_dictionary("target",node["_targetType"])
    abnormal_combo = anne_dictionary("abnormal",node["_abnormalCombo"])+"异常组合"
    if node["_isUnset"]:
        return {
            "main" : f"检查{target_name}是否持有{abnormal_combo}",
            "true" : f"若不持有{abnormal_combo}或免疫该异常组合",
            "false" : f"若持有{abnormal_combo}"
        }
    else:
        return {
            "main" : f"检查{target_name}是否持有{abnormal_combo}",
            "true" : f"若持有{abnormal_combo}",
            "false" : f"若不持有{abnormal_combo}或免疫该异常组合"
        }

# 检查职业
def node_CheckTargetProfession(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_readProfessionFromBlackboard"]:
        return {
            "main" : f"检查{target_name}的职业是否隶属于黑板记录的职业之一",
            "true" : "若其隶属于这些职业之一",
            "false" : "若其不属于这些职业中的任何一个"
        }
    else:
        professions = [anne_dictionary("profession",p) for p in node["_profession"]]
        sub_professions = []
        if node["_checkSubProfession"] and node["_subProfessions"] != None:
            sub_professions = [anne_dictionary("sub_profession",p) for p in node["_subProfessions"]]
        if len(professions) > 1:
            if len(sub_professions) > 1: # 一般不会用到
                return {
                    "main" : f"检查{target_name}是否为"+"/".join(professions)+"职业，且是否为"+"/".join(sub_professions)+"分支",
                    "true" : "若其满足职业条件，且属于上述分支之一",
                    "false" : "若其不满足职业条件或不属于上述分支之一"
                }
            elif len(sub_professions) == 1:
                return {
                    "main" : f"检查{target_name}是否为"+"/".join(professions)+"职业，且是否为"+sub_professions[0]+"分支",
                    "true" : "若其满足职业条件，且属于该分支",
                    "false" : "若其不满足职业条件，或不属于该分支"
                }
            else:
                return {
                    "main" : f"检查{target_name}是否为"+"/".join(professions)+"职业",
                    "true" : "若其满足职业条件",
                    "false" : "若其不满足职业条件"
                }
        elif len(professions) == 1:
            if len(sub_professions) > 1: # 一般不会用到
                return {
                    "main" : f"检查{target_name}是否为"+professions[0]+"职业，且是否为"+"/".join(sub_professions)+"分支",
                    "true" : "若其为该职业，且属于上述分支之一",
                    "false" : "若其不为该职业，或不属于上述分支之一"
                }
            elif len(sub_professions) == 1:
                return {
                    "main" : f"检查{target_name}是否为"+"/".join(professions)+"职业，且是否为"+sub_professions[0]+"分支",
                    "true" : "若其为该职业，且属于该分支",
                    "false" : "若其不为该职业，或不属于该分支"
                }
            else:
                return {
                    "main" : f"检查{target_name}是否为"+professions[0]+"职业",
                    "true" : "若其为"+professions[0],
                    "false" : "若其不为"+professions[0]
                }
        else:
            if len(sub_professions) > 1:
                return {
                    "main" : f"检查{target_name}是否为"+"/".join(sub_professions)+"分支",
                    "true" : "若其属于上述分支之一",
                    "false" : "若其不属于上述分支之一"
                }
            elif len(sub_professions) == 1:
                return {
                    "main" : f"检查{target_name}是否为"+sub_professions[0]+"分支",
                    "true" : "若其属于该分支",
                    "false" : "若其不属于该分支"
                }
            else:
                return {
                    "main" : f"检查{target_name}职业，但未配置职业条件",
                    "true" : "始终通过",
                    "false" : "始终不通过"
                }

# 检查标签
def node_CheckFilterTag(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_bbKey"] != None and node["_bbKey"] != "":
        return {
            "main" : "",
            "true" : f"若{target_name}具有黑板({node['_bbKey']})上记录的标签",
            "false" : f"若{target_name}不具有黑板({node['_bbKey']})上记录的标签"
        }
    else:
        return {
            "main" : "",
            "true" : f"若{target_name}具有\"{node['_filterTag']}\"标签",
            "false" : f"若{target_name}不具有\"{node['_filterTag']}\"标签"
        }

# 检查势力
def node_CheckCharacterGroupTag(node):
    target_name = anne_dictionary("target",node["_targetType"])
    group_name = anne_dictionary("group_tag",node["_groupTag"])
    return {
        "main" : f"检查{target_name}的势力标签",
        "true" : f"若其隶属于{group_name}势力",
        "false" : f"若其不隶属于{group_name}势力"
    }


# 检查阻挡模式
def node_CheckBlockMode(node):
    target_name = anne_dictionary("target",node["_targetType"])
    block_mode = anne_dictionary("block_mode",node["_blockMode"])
    return {
        "main" : f"检查{target_name}的阻挡模式",
        "true" : f"若其阻挡模式为 {block_mode}",
        "false" : f"若其阻挡模式为 {block_mode}"
    }

# 检查阻挡状态
def node_CheckBlocked(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_checkBlockedBySource"]:
        source_name = anne_dictionary("target",node["_sourceType"])
        if node["_checkBlockedBySourceToken"]:
            source_name += "或其召唤物"
        return {
            "main" : f"根据单位类型，检查{target_name}的阻挡/被阻挡状态",
            "true" : f"若其正被{source_name}阻挡/阻挡着{source_name}",
            "false" : f"若其未被{source_name}阻挡/未阻挡{source_name}"
        }
    elif node["_checkBlockedBySourceToken"]:
        source_name = anne_dictionary("target",node["_sourceType"])+"的召唤物"
        return {
            "main" : f"根据单位类型，检查{target_name}的阻挡/被阻挡状态",
            "true" : f"若其正被{source_name}阻挡/阻挡着{source_name}",
            "false" : f"若其未被{source_name}阻挡/未阻挡{source_name}"
        }
    else:
        return {
            "main" : f"根据单位类型，检查{target_name}的阻挡/被阻挡状态",
            "true" : f"若其正被任意单位阻挡/阻挡着任意单位",
            "false" : f"若其未阻挡/未被阻挡"
        }

# 通用目标检查
def node_IfTarget(node):
    target_name = anne_dictionary("target",node["_targetType"])
    conditions = []
    last_type = ""
    if node["_checkTargetAlive"]:
        conditions.append("存活")
        last_type = "是否存活"
    if node["_checkTargetFree"]:
        conditions.append("对于来源而言可选")
        last_type = "对于来源而言是否可选"
    if node["_checkTargetUnitType"]:
        conditions.append("单位类型为"+anne_dictionary("unit_type",node["_unitType"]))
        last_type = "单位类型是否为"+anne_dictionary("unit_type",node["_unitType"])
    if node["_motionMask"] != "ALL":
        conditions.append("行动类型为"+anne_dictionary("motion",node["_motionMask"]))
        last_type = "行动类型是否为"+anne_dictionary("motion",node["_motionMask"])
    if node["_checkApplyWay"] and node["_applyWay"] == "MELEE": # 这个不是检查本次攻击的类型，是检查目标的
        conditions.append("属于\"近战\"单位")
        last_type = "是否属于\"近战\"单位"
    elif node["_checkApplyWay"] and node["_applyWay"] == "RANGED":
        conditions.append("属于\"远程\"单位")
        last_type = "是否属于\"远程\"单位"
    if len(conditions) > 1:
        return {
            "main" : f"检查{target_name}是否"+"、".join(conditions),
            "true" : f"若{target_name}均满足上述条件",
            "false" : f"若{target_name}不满足上述任一条件"
        }
    elif len(conditions) == 1:
        return {
            "main" : f"检查"+target_name+last_type,
            "true" : "若"+target_name+conditions[0],
            "false" : "若"+target_name+conditions[0].replace("属于","不属于").replace("为","不为")
        }
    else:
        return {
            "main" : f"检查{target_name}，但未配置条件",
            "true" : "始终通过",
            "false" : "始终不通过"
        }

# 检查单位是否存活
def node_CheckUnitAlive(node):
    owner_name = anne_dictionary("target",node["_ownerType"])
    return {
        "main" : f"检查{owner_name}目前是否存活",
        "true" : f"若{owner_name}仍存活（生命值不为0且不处于死亡状态机）",
        "false" : f"若{owner_name}已被击倒/死亡"
    }

# 检查绝对阵营
def node_IfTargetSide(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_sideMask"] in ["BOTH_ALLY_AND_ENEMY","ALL","NONE"]: # 无法判断的阵营类型
        #是的，沟槽的yj写的是全等于，因此这几个判定必定失败
        return {
            "main" : f"检查{target_name}的阵营（绝对阵营），但给入了错误的参数",
            "true" : f"始终不通过",
            "false" : f"始终通过"
        }
    side_type = anne_dictionary("side_type",node["_sideMask"])
    return {
        "main" : f"检查{target_name}的阵营（绝对阵营）",
        "true" : f"若其为{side_type}单位",
        "false" : f"若其不为{side_type}单位"
    }
    
# 是否属于干员
def node_IsCharacter(node):
    target_name = anne_dictionary("target",node["_targetType"])
    return {
        "main" : f"检查{target_name}的单位是否为干员（为角色类且为八大职业之一）",
        "true" : f"若其为干员",
        "false" : f"若其不为干员"
    }

# 是否属于角色类（干员、召唤物、装置）
def node_IsCharacterOrTokenOrTrap(node):
    target_name = anne_dictionary("target",node["_targetType"])
    return {
        "main" : f"检查{target_name}的单位类型",
        "true" : f"若其为角色类单位",
        "false" : f"若其不为角色类单位"
    }
    
# 是否属于敌人类
def node_IsEnemy(node):
    target_name = anne_dictionary("target",node["_targetType"])
    return {
        "main" : f"检查{target_name}的单位类型",
        "true" : f"若其为敌人类单位",
        "false" : f"若其不为敌人类单位"
    }

# 是否为同一人
def node_IfTargetEqual(node):
    left_target = anne_dictionary("target",node["_target1"])
    right_target = anne_dictionary("target",node["_target2"])
    if node["_equalIfBothNull"]:
        if left_target == right_target:
            return {
                "main" : f"检查{left_target}是否是自己",
                "true" : "始终通过",
                "false" : "始终不通过"
            }
        else:
            return {
                "main" : f"检查{left_target}和{right_target}",
                "true" : "若两者为同一个单位（或均不存在）",
                "false" : "若两者为不同单位（或一方存在一方不存在）"
            }
    else:
        if left_target == right_target: # 也就是说，不考虑两边对不对等，只考虑存不存在了
            return {
                "main" : f"检查{left_target}是否存在",
                "true" : f"若存在{left_target}",
                "false" : f"若不存在{left_target}"
            }
        else:
            return {
                "main" : f"检查{left_target}和{right_target}",
                "true" : "若两者为同一个单位",
                "false" : "若两者为不同单位（或任意一方不存在）"
            }

# 另一种是否为同一人
# 没有任何“多余”的处理
def node_CheckEntityEquals(node):
    left_target = anne_dictionary("target",node["_lhsType"])
    right_target = anne_dictionary("target",node["_rhsType"])
    if left_target == right_target:
        return {
            "main" : f"检查单位，但配置有误",
            "true" : "始终通过",
            "false" : "始终不通过"
        }
    else:
        return {
            "main" : f"检查{left_target}和{right_target}",
            "true" : "若两者为同一个单位（或均不存在）",
            "false" : "若两者为不同单位（或一方存在一方不存在）"
        }
    
# 检查行动类型
def node_CheckMotionMode(node):
    target_name = anne_dictionary("target",node["_targetType"])
    motion = anne_dictionary("motion",node["_mode"])
    return {
        "main" : f"检查{target_name}的行动模式",
        "true" : f"若其当前为{motion}单位",
        "false" : f"若其当前为{motion}单位"
    }

# 追溯角色类单位死亡原因
def node_FilterCharacterLastDeathReason(node):
    target_name = anne_dictionary("target",node["_characterType"])
    finish_reason = anne_dictionary("finish_reason",node["_finishReason"])
    return {
        "main" : f"追溯{target_name}（角色类）最近一次退场/死亡的原因",
        "true" : f"若该次退场/死亡原因为\"{finish_reason}\"",
        "false" : f"若该次退场/死亡原因不为\"{finish_reason}\"，或没有退场/死亡"
    }

# 检查单位本次死亡原因
def node_FilterDeathReason(node):
    target_name = anne_dictionary("target",node["_source"])
    finish_reason = anne_dictionary("finish_reason",node["_finishReason"])
    return {
        "main" : f"检查{target_name}的本次退场/死亡原因",
        "true" : f"若退场/死亡原因为\"{finish_reason}\"",
        "false" : f"若退场/死亡原因不为\"{finish_reason}\""
    }

# 检查角色部署类型
def node_CheckBuildableType(node):
    target_name = anne_dictionary("target",node["_target"])
    buildable_type = anne_dictionary("buildable_type",node["_buildableType"])
    if node["_checkOriginCondition"]:
        return {
            "main" : f"检查{target_name}（角色类）的原始部署类型（不受舞鞋等效果影响）",
            "true" : f"若其原始部署类型为{buildable_type}",
            "false" : f"若其原始部署类型不为{buildable_type}"
        }
    else:
        return {
            "main" : f"检查{target_name}（角色类）的部署类型",
            "true" : f"若其部署类型为{buildable_type}",
            "false" : f"若其部署类型不为{buildable_type}"
        }

# 检查敌人地位级别
def node_CheckEnemyLevelMask(node):
    target_name = anne_dictionary("target",node["_targetType"])
    enemy_level = anne_dictionary("enemy_level",node["_targetLevelMask"])
    return {
        "main" : f"检查{target_name}（敌人类）的地位级别",
        "true" : f"若其为{enemy_level}地位的敌人",
        "false" : f"若其不为{enemy_level}地位的敌人"
    }

# 检查地图标签（水地形、肉鸽、十三章等）
def node_CheckConatinsMapTags(node):
    map_tags = []
    if isinstance(node["_mapTags"],list):
        for tag in node["_mapTags"]:
            map_tags.append(anne_dictionary("map_tag",tag))
    # 虽然看着像和模式，但其实是写死的或模式
    map_tag = ""
    if len(map_tags) > 1:
        all_map_tag = "、".join(map_tags)
        return {
            "main" : f"检查当前关卡的地图TAG",
            "true" : f"若当前关卡具有{all_map_tag}TAG中的任意一个",
            "false" : f"若当前关卡均不具有{all_map_tag}TAG"
        }
    elif len(map_tags) == 1:
        return {
            "main" : f"检查当前关卡的地图TAG",
            "true" : f"若当前关卡具有{map_tags[0]}TAG",
            "false" : f"若当前关卡没有{map_tags[0]}TAG"
        }
    else:
        return {
            "main" : "检查当前关卡的地图TAG，但未配置检查对象",
            "true" : "始终通过",
            "false" : "始终不通过"
        }

# 检查对象所在地块的相对位置（普罗旺斯专属）
def node_CheckModifierDirectionOffset(node):
    # 未解析参数：_offset.col
    source_name = anne_dictionary("target",node["_source"])
    target_name = anne_dictionary("target",node["_target"])
    row = node["_offset"]["row"]
    #col = node["_offset"]["col"]
    condition = f"部署方向正前方的第{row}个地块"
    if node["_targetToSource"]:
        source_name,target_name = target_name,source_name
    if node["_exceptThisOffset"]:
        return {
            "main" : f"检查{target_name}所处的地块",
            "true" : f"若{target_name}位于{source_name}{condition}",
            "false" : f"若{target_name}位于{source_name}{condition}以外的地块"
        }
    else:
        return {
            "main" : f"检查{target_name}所处的地块",
            "true" : f"若{target_name}位于{source_name}{condition}以外的地块",
            "false" : f"若{target_name}位于{source_name}{condition}"
        }

# 检查对象所处地块是否位于某个攻击范围/半径内
def node_CheckTargetInRange(node):
    source_name = anne_dictionary("target",node["_soureceType"]) #对的yj真的多打了个e
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_autoRange"]:
        return {
            "main" : f"检查{target_name}是否位于{source_name}当前的攻击范围内（不考虑攻击范围延伸；中心判定）",
            "true" : f"若{target_name}位于攻击范围内",
            "false" : f"若{target_name}位于攻击范围外"
        }
    elif node["_checkRadius"]:
        return {
            "main" : f"检查{target_name}是否位于{source_name}半径{node['_rangeRadius']}格内（中心判定）",
            "true" : f"若{target_name}位于此半径内",
            "false" : f"若{target_name}位于此半径外"
        }
    else:
        return {
            "main" : f"检查{target_name}是否位于{source_name}部署位置与方向的特定范围（ID：{node['_rangeId']}）内（中心判定）",
            "true" : f"若{target_name}位于该范围内",
            "false" : f"若{target_name}位于该范围外"
        }

# 检查特定范围内是否存在其他友方“可点选”单位
def node_CheckOtherCharacterInRange(node):
    source_name = anne_dictionary("target",node["_source"])
    return {
        "main" : f"检查{source_name}部署位置与方向的特定范围（ID：{node['_rangeId']}）内是否存在其他同阵营\"可点选\"的单位",
        "description" : "\"可点选\"的判定方式如同博士亲手点击该地块中央时可以点击到的所有单位",
        "true" : "若该范围内存在至少一个此类单位",
        "false" : "若该范围内不存在此类单位"
    }

# 检查目标重量
def node_FilterByTargetMassLevel(node):
    target_name = anne_dictionary("target",node["_target"])
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    return {
        "main" : f"检查{target_name}的重量",
        "true" : f"若其重量 {compare} [value]",
        "false" : f"若其重量 {compare_not} [value]"
    }

# 检查目标生命
def node_FilterByTargetHp(node):
    target_name = anne_dictionary("target",node["_targetType"])
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    default_value = analyze_FP(node["_hpValue"])
    return {
        "main" : f"检查{target_name}当前生命值",
        "true" : f"若其当前生命值 {compare} [hp]（默认{default_value}）",
        "false" : f"若其当前生命值 {compare_not} [hp]（默认{default_value}）"
    }

# 检查目标生命比例
def node_FilterByTargetHpRatio(node):
    target_name = anne_dictionary("target",node["_targetType"])
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    if node["_useSourceHpRatio"]:
        source_name = anne_dictionary("target",node["_sourceType"])
        return {
            "main" : f"检查{target_name}与{source_name}当前生命比例（生命/最大生命值）",
            "true" : f"若{target_name}的生命比例 {compare} {source_name}的生命比例",
            "false" : f"若{target_name}的生命比例 {compare_not} {source_name}的生命比例"
        }
    else:
        default_value = node["_value"]
        prefix = node["_blackboardPrefix"].lower() if node["_blackboardPrefix"] else "" # 对的这玩意自带一次小写化
        return {
            "main" : f"检查{target_name}当前生命比例（生命/最大生命值）",
            "true" : f"若其生命比例 {compare} [{prefix}hp_ratio]（默认{default_value}）",
            "false" : f"若其生命比例 {compare_not} [{prefix}hp_ratio]（默认{default_value}）"
        }

# 检查目标技力比例
def node_FilterByTargetSpRatio(node):
    target_name = anne_dictionary("target",node["_target"])
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    default_value = node["_spRatio"]
    return {
        "main" : f"检查{target_name}当前技力比例（技力/技力上限）",
        "true" : f"若其技力比例 {compare} [sp_ratio]（默认{default_value}）",
        "false" : f"若其技力比例 {compare_not} [sp_ratio]（默认{default_value}）"
    }

# 检查目标当前损伤元素的比例
def node_FilterByTargetEpRatio(node):
    target_name = anne_dictionary("target",node["_targetType"])
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    default_value = node["_epRatio"]
    return {
        "main" : f"检查{target_name}当前元素损伤程度（当前损伤元素的元素值/元素上限，\"爆条\"期间视为100%）",
        "true" : f"若其元素损伤程度 {compare} [ep_ratio]（默认{default_value}）",
        "false" : f"若其元素损伤程度 {compare_not} [ep_ratio]（默认{default_value}）"
    }

# 检查目标属性
def node_FilterByTargetAttribute(node):
    target_name = anne_dictionary("target",node["_target"])
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    attribute = anne_dictionary("attribute",node["_attributeType"])
    default_value = node["_value"] if node["_useFloat"] else node["_valueFP"] # 我寻思怎么取都是float，为什么还得分这个？
    if default_value != 0:
        return {
            "main" : f"检查{target_name}的{attribute}",
            "true" : f"若其{attribute} {compare} [value]",
            "false" : f"若其{attribute} {compare_not} [value]"
        }
    else:
        return {
            "main" : f"检查{target_name}的{attribute}",
            "true" : f"若其{attribute} {compare} [value]（默认{default_value}）",
            "false" : f"若其{attribute} {compare_not} [value]（默认{default_value}）"
        }

# 检查目标元素值是否为全满/特定元素值是否为满
def node_CheckTargetEpIsFull(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_elementType"] != None and node["_elementType"] != "":
        element = anne_dictionary("element",node["_elementType"])
        return {
            "main" : f"检查{target_name}的{element}元素值",
            "true" : f"若其{element}元素值 ≥ 其元素上限且不处于\"爆条\"状态",
            "false" : f"若其{element}元素值 < 其元素上限或处于\"爆条\"状态"
        }
    else:
        return {
            "main" : f"检查{target_name}的所有类型的元素值",
            "true" : f"若其所有元素值均 ≥ 其元素上限且不处于\"爆条\"状态",
            "false" : f"若其任何一项元素值 < 其元素上限，或其处于\"爆条\"状态"
        }

# 检查目标等级
def node_FilterByTargetDataLevel(node):
    target_name = anne_dictionary("target",node["_target"])
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    return {
        "main" : f"检查{target_name}的等级数据（不考虑精英化）",
        "true" : f"若其等级 {compare} {node['_level']}",
        "false" : f"若其等级 {compare_not} {node['_level']}"
    }

# 检查技力类型
def node_FilterByTargetSPType(node):
    target_name = anne_dictionary("target",node["_targetType"])
    sp_type = anne_dictionary("sp_type",node["_spType"])
    return {
        "main" : f"检查{target_name}的技力类型",
        "true" : f"若其技力类型为 {sp_type} ",
        "false" : f"若其技力类型为 {sp_type} "
    }

# 检查所处地块
def node_CheckCurrentTileKey(node):
    target_name = anne_dictionary("target",node["_target"])
    tile_keys = []
    for tile_key in node["_tileKey"]:
        tile_keys.append(tile_key) # 需翻译
    result ={
        "main" : f"检查{target_name}所处的地块是否为"+"、".join(tile_keys),
        "true" : f"若其位于此类地块之一",
        "false" : f"若其不位于此类地块"
    }
    if node["_isExclude"]:
        result["true"],result["false"] = result["false"],result["true"]
    return result

# 检查敌人类单位的ID
def node_CheckEnemyId(node):
    target_name = anne_dictionary("target",node["_targetType"])
    enemy_names = []
    if not node["_loadIdFromBb"]:
        for enemy_id in node["_filterIds"]:
            if "_" in enemy_id and enemy_id.startswith("enemy_"):
                enemy_name = enemy_id.split("_")[2] # 这是实际ID，就看这个就好
                if enemy_name in ENEMY_NAMES:
                    enemy_names.append(ENEMY_NAMES[enemy_name])
                else:
                    enemy_names.append(enemy_id)
    result = None
    if node["_loadIdFromBb"]:
        result = {
            "main" : f"检查{target_name}（敌人类）的ID是否为黑板[enemy_key]记述的ID",
            "true" : f"若该敌人为该ID的敌人",
            "false" : f"若该敌人不为该ID的敌人"
        }
    elif len(enemy_names) > 1:
        result = {
            "main" : f"检查{target_name}（敌人类）是否为 "+"、".join(enemy_names) + " 之一",
            "description" : "即检查ID是否为："+"；".join(node["_filterIds"]),
            "true" : f"若该敌人在上述敌人之一",
            "false" : f"若该敌人不为上述敌人之一"
        }
    else:
        result = {
            "main" : f"检查{target_name}（敌人类）是否为 "+enemy_names[0],
            "description" : "即检查ID是否为："+node["_filterIds"][0],
            "true" : f"若该敌人为 {enemy_names[0]}",
            "false" : f"若该敌人不为 {enemy_names[0]}"
        }
    if node["_isUnset"]:
        result["true"],result["false"] = result["false"],result["true"]
    return result

# 检查当前单位模式
def node_CheckUnitCurrentMode(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_loadCurModeBbKey"] != None:
        return {
            "main" : f"检查{target_name}当前的模式编号是否为黑板[{node['_loadCurModeBbKey']}]记述的编号",
            "true" : f"若其单位当前模式为[{node['_loadCurModeBbKey']}]号模式",
            "false" : f"若其单位当前模式不为[{node['_loadCurModeBbKey']}]号模式"
        }
    else:
        return {
            "main" : f"检查{target_name}当前的模式编号",
            "true" : f"若其单位当前模式为{node['_checkCurModeIndex']}号模式",
            "false" : f"若其单位当前模式不为{node['_checkCurModeIndex']}号模式"
        }