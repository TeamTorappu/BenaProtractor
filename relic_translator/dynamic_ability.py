#----------------------------------------
# 额外能力相关效果
#----------------------------------------
from .analyzer import analyze_selector, analyze_timing

# 给予目标额外的能力
def rogue_char_ability_new(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    ability_name = blackboard["key"]
    selector = analyze_selector(blackboard)
    result = {
        "main" : f"{timing}为所有{selector}添加一个额外能力：{ability_name}",
        "children" : []
    }
    for key,bb in blackboard.items():
        if not key.startswith("selector.") and key != "key" and key != "trig_type":
            result["children"].append({"main": str(key) + " : "+str(bb)})
    return result

# 给予目标额外的能力（于根部生效）
# 暂时不清楚有什么区别
def rogue_char_ability_new_at_root(item_type,blackboard):
    result = rogue_char_ability_new(item_type,blackboard)
    return result