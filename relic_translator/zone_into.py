#----------------------------------------
# 进入下一层时的效果
#----------------------------------------
import math

from translator import anne_dictionary

from .analyzer import analyze_item, analyze_item_reward, analyze_timing
from .attribute_rune import rogue_char_attribute_mul

# 每过一层，为本藏品叠加一个效果
def rogue_zone_into_buff(item_type,blackboard):
    # 目前只有char_attribute_mul
    if blackboard["buff"] == "char_attribute_mul":
        return {
            "main" : "每次进入下一层时，增加一个新效果：",
            "children" : [rogue_char_attribute_mul(item_type,blackboard)]
        }
    return {
        "main" : f"每次进入下一层时，增加一个新效果：{blackboard['buff']}（未翻译）"
    }

# 每过一层或进入特定层数时，发放奖励
def rogue_zone_into_reward(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    reward = analyze_item_reward(blackboard)
    if "zone" in blackboard:
        zone_name = anne_dictionary("rogue_zone",blackboard["zone"])
        timing += f"进入{zone_name}时，"
    else:
        timing += f"每次进入下一层时，"
    reward["main"] = timing + reward["main"]
    return reward

# 每过一层或进入特定层数时，消耗物品
def rogue_zone_into_cost(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    if "zone" in blackboard:
        zone_name = anne_dictionary("rogue_zone",blackboard["zone"])
        timing += f"进入{zone_name}时，"
    else:
        timing += f"每次进入下一层时，"
    result = {
        "main" : timing + "消耗玩家"
    }
    item = analyze_item(blackboard)
    if item != None:
        result["main"] += f"{item.display_type} {item.display_name} × {math.floor(blackboard.get('count',1))}"
        result["link"] = blackboard['id']
    else:
        result["main"] += f" {blackboard['id']} × {math.floor(blackboard.get('count',1))}"
    if "is_zone_end_battle":
        result["description"] = "is_zone_end_battle = 1.0"
    return result

# 过一层或进入特定层数时，仅一次奖励物品
def rogue_zone_into_reward_once(item_type,blackboard):
    result = rogue_zone_into_reward(item_type,blackboard)
    result["main"] = result["main"].replace("每次进入下一层","进入下一层") + "（仅一次）"
    return result

# 过一层或进入特定层数时，仅一次消耗物品
def rogue_zone_into_cost_once(item_type,blackboard):
    result = rogue_zone_into_cost(item_type,blackboard)
    result["main"] = result["main"].replace("每次进入下一层","进入下一层") + "（仅一次）"
    return result