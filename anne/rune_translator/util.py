#----------------------------------------
# 其他符文
#----------------------------------------
from analyzer import to_delta

# 可携带数量增减
def global_squad_num_limit(blackboard,selector=None):
    value = int(blackboard["value"]) if "value" in blackboard else 0
    power = to_delta(value)
    return {"main" : f"战斗开始前，可携带干员数量{power}"}
