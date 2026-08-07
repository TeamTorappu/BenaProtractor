#----------------------------------------
# 屏障相关Node
#----------------------------------------
from translator import anne_dictionary

# 获取当前已有屏障值
def node_FilterByShieldValue(node):
    target_name = anne_dictionary("target",node["_targetType"])
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    buff_name = "Buff"
    shield_value = str(node["_shieldValue"])
    if node["_shieldKey"] != None and node["_shieldKey"] != "" and node["_shieldKey"] != "invalid":
        shield_value = f"[{node['_shieldKey']}]（默认为{shield_value} ）"
    if node["_enableFilterSource"]:
        if node["_filterSource"] == "BUFF_SOURCE" and not node["_filterHostOrToken"]:
            buff_name = "与本Buff同来源的Buff"
        elif node["_filterHostOrToken"]:
            buff_name = "来源于" + anne_dictionary("target",node["_filterSource"]) + "的主人/召唤物的BUFF"
        else:
            buff_name = "来源于" + anne_dictionary("target",node["_filterSource"]) + "的BUFF"
    result = {
        "main" : f"检查{target_name}的所有{buff_name}中的\"屏障值\"之和",
        "description" : "其实就是检查所有Buff的 [dynamic] 黑板，即使该Buff并不作屏障用也会被视为\"屏障值\"",
        "true" : f"若\"屏障值\"之和 {compare} {shield_value}",
        "false" : f"若\"屏障值\"之和 {compare_not} {shield_value}"
    }
    if node["_enableFilterSource"] and node["_passIfNoSource"]: # 何意味的补充判定
        result["true"] += "，或不存在该来源的Buff"
        result["false"] += "，且存在至少一个该来源的Buff"
    return result
