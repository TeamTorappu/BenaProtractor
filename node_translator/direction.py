#----------------------------------------
# 朝向相关Node
#----------------------------------------
from translator import anne_dictionary

DIRECTION_TIP = "敌人类单位未移动的情况下，其移动朝向为上"

# 将部署方向记录到黑板上
def node_AssignDirectionToBB(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node['_isReverse']:
        return {
            "main" : f"将{target_name}朝向的相反方向记录至黑板 [{node['_blackboardKey']}]",
            "description" : "即 上=2 右=3 下=0 左=1；若为\"无朝向\"，记录4"
        }
    return {
        "main" : f"将{target_name}朝向的方向记录至黑板 [{node['_blackboardKey']}]",
        "description" : "即 上=0 右=1 下=2 左=3；若为\"无朝向\"，记录4"
    }

# 检查移动朝向/部署朝向
def node_CheckFaceDirection(node):
    target_name = anne_dictionary("target",node["_target"])
    direction = anne_dictionary("direction",node["_direction"])
    direction_not = anne_dictionary("direction_not",node["_direction"])
    return {
        "main" : f"检查{target_name}的移动朝向（敌人类）/部署朝向（角色类）",
        "description" : DIRECTION_TIP,
        "true" : f"若其朝向为{direction}",
        "false" : f"若其朝向为{direction_not}"
    }

# 检查单位是否朝左/朝右，但是实际上和上面那个效果一样
def node_CheckFaceLOrR(node):
    target_name = anne_dictionary("target",node["_target"])
    if node["_direction"] == "LEFT":
        return {
            "main" : f"检查{target_name}的移动朝向（敌人类）/部署朝向（角色类）",
            "description" : DIRECTION_TIP,
            "true" : f"若其朝向左边",
            "false" : f"若其不朝向左边"
        }
    elif node["_direction"] != "RIGHT":
        return {
            "main" : f"检查{target_name}的移动朝向（敌人类）/部署朝向（角色类）",
            "description" : DIRECTION_TIP,
            "true" : f"若其朝向右边",
            "false" : f"若其不朝向右边"
        }
    return node_CheckFaceDirection(node)

# 检查角色类单位的“默认部署朝向”——可你不检查角色类，这不就是检查朝向？
def node_CheckCharacterDefaultDirection(node):
    target_name = anne_dictionary("target",node["_target"])
    if node["_useBB"] and node["_bbKey"] != None and node["_bbKey"] != "": #唯一的区别
        return {
            "main" : f"检查{target_name}的移动朝向（敌人类）/部署朝向（角色类）",
            "description" : DIRECTION_TIP,
            "true" : f"若其朝向与黑板上记述的 [{node['_bbKey']}] 相同",
            "false" : f"若其朝向与黑板上记述的 [{node['_bbKey']}] 不同"
        }
    return node_CheckFaceDirection(node)

# 检查两者之间的朝向
def node_CheckDirection(node):
    source_name = anne_dictionary("target",node["_source"])
    target_name = anne_dictionary("target",node["_target"])
    if node["_judgeType"] == "FACE_TARGET":
        return {
            "main" : f"检查{source_name}的部署移动朝向（敌人类）/部署朝向（角色类）是否面向{target_name}",
            "description" : DIRECTION_TIP,
            "true" : f"若{source_name}的朝向面向{target_name}",
            "false" : f"若{source_name}的朝向不面向{target_name}"
        }
    judge = anne_dictionary("direction_judge",node["_judgeType"])
    judge_not = anne_dictionary("direction_judge_not",node["_judgeType"])
    return {
        "main" : f"检查{source_name}与{target_name}两者的移动朝向（敌人类）/部署朝向（角色类）",
        "description" : DIRECTION_TIP,
        "true" : f"若{source_name}与{target_name}的朝向{judge}",
        "false" : f"若{source_name}与{target_name}的朝向并不{judge}"
    }