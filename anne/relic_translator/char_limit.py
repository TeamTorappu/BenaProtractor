#----------------------------------------
# 可部署人数上限效果
#----------------------------------------
import math

from analyzer import to_delta

# 关卡内的可部署人数上限增减
def level_char_limit_add(item_type,blackboard):
    value = blackboard.get("value",0)
    if value < 0:
        return {"main": f"战斗中的可部署人数上限{to_delta(value)}（不会低于1）"}
    else:
        return {"main": f"战斗中的可部署人数上限{to_delta(value)}"}