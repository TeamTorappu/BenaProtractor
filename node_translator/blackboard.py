#----------------------------------------
# 黑板类Node
#----------------------------------------
from .analyzer import anne_dictionary

# 记录黑板值
def node_AssignValueToBB(node):
    result = {
        "main" : f"设 {node['_blackboardKey']} = "
    }
    if node["_copyFromKey"] != None:
        result["main"] += node['_copyFromKey']
    else:
        result["main"] += str(node['_value'])
    if node["_assignString"]:
        result["main"] += "（字符串格式）"
    return result

# 将属性值记录到黑板中
def node_AssignAttributeToBB(node):
    target_name = anne_dictionary("target",node["_targetType"])
    attribute = anne_dictionary("attribute",node["_attributeType"])
    if node["_scaleVar"] != None and node["_scaleVar"] != "":
        return {"main" : f"取{target_name}的{attribute}，设 {node['_blackboardKey']} = {attribute} × {node['_scaleVar']}"}
    else:
        return {"main" : f"取{target_name}的{attribute}，设 {node['_blackboardKey']} = {attribute}"}

# 将召唤物的数量或最大数量记录到黑板中
def node_AssignTokenCardCntToBB(node):
    target_name = anne_dictionary("target",node["_targetType"])
    count_key = node["_countKey"]
    if node["_assignMaxCount"]:
        return {"main" : f"在黑板上将{target_name}的召唤物最大持有数记录为 {count_key}"}
    else:
        return {"main" : f"在黑板上将{target_name}的召唤物当前持有数记录为 {count_key}"}

# 三合一节点：记录伤害值、记录模拟的计算伤害值、记录伤害影响差值
def node_AssignDamageValueToBlackboard(node):
    owner_name = anne_dictionary("target",node["_owner"])
    if node["_assignRealDelta"]:
        return {"main" : "设黑板值 damage 为 本次伤害实际造成的生命值减少量（最低为0）"}
    elif node["_assignValueWithoutCalculate"]:
        return {"main" : f"设黑板值 damage 为 {owner_name}的攻击力 × {node['_scaleKey']}"}
    else:
        damage_type = anne_dictionary("damage_type",node["_damageType"])
        return {"main" : f"设黑板值 damage 为 本次{damage_type}伤害的值（类型不对则为0）"}

# 确保黑板默认值，防止出错
def node_EnsureBlackboardDefaultValue(node):
    results = []
    has_overrided = False
    if node["_defaultSettings"] != None:
        for setting in node["_defaultSettings"]:
            if setting["overrideIfExists"]: # 默认值里写覆写，也是神人操作了
                has_overrided = True;
                if setting["valStr"] != None and setting["valStr"] != "":
                    results.append({"main" : f"不论是否已定义，设 {setting['key']} = {setting['valStr']}"})
                else:
                    results.append({"main" : f"不论是否已定义，设 {setting['key']} = {setting['val']}"})
            else:
                if setting["valStr"] != None and setting["valStr"] != "":
                    results.append({"main" : f"若 {setting['key']} 未定义，设 {setting['key']} = {setting['valStr']}"})
                else:
                    results.append({"main" : f"若 {setting['key']} 未定义，设 {setting['key']} = {setting['val']}"})
    if len(results) > 0:
        if has_overrided:
            return {
                "main" : "为确保黑板具有数据，批量设置以下数据（注意，部分设置会覆盖原有数据）：",
                "children" : results
            }
        else:
            return {
                "main" : "为确保黑板具有数据，批量设置以下数据：",
                "children" : results
            }
    return {"main" : "为黑板记录数据，但无事发生"}

# 从其他Buff的黑板中获取黑板值
def node_AssignBuffBlackboardFromOthers(node):
    target_name = anne_dictionary("target",node["_targetType"])
    buff_name = " " + node["_buffKey"] + " Buff"
    if node["_filterBuffSource"]:
        if node["_sourceType"]:
            buff_name = "由同一来源提供的" + buff_name
        else:
            buff_name = "由" + anne_dictionary("target",node["_sourceType"]) + "提供的" + buff_name
    return {
        "main" : f"尝试寻找{target_name}持有的首个{buff_name}，设自己黑板上的 {node['_blackboardKey']} = 该Buff黑板上的{node['_valueKey']}"
    }
