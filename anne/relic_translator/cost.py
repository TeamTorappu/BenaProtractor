#----------------------------------------
# 费用相关效果
#----------------------------------------
import math

from analyzer import analyze_relic_timing, to_percent
# 关卡费用增加间隔乘算
def level_cost_increase_time_mul(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    percent = to_percent(blackboard["scale"])
    anti_percent = to_percent(1. / blackboard["scale"])
    return {
        "main" : f"{timing}关卡的部署费用自然回复间隔{'提升至' if blackboard['scale'] >= 1.0 else '降低至'}{percent}",
        "description" : f"即基础部署费用回复速度{'降低至' if blackboard['scale'] >= 1.0 else '提升至'}{anti_percent}"
    }

#  关卡初始费用增加
def level_init_cost_add(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    if blackboard["value"] < 0:
        return {"main" : f"{timing}关卡的初始部署费用减少{-blackboard['value']}（不会低于0）"}
    else:
        return {"main" : f"{timing}关卡的初始部署费用增加{blackboard['value']}"}