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