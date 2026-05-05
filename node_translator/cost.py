#----------------------------------------
# 费用相关的Node
#----------------------------------------
from translator import anne_dictionary

# 修改费用
def node_ModifyCost(node):
    source_name = anne_dictionary("target",node["_sourceType"])
    shared_flags = []
    if node["_forceToDisplayNumber"]: # 强制显示正数？
        shared_flags.append(anne_dictionary("shared_flag","FORCE_TO_DISPLAY_NUMBER"))
    if node["_forceToDisplayNegativeNumber"]: # 强制显示负数？
        shared_flags.append(anne_dictionary("shared_flag","FORCE_TO_DISPLAY_NEGATIVE_NUMER"))
    if len(shared_flags) > 0:
        return {
            "main" : f"令持有的部署费用+{node['_blackboardKey']}",
            "description" : "、".join(shared_flags)
        }
    else:
        return {"main" : f"令持有的部署费用+{node['_blackboardKey']}"}
    
# 检查费用
def node_CheckCost(node):
    compare = anne_dictionary("compare",node["_condType"])
    compare_not = anne_dictionary("compare_not",node["_condType"])
    if node["_considerNegativeCost"]: # 考虑负费
        return {
            "main" : "检查当前关卡的部署费用（可\"贷款\"）",
            "true" : f"若持有的部署费用 {compare} 部署费用下限 + [{node['_blackboardKey']}]",
            "false" : f"若持有的部署费用 {compare_not} 部署费用下限 + [{node['_blackboardKey']}]"
        }
    else:
        return {
            "main" : "检查当前关卡的部署费用",
            "true" : f"若持有的部署费用 {compare} [{node['_blackboardKey']}]",
            "false" : f"若持有的部署费用 {compare_not} [{node['_blackboardKey']}]"
        }