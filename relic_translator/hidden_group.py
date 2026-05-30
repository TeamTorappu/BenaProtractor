#----------------------------------------
# 隐藏组相关效果
#----------------------------------------
from .analyzer import analyze_timing

# 激活战斗的隐藏组（即额外出怪）
def rogue_level_hidden_group_enable(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    key = blackboard["key"] if "key" in blackboard else "???"
    return {"main" : f"{timing}战斗中将出现额外敌人（启用隐藏组：{key}）"}

# 取消战斗的隐藏组（即无法再额外出怪）
def rogue_level_hidden_group_disable(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    key = blackboard["key"] if "key" in blackboard else "???"
    return {"main" : f"{timing}战斗中部分额外敌人将无法再出现（禁用隐藏组：{key}）"}