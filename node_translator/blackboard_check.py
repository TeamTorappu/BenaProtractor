#----------------------------------------
# 黑板检查类Node
#----------------------------------------
from dictionary import anne_dictionary

# 检查黑板
def FilterByBlackboardValue(node,blackboard):
    left_var = "["+node["_blackboardKey"]+"]"
    right_var = node["_valueToCompare"]
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    if node["_anotherKeyToCompare"] != None and node["_anotherKeyToCompare"] != "": # 比对另一个黑板值
        right_var = "["+node["_anotherKeyToCompare"]+"]"
        if node["_anotherBuff"] and node["_buffKey"] != None: # 比对另一个Buff的黑板值
            if node["_targetType"] != "BUFF_OWNER":
                target_name = anne_dictionary("target",node["_target"])
                return {
                    "main" : f"比对黑板上的{left_var}与{target_name}的另一buff <{node['_buffKey']}> 的{right_var}",
                    "true" : f"{left_var} {compare} {right_var}",
                    "false" : f"{left_var} {compare_not} {right_var}"
                }
            else:
                return {
                    "main" : f"比对黑板上的{left_var}与另一buff <{node['_buffKey']}> 的{right_var}",
                    "true" : f"{left_var} {compare} {right_var}",
                    "false" : f"{left_var} {compare_not} {right_var}"
                }
        else:
            return {
                "main" : f"比对黑板上的{left_var}与{right_var}",
                "true" : f"{left_var} {compare} {right_var}",
                "false" : f"{left_var} {compare_not} {right_var}"
            }
    else:
        return {
            "main" : f"检查黑板上的{left_var}",
            "true" : f"{left_var} {compare} {right_var}",
            "false" : f"{left_var} {compare_not} {right_var}"
        }

# 检查黑板是否等于某个浮点值（带浮点数差值处理）
def IsBlackboardEqualWithFloat(node,blackboard):
    left_var = node["_var"]
    right_var = node["_compareValue"]
    if right_var == 0.0:
        return {
            "main" : f"检查黑板上的 [{left_var}]",
            "true" : f" [{left_var}] ≈ 0",
            "false" : f" [{left_var}] ≈ 0"
        }
    else:
        return {
            "main" : f"检查黑板上的 [{left_var}]",
            "true" : f" [{left_var}] ≈ {right_var}",
            "false" : f" [{left_var}] ≈ {right_var}"
        }
    
# 检查全局黑板
def FilterByGlobalBlackboard(node,blackboard):
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    left_var = "["+node["_blackboardKey"]+"]"
    channel = anne_dictionary("global_blackboard_channel",node["_channel"])
    right_var = node["_valueToCompare"]
    return {
        "main" : f"检查全局黑板（{channel}）上 {left_var} 的值",
        "true" : f"全局黑板（{channel}）上的{left_var} {compare} {right_var}",
        "false" : f"全局黑板（{channel}）上的{left_var} {compare_not} {right_var}"
    }

# 检查末影黑板（同UID单位间互通）
def FilterByCharacterSharedBlackboard(node,blackboard):
    target_name = anne_dictionary("target",node["_target"])
    left_var = "["+node["_blackboardKey"]+"]"
    right_var = node["_valueToCompare"]
    if node["_valueToCompareKey"] != None and node["_valueToCompareKey"] != "":
        if node["_valueToCompareKey"] in blackboard:
            right_var = str(blackboard[node["_valueToCompareKey"]])
        else:
            right_var = "本Buff黑板上的 [" + node["_valueToCompareKey"] + "]"
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    return {
        "main" : f"检查{target_name}末影黑板上 {left_var} 的值",
        "description" : "\"末影黑板\"为同一UID的干员实例间互通的数据",
        "style_closed" : True,
        "true" : f"末影黑板上的{left_var} {compare} {right_var}",
        "false" : f"末影黑板上的{left_var} {compare_not} {right_var}"
    }

# 检查末影黑板上是否存在目标的EnemyID（同UID单位间互通）
def CheckHasEnemyIdInCharacterSharedBlackboard(node,blackboard):
    source_name = anne_dictionary("target",node["_source"])
    target_name = anne_dictionary("target",node["_target"])
    return {
        "main" : f"检查{source_name}的末影黑板上是否存在与{target_name}的EnemyID（Key）",
        "style_closed" : True,
        "description" : "\"末影黑板\"为同一UID的干员实例间互通的数据",
        "true" : f"末影黑板上存在该Key（且Value不为0）",
        "false" : f"末影黑板上不存在该Key（或Value为0）"
    }

# 检查黑板是否为0或未定义
def IsBlackboardZero(node,blackboard):
    return {
        "main" : f"检查黑板 [{node['_var']}] 的值",
        "true" : f"不存在或 [{node['_var']}] = 0",
        "false" : f"存在且 [{node['_var']}] ≠ 0"
    }