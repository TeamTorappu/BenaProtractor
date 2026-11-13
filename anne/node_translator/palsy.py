#----------------------------------------
# 麻痹相关Node
#----------------------------------------
from dictionary import anne_dictionary

# 添加麻痹
def PalsyBuffAdd(node,blackboard):
    # 两者皆是，这就是答案
    target_name = anne_dictionary("target",node.get("_target",node["_targetType"]))
    return {
        "main" : f"令{target_name}的麻痹控制器添加一层麻痹",
        "description" : "即\"若单位已有麻痹Buff，令该Buff叠层直至上限；并记录溢出层数...\""
    }

# 触发麻痹震颤
def TriggerPalsy(node,blackboard):
    target_name = anne_dictionary("target",node["_target"])
    return {"main" : f"让{target_name}触发麻痹，产生麻痹震颤"}

# 更新麻痹衰减间隔
def UpdatePalsyDecayInterval(node,blackboard):
    # 未解析参数：_targetType
    return {
        "main" : f"获取麻痹衰减间隔，用其覆写此Buff的触发间隔",
        "description" : f"麻痹衰减间隔 = max(max(一减状态抵抗率 × (1 - 麻痹异常抵抗率),0.001) × [interval],{node["_minInterval"]})"
    }