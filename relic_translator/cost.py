#----------------------------------------
# 费用相关效果
#----------------------------------------
import math

from .analyzer import analyze_timing, to_percent
# 常规的全局Buff
def rogue_level_cost_increase_time_mul(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    percent = to_percent(blackboard["scale"])
    anti_percent = to_percent(1. / blackboard["scale"])
    return {
        "main" : f"{timing}关卡的部署费用自然回复间隔{'提升至' if blackboard['scale'] >= 1.0 else '降低至'}{percent}",
        "description" : f"即基础部署费用回复速度{'降低至' if blackboard['scale'] >= 1.0 else '提升至'}{anti_percent}"
    }