#----------------------------------------
# 局外效果
#----------------------------------------
import math

from bena import ask_bena, ask_bena_character
from dictionary import anne_dictionary
from analyzer import analyze_rogue_item_reward, analyze_profession, analyze_sub_profession, to_delta, analyze_relic_timing, analyze_rogue_item, to_delta_percent

# 立即奖励
def immediate_reward(item_type,blackboard):
    if blackboard["id"] == "rogue_6_hp" and blackboard["count"] == 0: # 神秘0个目标生命值
        return {"main" : "占位效果"}
    timing = analyze_relic_timing(item_type,blackboard)
    reward = analyze_rogue_item_reward(blackboard)
    reward["main"] = timing + reward["main"]
    return reward

# 立刻消耗
def immediate_cost(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    item = analyze_rogue_item(blackboard)
    if item != None and item.type == "COPPER": # 界园钱的特殊处理
        return {"main" : f"{timing}让钱盒内的 <rogue_item|{item.display_name}> 变为大炎通宝。"}
    return {"main" : f"{timing}消耗玩家 {blackboard['id']} × {math.floor(blackboard.get('count',0))}"}

# 开局额外招募券奖励
def initial_recruit_reward(item_type,blackboard):
    reward = analyze_rogue_item_reward(blackboard)
    reward["main"] = "初始招募时，额外" + reward["main"]
    return reward

# 下次开局奖励
def init_gift(item_type,blackboard):
    reward = analyze_rogue_item_reward(blackboard)
    reward["main"] = "下次开始探索时，额外" + reward["main"]
    return reward

# 物品数量覆盖
def item_cover_set(item_type,blackboard):
    item = analyze_rogue_item(blackboard)
    if item != None:
        return {
            "main" : f"让玩家的{item.display_type} {item.display_name} 数量增加/减少至 {math.floor(blackboard.get('count',1))}",
            "link" : blackboard['id']
        }
    return {"main" : f"将玩家的 {blackboard['id']} 数量增加/减少至{math.floor(blackboard.get('count',1))}"}

# 进入岁兽残识发放奖励（仅一次）
def secret_into_reward_once(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    reward = analyze_rogue_item_reward(blackboard)
    reward["main"] = timing + "首次进入岁兽残识时" + reward["main"]
    return reward

# 进入岁兽残识发放奖励
def secret_into_reward(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    reward = analyze_rogue_item_reward(blackboard)
    reward["main"] = timing + "每次进入岁兽残识时" + reward["main"]
    return reward

# 钱的自变化
def copper_exchange(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    if "id" in blackboard:
        if blackboard["id"] == "pool_reroll_copper":
            return {"main" : f"{timing}尝试将钱盒内的该钱替换为随机的钱"}
        elif blackboard["id"] == "pool_reroll_copper_high":
            return {"main" : f"{timing}尝试将钱盒内的该钱替换为随机的花钱"}
        elif blackboard["id"] == "pool_reroll_copper_low":
            return {"main" : f"{timing}尝试将钱盒内的该钱替换为随机的厉钱"}
        else:
            return {
                "main": f"{timing}尝试将钱盒内的该钱替换为 <rogue_item|{blackboard['id']}> 。"
            }
    return {"main" : f"{timing}尝试将钱盒内的该钱替换为空气。"}
    
# 战斗后额外掉落随机招募券
def battle_extra_recruit_ticket(item_type,blackboard):
    return {"main": f"每次战斗结束时，在掉落物中增加{math.floor(blackboard['count'])}个随机招募券。"}

# 战斗中获得临时生命值
def level_life_point_add(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    return {"main" : f"{timing}战斗开始时获得{int(blackboard['value'])}点本局专用的生命值（会影响国王套判断）"}

# 特定情况下的奖励增加
def up_reward(item_type,blackboard):
    timing = "未知时点，"
    if blackboard["mask"] == "battle":
        timing = "战斗胜利时，"
    item = analyze_rogue_item(blackboard)
    percent = to_delta_percent(blackboard["up"])
    return {"main" : f"{timing}使获得的 {item.display_name} 数量{percent}"}

# 玩家升级时的额外奖励
def player_level_rewards(item_type,blackboard):
    level = int(blackboard["level"])
    reward = analyze_rogue_item_reward(blackboard)
    reward["main"] = f"玩家指挥等级达到{level}时，立刻" + reward["main"]
    return reward

# 战斗结束时的额外奖励
def battle_extra_reward(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    reward = analyze_rogue_item_reward(blackboard)
    reward["main"] = f"{timing}战斗结束将额外" + reward["main"]
    return reward

# 击破宝箱获得额外源石锭
def extra_gold_from_chest(item_type,blackboard):
    trap_name = ask_bena_character(blackboard["id"])
    return {"main" : f"战斗中每击破一个 {trap_name}，结束后就将给予 源石锭 × {math.floor(blackboard.get('count',0))}"}

# 特定职业招募希望减少
def recruit_cost(item_type,blackboard):
    rarity = anne_dictionary("rarity",blackboard["rarity"])
    professions = analyze_profession(blackboard["profession"])
    delta = ("+" + int(blackboard["delta"])) if blackboard["delta"] > 0 else (str(int(blackboard["delta"])))
    return {"main" : f"招募{rarity}的{professions}的希望{delta}"}

# 特定职业进阶希望减少
def upgrade_cost(item_type,blackboard):
    rarity = anne_dictionary("rarity",blackboard["rarity"])
    professions = analyze_profession(blackboard["profession"])
    delta = ("+" + int(blackboard["delta"])) if blackboard["delta"] > 0 else (str(int(blackboard["delta"])))
    return {"main" : f"进阶{rarity}的{professions}的希望{delta}"}

# 特定子职业招募希望减少
def recruit_cost_sub_profession(item_type,blackboard):
    rarity = anne_dictionary("rarity",blackboard["rarity"])
    sub_professions = analyze_sub_profession(blackboard["sub_profession"])
    delta = ("+" + int(blackboard["delta"])) if blackboard["delta"] > 0 else (str(int(blackboard["delta"])))
    return {"main" : f"招募{rarity}的{sub_professions}的希望{delta}"}

# 特定子职业进阶希望减少
def upgrade_cost_sub_profession(item_type,blackboard):
    rarity = anne_dictionary("rarity",blackboard["rarity"])
    sub_professions = analyze_sub_profession(blackboard["sub_profession"])
    delta = ("+" + int(blackboard["delta"])) if blackboard["delta"] > 0 else (str(int(blackboard["delta"])))
    return {"main" : f"进阶{rarity}的{sub_professions}的希望{delta}"}

# 立刻招募
def immediate_recruit(item_type,blackboard):
    result = {
        "main" : "立刻以临时招募的形式招募以下干员：",
        "children" : []
    }
    for character in blackboard["char_list"].split(","):
        character_name = ask_bena_character(character)
        if character_name != character:
            character_name += "（" + character + "）"
            result["children"].append({"main" : character_name})
    return result