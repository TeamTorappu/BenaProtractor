#----------------------------------------
# 局外效果
#----------------------------------------
from .analyzer import anne_dictionary, to_delta, analyze_timing, analyze_item

# 关卡内的可部署人数上限增减
def rogue_level_char_limit_add(item_type,blackboard):
    value = blackboard.get("value",0)
    if value < 0:
        return {"main": f"战斗中的可部署人数上限{to_delta(value)}（不会低于1）"}
    else:
        return {"main": f"战斗中的可部署人数上限{to_delta(value)}"}

# 立即奖励
def rogue_immediate_reward(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    translation = analyze_item(blackboard)
    translation["main"] = timing+"，"+translation["main"]
    return translation

# 进入特殊节点奖励一次？
def rogue_secret_into_reward_once(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    translation = analyze_item(blackboard)
    translation["main"] = timing+"，"+translation["main"]
    return translation

# 钱的自变化
def rogue_copper_exchange(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    if "id" in blackboard:
        if blackboard["id"] == "pool_reroll_copper":
            return {"main" : f"{timing}，尝试将钱盒内的该钱替换为随机的钱"}
        elif blackboard["id"] == "pool_reroll_copper_high":
            return {"main" : f"{timing}，尝试将钱盒内的该钱替换为随机的花钱"}
        elif blackboard["id"] == "pool_reroll_copper_low":
            return {"main" : f"{timing}，尝试将钱盒内的该钱替换为随机的厉钱"}
        else:
            item = ask_bena("rogue_item",blackboard["id"])
            if item != None:
                # 变成指定通宝
                if item.type != "COPPER": # 界园钱的特殊处理
                    return {"main" : f"{timing}，尝试将钱盒内的该钱替换为 {item.display_name}（非通宝，无法正常运作）"}
                return {
                    "main": f"{timing}，尝试将钱盒内的该钱替换为 {item.display_name} 。",
                    "link": blackboard['id']
                }
    return {"main" : f"{timing}，尝试将钱盒内的该钱替换为空气。"}
    
# 战斗后额外掉落随机招募券
def rogue_battle_extra_recruit_ticket(item_type,blackboard):
    return {"main": f"每次战斗结束时，在掉落物中增加{math.floor(blackboard['count'])}个随机招募券。"}

# 战斗中获得临时生命值
def rogue_level_life_point_add(item_type,blackboard):
    if "trig_type" in blackboard:
        timing = analyze_timing(item_type,blackboard)
        return {"main" : f"{timing}，战斗开始时获得{blackboard['value']}点本局专用的生命值（会影响国王套判断）"}
    return {"main" : f"战斗开始时获得{blackboard['value']}点本局专用的生命值（会影响国王套判断）"}