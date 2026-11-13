#----------------------------------------
# 检查类Node
#----------------------------------------
from bena import ask_bena_character, ask_bena_enemy

from dictionary import anne_dictionary
from analyzer import analyze_fp, analyze_target_options

# 检查异常效果（带免疫）
def CheckIfDamageHasSharedFlags(node,blackboard):
    sharedflag = node["_sharedFlags"]
    #sharedflag_name = anne_dictionary("sharedflag",node["_sharedFlags"])
    if node["_isUnset"]:
        return {
            "main" : f"检查本次伤害是否带有{sharedflag}标签",
            "true" : f"不带有{sharedflag}标签",
            "false" : f"带有{sharedflag}标签"
        }
    else:
        return {
            "main" : f"检查本次伤害是否带有{sharedflag}标签",
            "true" : f"带有{sharedflag}标签",
            "false" : f"不带有{sharedflag}标签"
        }

# 检查伤害取消原因
def FilterDamageCancellation(node,blackboard):
    reasons = "、".join([anne_dictionary("cancel_reason",reason)+"("+reason+")" for reason in node["_allowedCancelReasons"]])
    if node["_acceptUncancelled"]:
        return {
            "main" : f"检查本次伤害是否已取消，并检查取消的原因",
            "true" : f"未取消，或因{reasons}取消",
            "false" : f"因{reasons}以外的原因取消"
        }
    else:
        return {
            "main" : f"检查本次伤害被取消的原因",
            "true" : f"因{reasons}取消",
            "false" : f"因{reasons}以外的原因取消，或未取消"
        }