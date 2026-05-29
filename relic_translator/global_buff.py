#----------------------------------------
# 全局Buff相关效果
#----------------------------------------
from bena import translate_buff_name

from .analyzer import analyze_selector, analyze_timing

# 常规的全局Buff
def rogue_global_buff_normal(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    global_buff_key = blackboard["key"]
    buff_name = translate_buff_name(blackboard["key"])
    result = {
        "main" : f"{timing}生效全局Buff：{buff_name}",
        "link" : "global_buff."+global_buff_key,
        "children" : []
    }
    has_selector = False
    for key,bb in blackboard.items():
        if key.startswith("selector."):
            has_selector = True
        elif key != "key" and key != "trig_type":
            result["children"].append({"main": str(key) + " : "+str(bb)})
    if has_selector:
        result["description"] = "仅对" + analyze_selector(blackboard) + "生效"
    return result

# 黑板值累加的全局Buff（累加时会-1）
def rogue_global_buff_stack_base_one(item_type,blackboard):
    result = rogue_global_buff_normal(item_type,blackboard)
    result["main"] += "（若已有同名效果，改为累加(下列数值-1) ）"
    return result

# 黑板值累加的全局Buff
def rogue_global_buff_stack(item_type,blackboard):
    result = rogue_global_buff_normal(item_type,blackboard)
    result["main"] += "（若已有同名效果，改为累加下列数值）"
    return result