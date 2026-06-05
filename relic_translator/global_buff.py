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
        "global_buff" : global_buff_key,
        "children" : []
    }
    # 预处理黑板数据与选择器
    has_selector = False
    extra_target_options = {}
    true_blackboard = {}
    for key,bb in blackboard.items():
        if key.startswith("selector."):
            has_selector = True
        elif key != "key" and key != "trig_type":
            true_blackboard[str(key)] = bb
    # 添加选择器结果
    if has_selector:
        result["description"] = "仅对" + analyze_selector(blackboard) + "生效"
    # 添加黑板结果
    if len(true_blackboard) > 0:
        blackboard_result = {"main" : "黑板值（数据）：","children" : []}
        for key,bb in true_blackboard.items():
            blackboard_result["children"].append({"main": f"[{key}] = {bb}"})
        result["children"].append(blackboard_result)
    return result

# 叠层加倍增幅量/减少量的全局Buff（累加时会-1）
def rogue_global_buff_stack_base_one(item_type,blackboard):
    result = rogue_global_buff_normal(item_type,blackboard)
    result["main"] += "（数值增幅量/减少量均乘以当前层数；同名效果间数值取增幅量/减少量累加）"
    return result

# 叠层的全局Buff
def rogue_global_buff_stack(item_type,blackboard):
    result = rogue_global_buff_normal(item_type,blackboard)
    result["main"] += "（数值均乘以当前层数）"
    return result