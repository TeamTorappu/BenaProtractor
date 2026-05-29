#----------------------------------------
# 界园的钱相关效果
#----------------------------------------
import math

from .analyzer import analyze_item, analyze_item_reward, analyze_timing

# 钱的叠层，通常是投出时
def rogue_copper_unlock_layer(item_type,blackboard):
    timing = analyze_timing(item_type,blackboard)
    if "max" in blackboard and "init" in blackboard and blackboard["init"] != 0:
        return {
            "main" : f"{timing}令钱叠加一层（初始{int(blackboard['init'])}层，上限{int(blackboard['max'])}层）"
        }
    elif "max" in blackboard:
        return {
            "main" : f"{timing}令钱叠加一层（初始0层，上限{int(blackboard['max'])}层）"
        }
    elif "init" in blackboard and blackboard["init"] != 0:
        return {
            "main" : f"{timing}令钱叠加一层（初始{int(blackboard['init'])}层，无上限）"
        }
    else:
        return {
            "main" : f"{timing}令钱叠加一层（初始0层，无上限）"
        }

# 投出特定数量的钱给予特定物品
def rogue_copper_draw_reward_lucky_level(item_type,blackboard):
    # 未解析黑板：divine_type
    reward = analyze_item_reward(blackboard)
    conditions = []
    # 厉钱
    if "low_min" in blackboard and "low_max" in blackboard:
        conditions.append(f"厉钱{int(blackboard['low_min'])}~{int(blackboard['low_max'])}枚")
    elif "low_min" in blackboard:
        conditions.append(f"厉钱至少{int(blackboard['low_min'])}枚")
    elif "low_max" in blackboard:
        conditions.append(f"厉钱0~{int(blackboard['low_max'])}枚")
    # 厉钱
    if "mid_min" in blackboard and "mid_max" in blackboard:
        conditions.append(f"衡钱{int(blackboard['mid_min'])}~{int(blackboard['mid_max'])}枚")
    elif "mid_min" in blackboard:
        conditions.append(f"衡钱至少{int(blackboard['mid_min'])}枚")
    elif "mid_max" in blackboard:
        conditions.append(f"衡钱0~{int(blackboard['mid_max'])}枚")
    # 花钱
    if "high_min" in blackboard and "high_max" in blackboard:
        conditions.append(f"花钱{int(blackboard['high_min'])}~{int(blackboard['high_max'])}枚")
    elif "high_min" in blackboard:
        conditions.append(f"花钱至少{int(blackboard['high_min'])}枚")
    elif "high_max" in blackboard:
        conditions.append(f"花钱0~{int(blackboard['high_max'])}枚")
    # 合并
    if len(conditions) > 1:
        reward["main"] = f"若一次投钱中同时投出了{'、'.join(conditions)}，" + reward["main"]
    elif len(conditions) == 1:
        reward["main"] = f"若一次投钱中投出了{conditions[0]}，" + reward["main"]
    else:
        reward["main"] = f"每次投钱后，" + reward["main"]
    return reward