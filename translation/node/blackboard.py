#----------------------------------------
# 黑板类Node
#----------------------------------------
from .analyzer import anne_dictionary

# 记录黑板值
def node_AssignValueToBB(node):
    result = {
        "main" : f"设黑板值{node['_blackboardKey']} = "
    }
    if node["_copyFromKey"] != None:
        result["main"] += node['_copyFromKey']
    else:
        result["main"] += str(node['_value'])
    if node["_assignString"]:
        result["main"] += "（字符串格式）"
    return result

# 将召唤物的数量或最大数量记录到黑板中
def node_AssignTokenCardCntToBB(node):
    target_name = anne_dictionary("target",node["_targetType"])
    count_key = node["_countKey"]
    if node["_assignMaxCount"]:
        return {"main" : f"在黑板上将{target_name}的召唤物最大持有数记录为 {count_key}"}
    else:
        return {"main" : f"在黑板上将{target_name}的召唤物当前持有数记录为 {count_key}"}
