#----------------------------------------
# 隐藏组相关效果
#----------------------------------------
from .analyzer import analyze_timing

# 激活战斗的隐藏组（即额外出怪）
def rogue_level_hidden_group_enable(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    key = blackboard["key"] if "key" in blackboard else "???"
    return {"main" : f"{timing}战斗中将出现额外敌人（启用隐藏组：{key}）"}