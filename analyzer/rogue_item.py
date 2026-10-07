#----------------------------------------
# 解析肉鸽道具
#----------------------------------------
import math

from bena import ask_bena
from dictionary import anne_dictionary

# 道具的处理
# 返回道具类
def analyze_rogue_item(blackboard):
    if "id" in blackboard:
        item = ask_bena("rogue_item",blackboard["id"])
        return item
    return None

# 道具奖励的处理
# 返回结构体，可能会带有链接
def analyze_rogue_item_reward(blackboard):
    item_id = blackboard.get("id","")
    if item_id == "":
        return {"main" : "给予玩家 棍木"}
    if item_id.startswith("pool"):
            return {"main" : f"给予玩家 {blackboard['id']} 奖池中的随机一个物品"}
    item = ask_bena("rogue_item",blackboard["id"])
    if item.type == "COPPER": # 界园钱的特殊描述
        return {"main" : f"让 <rogue_item|{blackboard['id']}> 加入玩家钱盒"}
    return {"main" : f"给予玩家 <rogue_item|{blackboard['id']}> × {math.floor(blackboard.get('count',0))}"}