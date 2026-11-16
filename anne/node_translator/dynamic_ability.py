#----------------------------------------
# 动态能力相关Node
#----------------------------------------
from dictionary import enum_dictionary

# 挂载新的动态能力
def AddRuntimeDynamicAbility(node,blackboard):
    target_name = enum_dictionary("target",node["_target"])
    position = "根目录(./...)" if node["_atRoot"] else "常见能力(./CommonAbilities/...)"
    return {
        "main" : f"在{target_name}的 {position} 下，挂载一个动态能力：{node['_prefabKey']}",
        "description" : "以此挂载的动态能力会继承此Buff的黑板"
    }
