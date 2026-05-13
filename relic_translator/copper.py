#----------------------------------------
# 界园的钱相关效果
#----------------------------------------
import math

from .analyzer import analyze_timing

# 钱的叠层，通常是投出时
def rogue_copper_unlock_layer(item_type,blackboard):
    timing = ""
    if "trig_type" in blackboard:
        timing = analyze_timing(item_type,blackboard)
    if "max" in blackboard and "init" in blackboard and blackboard["init"] != 0:
        return {
            "main" : f"{timing}叠加一层（初始{int(blackboard['init'])}层，上限{int(blackboard['max'])}层）"
        }
    elif "max" in blackboard:
        return {
            "main" : f"{timing}叠加一层（初始0层，上限{int(blackboard['max'])}层）"
        }
    elif "init" in blackboard and blackboard["init"] != 0:
        return {
            "main" : f"{timing}叠加一层（初始{int(blackboard['init'])}层，无上限）"
        }
    else:
        return {
            "main" : f"{timing}叠加一层（初始0层，无上限）"
        }
