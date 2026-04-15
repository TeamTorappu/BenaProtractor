#----------------------------------------
# CardBuff类Node
#----------------------------------------
from .analyzer import anne_dictionary, analyze_buff

# 创建CardBuff
def node_CreateCardBuff(node):
    target_name = anne_dictionary("target",node["_target"])
    descriptions = []
    cardbuff_type = "永久Cardbuff" 
    if node["_lifeType"] == "UNTIL_NEXT_SPAWN" :
        cardbuff_type = "单次Cardbuff"
        descriptions.append("下次部署后将消耗")
    if node["_enableMaxStackCount"]:
        descriptions.append("同名效果叠加上限[max_stack]")
    if node["_filterIsInHand"]:
        descriptions.append("目标必须在\"手卡中\"（非已部署/处于墓地等隐藏的单位）")
    
    cardbuff_actions = []
    result = {
        "main" : f"尝试为待部署区的{target_name}(以UID为准)创建{cardbuff_type}",
        "style_closed" : True
    }
    if len(descriptions) > 0:
        result["description"] = "；".join(descriptions)
    if node["_isRatio"]: #这个参数只对再部署有效果
        cardbuff_actions.append("再部署时间+[respawn_time]%")
    else:
        cardbuff_actions.append("再部署时间+[respawn_time]秒")
        cardbuff_actions.append("再部署时间下限[min_respawn_time]秒（若有）")
        cardbuff_actions.append("再部署时间上限[max_respawn_time]秒（若有）")
    # [respawn_time_max_mult]
    cardbuff_actions.append("部署费用+[value]")
    cardbuff_actions.append("部署费用+[cost_scale]%")
    cardbuff_actions.append("若开启[respawn_stopped]，则禁止再部署")
    cardbuff_actions.append("若开启[not_add_respawn_cost_cnt]，则部署不增加部署费用惩罚")
    cardbuff_actions.append("为头像上添加[card_anim]特效（若有）")
    result["children"] = [{"main" : action} for action in cardbuff_actions]
    if node["_useCardBuffKey"] and node["_cardBuffKey"] != None:
        result["main"] += f"（<{node['_cardBuffKey']}>）"
        result["link"] = "cardbuff." + node["_cardBuffKey"]
    return result

# 结束CardBuff
def node_FinishCardBuff(node):
    return {
        "main" : f"结束本Buff相关的CardBuff"
    }