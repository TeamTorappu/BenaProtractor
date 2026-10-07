#----------------------------------------
# 解析属性加成
#----------------------------------------
from .delta_and_percent import to_delta, to_delta_percent, to_percent
from dictionary import anne_dictionary, is_anne_key

# 获取key是否是属性值的方法
# 属性字典里存了所有属性类型，因此直接用了
def is_attribute_key(key: str):
    return is_anne_key("attribute",key.upper())

# 解析属性修饰器
def analyze_attribute_modifiers(modifiers: list,blackboard: dict = {}):
    features = []
    for modifier in modifiers:
        attr_name = anne_dictionary("attribute",modifier["attributeType"])
        formula = modifier["formulaItem"]
        value = modifier["value"]
        value_str = str(value)
        # 获取数据加成/减少的写法
        if modifier["fetchBaseValueFromSourceEntity"]: # 读取自本尊，特殊判断
            if formula == "FINAL_SCALER": # 实际为终加
                if modifier["loadFromBlackboard"]:
                    bb_str = modifier["attributeType"].lower()  # 理论上是和type同名的黑板值
                    if bb_str in blackboard:
                        value = float(blackboard[bb_str])
                        value_str = f"+(Buff来源{attr_name})×{to_percent(value,True)}(终加)"
                    else:
                        value_str = f"+(Buff来源{attr_name})×[{bb_str}](终加)"
                else:
                    value_str = f"+(Buff来源{attr_name})×{to_percent(value,True)}(终加)"
            else:
                value_str = f"+???"
        elif modifier["loadFromBlackboard"]: # 读取自黑板，那value本身没用了，写个未知数
            bb_str = modifier["attributeType"].lower()  # 理论上是和type同名的黑板值
            if bb_str in blackboard:
                value = float(blackboard[bb_str])
                if formula == "FINAL_SCALER": # yj的小巧思会让终乘在负的情况下+1，实际徒增学习和排错成本
                    value_str = to_percent(value,True) + "(终乘)"
                elif formula == "MULTIPLIER": # 直乘就没有这种小巧思
                    value_str = to_delta_percent(value) + "(直乘)"
                elif formula == "ADDITION": # 剩下两个只看正负号
                    value_str = to_delta(value) + "(直加)"
                elif formula == "FINAL_ADDITION": # 剩下两个只看正负号
                    value_str = to_delta(value) + "(终加)"
            else:
                if formula == "ADDITION":
                    value_str = "+["+bb_str+"](直加)"
                elif formula == "MULTIPLIER":
                    value_str = "+["+bb_str+"]%(直乘)"
                elif formula == "FINAL_ADDITION":
                    value_str = "+["+bb_str+"](终加)"
                elif formula == "FINAL_SCALER":
                    value_str = "×["+bb_str+"]%(终乘)"
        else:
            if formula == "FINAL_SCALER": # yj的小巧思会让终乘在负的情况下+1，实际徒增学习和排错成本
                value_str = to_percent(value,True) + "(终乘)"
            elif formula == "MULTIPLIER": # 直乘就没有这种小巧思
                value_str = to_delta_percent(value) + "(直乘)"
            elif formula == "ADDITION": # 剩下两个只看正负号
                value_str = to_delta(value) + "(直加)"
            elif formula == "FINAL_ADDITION": # 剩下两个只看正负号
                value_str = to_delta(value) + "(终加)"
        # 根据算法
        features.append(attr_name+value_str)
    return features
