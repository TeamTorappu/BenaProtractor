#----------------------------------------
# 敌方的Global Buff
#----------------------------------------
from translator import anne_dictionary
from .analyzer import to_delta, to_delta_percent, to_percent

# 敌方最大生命值最终下降
def gb_enemy_max_hp_down(item_type,blackboard):
    power = to_delta_percent(blackboard["max_hp"])
    return {"main" : f"环境效果：敌方最大生命值×{power}(终乘)"}   

# 敌方防御力最终下降
def gb_enemy_def_down(item_type,blackboard):
    power = to_percent(blackboard["def"],True)
    return {"main" : f"环境效果：敌方防御力×{power}(终乘)"}

# 敌方攻击力最终下降
def gb_enemy_atk_down(item_type,blackboard):
    power = to_percent(blackboard["atk"],True)
    return {"main" : f"环境效果：敌方攻击力×{power}(终乘)"}

# 敌方变轻
def gb_enemy_lighter(item_type,blackboard):
    power = to_delta(blackboard["mass_level"])
    return {"main" : f"环境效果：敌方重量等级{power}(直加)"}