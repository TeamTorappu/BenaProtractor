#----------------------------------------
# 全局Buff相关符文
#----------------------------------------
from bena import translate_buff_name

from analyzer import analyze_selector, analyze_relic_timing

# 常规的全局Buff
def env_gbuff_new(selector,blackboard):
    global_buff_key = blackboard["key"]
    result = {
        "main" : f"战斗中将生效全局Buff：<global_buff|{global_buff_key}>",
        "global_buff" : global_buff_key,
        "children" : []
    }
    # 预处理黑板数据与选择器
    true_blackboard = {}
    for key,bb in blackboard.items():
        if key.startswith("selector."):
            has_selector = True
        elif key != "key" and key != "trig_type":
            true_blackboard[str(key)] = bb
    # 添加黑板结果
    if len(true_blackboard) > 0:
        blackboard_result = {"main" : "黑板值（数据）：","children" : []}
        for key,bb in true_blackboard.items():
            blackboard_result["children"].append({"main": f"[{key}] = {bb}"})
        result["children"].append(blackboard_result)
    return result

# 带验证的全局Buff（建议在别处翻译具体逻辑）
def env_gbuff_new_with_verify(selector,blackboard):
    result = env_gbuff_new(selector,blackboard)
    return result