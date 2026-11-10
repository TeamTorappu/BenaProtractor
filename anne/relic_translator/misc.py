#----------------------------------------
# 杂项效果
#----------------------------------------
from bena import ask_bena_character, ask_bena_enemy

# 让关卡加载特定敌人数据（炎佑.jpg）
def level_add_enemy_data(item_type,blackboard):
    enemy_name = ask_bena_enemy(blackboard["enemy_key"])
    level = int(blackboard.get("level",0))
    return {
        "main" : f"战斗加载期间，为关卡加载级别{level}的 {enemy_name}({blackboard['enemy_key']}) 的数据"
    }

# 提供支援装置
def misc_insert_token_card(item_type,blackboard):
    token_name = ask_bena_character(blackboard["token_key"])
    if token_name != blackboard["token_key"]:
        token_name += "（" + blackboard["token_key"] + "）"
    features = []
    result = {
        "main" : f"战斗开始时，提供 {token_name} × {int(blackboard['cnt'])}" \
    }
    if "level" in blackboard:
        features.append(f"{int(blackboard['level'])}级")
    if "skill" in blackboard and blackboard["skill"] != -1:
        features.append(f"携带{'一二三四五六七'[int(blackboard['skill'])]}技能")
    if len(features) > 0:
        result["description"] = "；".join(features)
    return result

# 展示消息
def push_message(item_type,blackboard):
    return {
        "main" : "展示消息",
        "description" : f"文本路径：{blackboard['path']}"
    }