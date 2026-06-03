#----------------------------------------
# 局外效果
#----------------------------------------
import math

from bena import ask_bena, ask_bena_character
from translator import anne_dictionary
from .analyzer import analyze_item_reward, to_delta, analyze_timing, analyze_item, to_delta_percent

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
    reward = analyze_item_reward(blackboard)
    reward["main"] = timing + reward["main"]
    return reward

# 立刻消耗
def rogue_immediate_cost(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    item = analyze_item(blackboard)
    if item != None:
        if item.type == "COPPER": # 界园钱的特殊处理
            return {
                "main": f"{timing}让钱盒内的 {item.display_name} 变为大炎通宝。",
                "link": blackboard['id']
            }
        return {
            "main": f"{timing}消耗玩家{item.display_type} {item.display_name} × {math.floor(blackboard.get('count',0))}",
            "link": blackboard['id']
        }
    return {"main": f"{timing}消耗玩家 {blackboard['id']} × {math.floor(blackboard.get('count',0))}"}

# 开局额外招募券奖励
def rogue_initial_recruit_reward(item_type,blackboard):
    reward = analyze_item_reward(blackboard)
    reward["main"] = "初始招募时，额外" + reward["main"]
    return reward

# 进入特定层数发放奖励
def rogue_zone_into_reward(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    reward = analyze_item_reward(blackboard)
    zone = blackboard["zone"]
    zone_name = "???层"
    if zone == "zone_2":
        zone_name = "第二层"
    elif zone == "zone_3":
        zone_name = "第三层"
    elif zone == "zone_4":
        zone_name = "第四层"
    elif zone == "zone_5":
        zone_name = "第五层"
    elif zone == "zone_6":
        zone_name = "第六层"
    elif zone == "zone_7":
        zone_name = "第七层"
    reward["main"] = timing + f"进入{zone_name}时" + reward["main"]
    return reward

# 进入岁兽残识发放奖励（仅一次）
def rogue_secret_into_reward_once(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    reward = analyze_item_reward(blackboard)
    reward["main"] = timing + "首次进入岁兽残识时" + reward["main"]
    return reward

# 进入岁兽残识发放奖励
def rogue_secret_into_reward(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    reward = analyze_item_reward(blackboard)
    reward["main"] = timing + "每次进入岁兽残识时" + reward["main"]
    return reward

# 钱的自变化
def rogue_copper_exchange(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    if "id" in blackboard:
        if blackboard["id"] == "pool_reroll_copper":
            return {"main" : f"{timing}尝试将钱盒内的该钱替换为随机的钱"}
        elif blackboard["id"] == "pool_reroll_copper_high":
            return {"main" : f"{timing}尝试将钱盒内的该钱替换为随机的花钱"}
        elif blackboard["id"] == "pool_reroll_copper_low":
            return {"main" : f"{timing}尝试将钱盒内的该钱替换为随机的厉钱"}
        else:
            item = ask_bena("rogue_item",blackboard["id"])
            if item != None:
                # 变成指定通宝
                if item.type != "COPPER": # 界园钱的特殊处理
                    return {"main" : f"{timing}尝试将钱盒内的该钱替换为 {item.display_name}（非通宝，无法正常运作）"}
                return {
                    "main": f"{timing}尝试将钱盒内的该钱替换为 {item.display_name} 。",
                    "link": blackboard['id']
                }
    return {"main" : f"{timing}尝试将钱盒内的该钱替换为空气。"}
    
# 战斗后额外掉落随机招募券
def rogue_battle_extra_recruit_ticket(item_type,blackboard):
    return {"main": f"每次战斗结束时，在掉落物中增加{math.floor(blackboard['count'])}个随机招募券。"}

# 战斗中获得临时生命值
def rogue_level_life_point_add(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    return {"main" : f"{timing}战斗开始时获得{int(blackboard['value'])}点本局专用的生命值（会影响国王套判断）"}

# 特定情况下的奖励增加
def rogue_up_reward(item_type,blackboard):
    timing = "未知时点，"
    if blackboard["mask"] == "battle":
        timing = "战斗胜利时，"
    item = analyze_item(blackboard)
    percent = to_delta_percent(blackboard["up"])
    return {"main" : f"{timing}使获得的 {item.display_name} 数量{percent}"}

# 玩家升级时的额外奖励
def rogue_player_level_rewards(item_type,blackboard):
    level = int(blackboard["level"])
    reward = analyze_item_reward(blackboard)
    reward["main"] = f"玩家指挥等级达到{level}时，立刻" + reward["main"]
    return reward

# 战斗结束时的额外奖励
def rogue_battle_extra_reward(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    reward = analyze_item_reward(blackboard)
    reward["main"] = f"{timing}战斗结束将额外" + reward["main"]
    return reward

# 击破宝箱获得额外源石锭
def rogue_extra_gold_from_chest(item_type,blackboard):
    trap_name = ask_bena_character(blackboard["id"])
    return {"main" : f"战斗中每击破一个 {trap_name}，结束后就将给予 源石锭 × {math.floor(blackboard.get('count',0))}"}