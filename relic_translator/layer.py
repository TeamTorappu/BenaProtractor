#----------------------------------------
# 叠层相关效果
#----------------------------------------
from translator import anne_dictionary

from .analyzer import analyze_timing, to_percent

# 战斗结束时为藏品叠层
def rogue_layer_after_battle_data(item_type,blackboard):
    # 未解析黑板：src
    timing = "战斗结束时，"
    if blackboard.get("is_success",0) != 0:
        timing = "战斗胜利时，"
    prob = ""
    if "prob" in blackboard: # 生效概率
        prob = f"有{to_percent(blackboard['prob'])}概率"
    scale = blackboard.get("scale",1)
    features = []
    if "init" in blackboard: # 初始层数
        features.append(f"初始{int(blackboard['init'])}层")
    if "max" in blackboard: # 最大层数
        features.append(f"最大{int(blackboard['max'])}层")
        
    if len(features) > 0:
        return {"main" : f"{timing}{prob}令本藏品叠加{scale}层（{'，'.join(features)})"}
    return {"main" : f"{timing}{prob}令本藏品叠加{scale}层"}

# 通过特定关卡后叠层
def rogue_layer_pass_stage(item_type,blackboard):
    result = rogue_layer_after_battle_data(item_type,blackboard)
    result["main"] = result["main"].replace("战斗结束","完成特定关卡") + "；包括关卡："
    result["children"] = []
    for stage in blackboard["stage_ids"].split(","):
        stage_name = anne_dictionary("rogue_stage",stage)
        if stage_name != stage:
            stage_name += "（" + stage + "）"
        result["children"].append({"main" : stage_name})
    return result

