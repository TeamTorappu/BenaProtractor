#----------------------------------------
# 检查类Node
#----------------------------------------
from .analyzer import anne_dictionary

# 检查黑板
def node_FilterByBlackboardValue(node):
    left_var = node["_blackboardKey"]
    right_var = node["_valueToCompare"]
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    if node["_anotherKeyToCompare"] != None: # 比对另一个黑板值
        right_var = node["_anotherKeyToCompare"]
        if node["_anotherBuff"] and node["_buffKey"] != None: # 比对另一个Buff的黑板值
            if node["_targetType"] != "BUFF_OWNER":
                target_name = anne_dictionary("target",node["_target"])
                return {
                    "main" : f"比对黑板上的{left_var}与{target_name}的另一buff({node['_buffKey']})的{right_var}",
                    "true" : f"若{left_var} {compare} {right_var}",
                    "false" : f"若{left_var} {compare_not} {right_var}"
                }
            else:
                return {
                    "main" : f"比对黑板上的{left_var}与另一buff({node['_buffKey']})的{right_var}",
                    "true" : f"若{left_var} {compare} {right_var}",
                    "false" : f"若{left_var} {compare_not} {right_var}"
                }
        else:
            return {
                "main" : f"比对黑板上的{left_var}与{right_var}",
                "true" : f"若{left_var} {compare} {right_var}",
                "false" : f"若{left_var} {compare_not} {right_var}"
            }
    else:
        return {
            "main" : f"检查黑板上的{left_var}",
            "true" : f"若{left_var} {compare} {right_var}",
            "false" : f"若{left_var} {compare_not} {right_var}"
        }

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
            "main" : f"检查{target_name}是否持有{abnormal_flag}",
            "true" : f"若不持有{abnormal_flag}或免疫该异常",
            "false" : f"若持有{abnormal_flag}"
        }
    else:
        return {
            "main" : f"检查{target_name}是否持有{abnormal_flag}",
            "true" : f"若持有{abnormal_flag}",
            "false" : f"若不持有{abnormal_flag}或免疫该异常"
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
def CheckTargetProfession(node):
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
    
# 检查调整值是否带有标记
def node_CheckModifierContainsKey(node):
    return {
        "main" : f"检查事件调整值是否具有{node['_customKey']}标记",
        "true" : f"若具有{node['_customKey']}标记",
        "false" : f"若没有{node['_customKey']}标记"
    }

# 检查阵营
def node_CheckCharacterGroupTag(node):
    target_name = anne_dictionary("target",node["_targetType"])
    group_name = node["_groupTag"] # 需要翻译
    return {
        #"main" : f"检查{target_name}阵营标签：{group_name}",
        "main" : f"检查{target_name}阵营标签",
        "true" : f"若其为{group_name}阵营",
        "false" : f"若其不为{group_name}阵营"
    }

# 检查重量
def node_FilterByTargetMassLevel(node):
    target_name = anne_dictionary("target",node["_target"])
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    return {
        #"main" : f"检查{target_name}的重量是否{compare}X",
        "main" : f"检查{target_name}的重量",
        "true" : f"若其重量 {compare} X",
        "false" : f"若其重量 {compare_not} X"
    }

# 检查阻挡状态
def node_CheckBlocked(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_checkBlockedBySource"]:
        source_name = anne_dictionary("target",node["_sourceType"])
        if node["_checkBlockedBySourceToken"]:
            source_name += "或其召唤物"
        return {
            "main" : f"检查{target_name}的阻挡状态（角色类与敌人类处理逻辑不同）",
            "true" : f"若其正被{source_name}阻挡，或阻挡着{source_name}",
            "false" : f"若其未被{source_name}阻挡，且未阻挡{source_name}"
        }
    elif node["_checkBlockedBySourceToken"]:
        source_name = anne_dictionary("target",node["_sourceType"])+"的召唤物"
        return {
            "main" : f"检查{target_name}的阻挡状态（角色类与敌人类处理逻辑不同）",
            "true" : f"若其正被{source_name}阻挡，或阻挡着{source_name}",
            "false" : f"若其未被{source_name}阻挡且未阻挡{source_name}"
        }
    else:
        return {
            "main" : f"检查{target_name}的阻挡状态（角色类与敌人类处理逻辑不同）",
            "true" : f"若其正被任意单位阻挡，或阻挡着任意单位",
            "false" : f"若其未阻挡且未被阻挡"
        }
        

# 检查是否持有某Buff
def node_CheckContainsBuff(node):
    # 未解析参数：_loadFromBlackboard _checkSourceHost
    target_name = anne_dictionary("target",node["_targetType"])
    condition = f"检查{target_name}是否"
    true_flag = "若其持有"
    false_flag = "若其没有"
    if node["isAND"]: # 与模式
        if len(node["_buffKeys"]) > 1:
            if node["_checkBuffSource"]:
                source_name = anne_dictionary("target",node["_buffSourceType"])
                condition += f"同时持有来自{source_name}的 {'、'.join(node['_buffKeys'])}"
            else:
                condition += f"同时持有 {'、'.join(node['_buffKeys'])}"
            true_flag = "若其全部持有"
            false_flag = "若其少了其中任意一个"
        elif len(node["_buffKeys"]) == 1:
            if node["_checkBuffSource"]:
                source_name = anne_dictionary("target",node["_buffSourceType"])
                condition += f"持有来自{source_name}的 {node['_buffKeys'][0]}"
            else:
                condition += f"持有 {node['_buffKeys'][0]}"
    else: # 或模式
        if len(node["_buffKeys"]) > 1:
            if node["_checkBuffSource"]:
                source_name = anne_dictionary("target",node["_buffSourceType"])
                condition += f"持有来自{source_name}的 {'、'.join(node['_buffKeys'])} 中的任意一个"
            else:
                condition += f"持有 {'、'.join(node['_buffKeys'])} 中的任意一个"
            true_flag = "若其持有其中任意一个"
            false_flag = "若其全部都没有"
        elif len(node["_buffKeys"]) == 1:
            if node["_checkBuffSource"]:
                source_name = anne_dictionary("target",node["_buffSourceType"])
                condition += f"持有来自{source_name}的 {node['_buffKeys'][0]}"
            else:
                condition += f"持有 {node['_buffKeys'][0]}"
    if condition != "" :
        return {
            "main" : condition,
            "true" : true_flag,
            "false" : false_flag
        }
    else:
        return {
            "main" : "检查Buff，但给定条件无法检查（写法有误？）",
            "true" : "（始终不执行）",
            "false" : "（始终不执行）"
        }

# 检查是否持有本Buff的某个子Buff
def node_CheckContainsDerviedBuff(node):
    return {
        "main" : f"检查本Buff的子Buff {node['_derviedBuffKey']}",
        "true" : "若Buff持有者同时还持有该子Buff",
        "false" : "若Buff持有者不持有该子Buff"
    }

# 检查黑板是否为0或未定义
def node_IsBlackboardZero(node):
    return {
        "main" : f"检查黑板{node['_var']}的值",
        "true" : f"若不存在或{node['_var']} = 0",
        "false" : f"若存在且{node['_var']} ≠ 0"
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

# 检查单位死亡原因
def node_FilterCharacterLastDeathReason(node):
    target_name = anne_dictionary("target",node["_characterType"])
    finish_reason = anne_dictionary("finish_reason",node["_finishReason"])
    return {
        "main" : f"检查{target_name}（角色类）的退场/死亡原因",
        "true" : f"若退场/死亡原因为\"{finish_reason}\"",
        "false" : f"若退场/死亡原因不为\"{finish_reason}\""
    }

# 检查角色部署类型
def node_CheckBuildableType(node):
    target_name = anne_dictionary("target",node["_characterType"])
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

# 检查角色技能状态
def node_CheckCharSkillAffecting(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_checkTargetHost"]:
        return {
            "main" : f"检查{target_name}（角色类）的技能状态（若对方为召唤物，改为检查其主人）",
            "true" : "若检查对象处于技能期间",
            "true" : "若检查对象不处于技能期间"
        }
    else:
        return {
            "main" : f"检查{target_name}（角色类）的技能状态",
            "true" : "若其处于技能期间",
            "true" : "若其不处于技能期间"
        }
    