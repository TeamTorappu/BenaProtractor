#----------------------------------------
# 全局Buff相关效果
#----------------------------------------
from bena import translate_buff_name

from analyzer import analyze_selector, analyze_relic_timing

# 常规的全局Buff
def global_buff_normal(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    global_buff_key = blackboard["key"]
    result = {
        "main" : f"{timing}战斗中将生效全局Buff：<global_buff|{global_buff_key}>",
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
    #if has_selector:
    #    result["description"] = "仅对" + analyze_selector(blackboard) + "生效"
    # 添加黑板结果
    if len(true_blackboard) > 0:
        blackboard_result = {"main" : "黑板值（数据）：","children" : []}
        for key,bb in true_blackboard.items():
            blackboard_result["children"].append({"main": f"[{key}] = {bb}"})
        result["children"].append(blackboard_result)
    return result

# 叠层加倍的全局Buff
def global_buff_layer(item_type,blackboard):
    result = global_buff_normal(item_type,blackboard)
    result["main"] += "（藏品层数记录在黑板 [stack_layer] 上）"
    return result

# 可叠加增幅量/减少量的全局Buff（累加时会-1）
def global_buff_stack_base_one(item_type,blackboard):
    result = global_buff_normal(item_type,blackboard)
    result["main"] += "（同名效果间黑板值取增幅量/减少量累加）"
    return result

# 可叠加的全局Buff
def global_buff_stack(item_type,blackboard):
    result = global_buff_normal(item_type,blackboard)
    result["main"] += "（同名效果间黑板值累加）"
    return result