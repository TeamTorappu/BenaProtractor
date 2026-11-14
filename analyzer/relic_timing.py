#----------------------------------------
# 解析藏品生效时点
#----------------------------------------
from dictionary import enum_dictionary

# 生效时点的处理
# 返回生效时间的字符串
def analyze_relic_timing(item_type,blackboard):
    # 根据触发类型...
    if "trig_type" not in blackboard:
        return ""
    trig_type = blackboard["trig_type"]
    # 界园钱特殊处理
    if item_type == "COPPER_BUFF":
        return enum_dictionary("trig_type_copper",trig_type)+"，"
    # 返回时点文本
    return enum_dictionary("trig_type",trig_type)+"，"