#----------------------------------------
# 状态机相关Node
#----------------------------------------
from dictionary import anne_dictionary

# 检查角色类单位是否为阻挡状态机
def CheckCharacterInBornState(node,blackboard):
    owner_name = anne_dictionary("target",node["_ownerType"])
    return {
        "main" : f"检查{owner_name}（角色类）的状态机",
        "true" : "处于部署（Born）状态机",
        "false" : "不处于部署（Born）状态机或不为角色类"
    }

# 检查敌人类单位是否为阻挡状态机
def CheckEnemyInBornState(node,blackboard):
    owner_name = anne_dictionary("target",node["_ownerType"])
    return {
        "main" : f"检查{owner_name}（敌人类）的状态机",
        "true" : "处于出场（Born）状态机",
        "false" : "不处于出场（Born）状态机或不为敌人类"
    }

# 检查是否为阻挡状态机
def CheckUnitInCombatState(node,blackboard):
    owner_name = anne_dictionary("target",node["_ownerType"])
    return {
        "main" : f"检查{owner_name}的状态机",
        "true" : "处于阻挡（Combat）状态机",
        "false" : "不处于阻挡（Combat）状态机"
    }

# 检查是否为攻击状态机
def CheckUnitInAttackState(node,blackboard):
    owner_name = anne_dictionary("target",node["_ownerType"])
    return {
        "main" : f"检查{owner_name}的状态机",
        "true" : "处于攻击（Attack）状态机",
        "false" : "不处于攻击（Attack）状态机"
    }

# 检查是否为重生状态机
def CheckUnitInRebornState(node,blackboard):
    owner_name = anne_dictionary("target",node["_ownerType"])
    return {
        "main" : f"检查{owner_name}的状态机",
        "true" : "处于重生（Reborn）状态机",
        "false" : "不处于重生（Reborn）状态机"
    }

# 检查是否为消失状态机
def CheckUnitInDisappearState(node,blackboard):
    owner_name = anne_dictionary("target",node["_ownerType"])
    return {
        "main" : f"检查{owner_name}的状态机",
        "true" : "处于消失（Disappear）状态机",
        "false" : "不处于消失（Disappear）状态机"
    }

# 检查是否为移动状态机
def CheckUnitInMoveState(node,blackboard):
    owner_name = anne_dictionary("target",node["_ownerType"])
    return {
        "main" : f"检查{owner_name}的状态机",
        "true" : "处于移动（Move）状态机",
        "false" : "不处于移动（Move）状态机"
    }