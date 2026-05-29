#----------------------------------------
# 叠层相关效果
#----------------------------------------
from .analyzer import analyze_timing, to_percent

# 战斗结束时为藏品叠层
def rogue_layer_after_battle_data(item_type,blackboard):
    # 未解析黑板：src
    timing = "战斗结束时，"
    if blackboard.get("is_success",0) != 0:
        timing = "战斗胜利时，"
    prob = to_percent(blackboard.get("prob",1))
    return {"main" : f"{timing}有{prob}概率令本藏品叠加{blackboard['scale']}层（上限{blackboard['max']}层)"}