#----------------------------------------
# 肉鸽特色Node
#----------------------------------------
from translator import anne_dictionary

# 获取源石锭数量
def node_AssignGoldToBlackboard(node):
    return {
        "main" : f"将当前“源石锭数量”记录至 [{node['_blackboardKey']}]",
        "description" : "“源石锭数量”是战斗开始时记录的源石锭道具数量，战斗中源石锭的增减不一定会影响此数值"
    }

# 检查角色是否已秉烛
def node_RoguelikeFilterCharacterInCandleHolder(node):
    target_name = anne_dictionary("target",node["_target"])
    return {
        "main" : f"检查{target_name}（干员）是否已秉烛",
        "description" : "黑流树海中的应急干员实现逻辑同样为“秉烛”",
        "true" : "若该干员已秉烛",
        "false" : "若该干员未秉烛，或单位不是干员/非招募所得"
    }

# 获取零件箱内零件数量
def node_AssignScrapInventoryToBlackboard(node):
    actions = []
    # 持有零件数量
    if node["_countBlackboardKey"] != None and node["_countBlackboardKey"] != "":
        actions.append(f"将持有零件数量记录至 [{node['_countBlackboardKey']}]")
    # 零件箱上限
    if node["_limitBlackboardKey"] != None and node["_limitBlackboardKey"] != "":
        actions.append(f"将零件箱上限记录至 [{node['_limitBlackboardKey']}]")
    if len(actions) == 0:
        return {"main" : "（猎狗Proto把这个Node的效果嚼嚼嚼掉了）"}
    return {
        "main" : "；".join(actions)
    }

# 各种“源石锭被偷走了！”框
def node_RoguelikeShowToastRL04(node):
    if node["_toastTypeRL04"] == "GOLD_STEAL":
        return {"main" : f"展示{node['_lastTime']}秒“源石锭被偷走了！”（萨卡兹肉鸽风格）"}
    elif node["_toastTypeRL04"] == "DISASTER_CONTINUE":
        return {"main" : f"展示{node['_lastTime']}秒“战士应当视死如归”（萨卡兹肉鸽版）"}
    return {"main" : f"展示{node['_lastTime']}秒“???”（萨卡兹肉鸽风格）"}
def node_RoguelikeShowToastRL05(node):
    if node["_toastTypeRL05"] == "GOLD_STEAL":
        return {"main" : f"展示{node['_lastTime']}秒“源石锭被偷走了！”（界园肉鸽风格）"}
    return {"main" : f"展示{node['_lastTime']}秒“???”（界园肉鸽风格）"}
def node_RoguelikeShowToastRL06(node):
    if node["_toastTypeRL06"] == "GOLD_STEAL":
        return {"main" : f"展示{node['_lastTime']}秒“源石锭被偷走了！”（树海肉鸽风格）"}
    elif node["_toastTypeRL06"] == "STEP_STEAL":
        return {"main" : f"展示{node['_lastTime']}秒“你的行动力被偷走了”（树海肉鸽风格）"}
    return {"main" : f"展示{node['_lastTime']}秒“???”（树海肉鸽风格）"}