#----------------------------------------
# CardBuff类Node
#----------------------------------------
from .analyzer import anne_dictionary, analyze_buff

# 创建CardBuff
def node_CreateCardBuff(node):
    #未解析参数：_isRatio
    target_name = anne_dictionary("target",node["_target"])
    descriptions = []
    cardbuff_type = "永久Cardbuff" 
    if node["_lifeType"] == "UNTIL_NEXT_SPAWN" :
        cardbuff_type = "单次Cardbuff"
        descriptions.append("部署完成时消耗，该次部署期间效果全程生效")
    if node["_enableMaxStackCount"]:
        descriptions.append("叠加存在上限")
    else:
        descriptions.append("可无限叠加")
    if node["_filterIsInHand"]:
        descriptions.append("目标必须在\"手卡中\"（位于待部署区且未隐藏）")
    
    if node["_useCardBuffKey"] and node["_cardBuffKey"] != None:
        return {
            "main" : f"尝试为{target_name}(以UID为准)创建{cardbuff_type}: {node['_cardBuffKey']}"
        }
    else:
        return {
            "main" : f"尝试为待部署区的{target_name}(以UID为准)创建{cardbuff_type}（无名）"
        }

# 结束CardBuff
def node_FinishCardBuff(node):
    return {
        "main" : f"结束本Buff相关的CardBuff"
    }