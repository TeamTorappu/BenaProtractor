#----------------------------------------
# 关卡符文
#----------------------------------------
from analyzer import to_delta,to_percent

# 启用战斗的隐藏组（即额外出怪）
def level_hidden_group_enable(blackboard,selector=None):
    key = blackboard["key"] if "key" in blackboard else "???"
    return {"main" : f"战斗中将出现额外敌人（启用隐藏组：{key}）"}

# 禁用战斗的隐藏组（即无法再额外出怪）
def level_hidden_group_disable(blackboard,selector=None):
    key = blackboard["key"] if "key" in blackboard else "???"
    return {"main" : f"战斗中部分敌人将无法再出现（禁用隐藏组：{key}）"}

# 关卡可部署人数增减
def global_placable_char_num_add(blackboard,selector=None):
    value = int(blackboard["value"]) if "value" in blackboard else 0
    power = to_delta(value)
    return {"main" : f"战斗中\"可部署人数\"{power}"}

# 关卡回费间隔修改
def global_cost_recovery_mul(blackboard,selector=None):
    value = int(blackboard["value"]) if "value" in blackboard else 0
    power = to_percent(value)
    return {"main" : f"战斗中\"费用回复间隔\"×{power}"}