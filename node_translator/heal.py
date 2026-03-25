#----------------------------------------
# 治疗类Node
#----------------------------------------
from .analyzer import anne_dictionary

# 固定数值治疗
def node_FixedValueHeal(node):
    source_name = anne_dictionary("target",node["_sourceType"])
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_ignoreHealFree"]:
        return {"main" : f"让{source_name}治疗{target_name} {node['_healValueKey']} 点生命值（无视禁疗）"}
    else:
        return {"main" : f"让{source_name}治疗{target_name} {node['_healValueKey']} 点生命值"}