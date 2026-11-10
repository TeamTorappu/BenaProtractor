#----------------------------------------
# 进入下一层时的效果
#----------------------------------------
import math

from dictionary import anne_dictionary

from analyzer import analyze_rogue_item, analyze_rogue_item_reward, analyze_relic_timing
from .attribute_rune import char_attribute_mul

# 每过一层，为本藏品叠加一个效果
def zone_into_buff(item_type,blackboard):
    # 目前只有char_attribute_mul
    if blackboard["buff"] == "char_attribute_mul":
        return {
            "main" : "每次进入下一层时，增加一个新效果：",
            "children" : [char_attribute_mul(item_type,blackboard)]
        }
    return {
        "main" : f"每次进入下一层时，增加一个新效果：{blackboard['buff']}（未翻译）"
    }

# 每过一层或进入特定层数时，发放奖励
def zone_into_reward(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    reward = analyze_rogue_item_reward(blackboard)
    if "zone" in blackboard:
        zone_name = anne_dictionary("rogue_zone",blackboard["zone"])
        timing += f"每次进入{zone_name}时，"
    else:
        timing += f"每次进入下一层时，"
    reward["main"] = timing + reward["main"]
    return reward

# 每过一层或进入特定层数时，消耗物品
def zone_into_cost(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    if "zone" in blackboard:
        zone_name = anne_dictionary("rogue_zone",blackboard["zone"])
        timing += f"进入{zone_name}时，"
    elif "is_zone_end_battle" in blackboard:
        timing += f"本层最终战结束后，进入下一层时，"
    result = {
        "main" : timing + "消耗玩家"
    }
    result["main"] += f" <rogue_item|{blackboard['id']}> × {math.floor(blackboard.get('count',1))}"

    return result

# 过一层或进入特定层数时，仅一次奖励物品
def zone_into_reward_once(item_type,blackboard):
    result = zone_into_reward(item_type,blackboard)
    result["main"] = result["main"].replace("每次进入下一层","进入下一层") + "（仅一次）"
    return result

# 过一层或进入特定层数时，仅一次消耗物品
def zone_into_cost_once(item_type,blackboard):
    result = zone_into_cost(item_type,blackboard)
    result["main"] = result["main"].replace("每次进入下一层","进入下一层") + "（仅一次）"
    return result

# 进入岁兽残识发放奖励（仅一次）
def secret_into_reward_once(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    reward = analyze_rogue_item_reward(blackboard)
    if "type" in blackboard:
        zone_name = anne_dictionary("rogue_zone",blackboard["zone"])
        reward["main"] = timing + "首次进入" + zone_name + "时" + reward["main"]
    else: # 默认树洞
        reward["main"] = timing + "首次进入隐藏层（包括岁兽残识）时" + reward["main"]
    return reward

# 进入岁兽残识发放奖励
def secret_into_reward(item_type,blackboard):
    timing = analyze_relic_timing(item_type,blackboard)
    reward = analyze_rogue_item_reward(blackboard)
    if "type" in blackboard:
        zone_name = anne_dictionary("rogue_zone",blackboard["zone"])
        reward["main"] = timing + "每次进入" + zone_name + "时" + reward["main"]
    else: # 默认树洞
        reward["main"] = timing + "每次进入隐藏层（包括岁兽残识）时" + reward["main"]
    return reward