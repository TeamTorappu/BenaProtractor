#----------------------------------------
# 特殊藏品的专属藏品效果Global Buff
#----------------------------------------
from .analyzer import anne_dictionary, analyze_selector

# 湖中神盾
def gb_rogue_3_increaseMaxHPWhenHavingShield(item_type,blackboard):
    power = to_delta_percent(blackboard["mass_level"])
    return {"main" : f"环境效果：开始战斗时若有护盾，所有我方单位{power}(直乘)"}

# 城墙之子
def gb_rogue_4_finalDefense_end_tile(item_type,blackboard):
    hp_power = to_delta_percent(blackboard["max_hp"])
    block_power = to_delta(blackboard["block_cnt"])
    target = analyze_selector(blackboard,"我方")
    return {
        "main" : f"环境效果：给予位于保护目标点及其周围八格的{target}增益Buff：",
        "children" : [
            {"main" : f"最大生命值{hp_power}(直乘)、阻挡数{block_power}(直加)、"}
        ]
    }