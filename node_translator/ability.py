#----------------------------------------
# 能力类Node
#----------------------------------------
from .analyzer import anne_dictionary

# 检查能力用途
def node_FilterAbilityFamily(node):
    family = anne_dictionary("ability_family",node["_familyGroupMask"])
    return {
        "main" : "检查此能力的类别（或称用途）",
        #"description" : "分为：常规攻击、阻挡攻击、技能、天赋、无特定类别；\"特性\"也是一种天赋或无特定类型能力",
        "true" : "若其隶属于"+family,
        "false" : "若其不隶属于"+family,
    }
