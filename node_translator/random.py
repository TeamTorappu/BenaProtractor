#----------------------------------------
# 概率类Node
#----------------------------------------
# 骰子
from .analyzer import anne_dictionary

def node_Dice(node):
    return {
        "main" : "投掷一枚\"骰子\"，进行概率检定（取0.0~100.0之内的随机浮点数，不包括100.0）",
        "true" : f"若出值 ≤ [{node['_probKey']}] × 100（检定成功)",
        "false" : f"若出值 > [{node['_probKey']}] × 100（检定失败）"
    }

# 骰子，伪随机分布算法
def node_DicePRD(node):
    return {
        "main" : f"投掷一枚\"伪随机分布式骰子\"，进行概率检定（取0.0~100.0之内的随机浮点数，不包括100.0）",
        "description" : f"基础概率依[{node['_probKey']}]查询，每次失败增加一倍概率直至成功时重置；连续失败次数记录于全局黑板[{node['_prdKey']}]",
        "true" : f"若出值 ≤ (连续失败次数 + 1) * 基础概率 × 100（检定成功)",
        "false" : f"若出值 > (连续失败次数 + 1) * 基础概率 × 100（检定失败）"
    }

# 骰子，概率合并处理
def node_DiceByBuffKeys(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_isReverseProb"]: # 成功一次
        return {
            "main" : "投掷一枚\"合并骰子\"，进行概率检定（取0.0~100.0之内的随机浮点数，不包括100.0）",
            "description" : f"取{target_name}身上所有 <{node['_buffKey']}> Buff的 [{node['_probKey']}] ，计算\"成功一次\"的概率作为实际概率",
            "true" : f"若出值 ≤ (1 - (1 - [{node['_probKey']}]₁) × (1 - [{node['_probKey']}]₂) × ...) × 100（检定成功)",
            "false" : f"若出值 > (1 - (1 - [{node['_probKey']}]₁) × (1 - [{node['_probKey']}]₂) × ...) × 100（检定失败）"
        }
    else:  # 全部成功
        return {
            "main" : "投掷一枚\"合并骰子\"，进行概率检定（取0.0~100.0之内的随机浮点数，不包括100.0）",
            "description" : f"取{target_name}身上所有 <{node['_buffKey']}> Buff的 [{node['_probKey']}] ，计算\"全部成功\"的概率作为实际概率",
            "true" : f"若出值 ≤ [{node['_probKey']}]₁ × [{node['_probKey']}]₂ × ... × 100（检定成功)",
            "false" : f"若出值 > [{node['_probKey']}]₁ × [{node['_probKey']}]₂ × ... × 100（检定失败）"
        }

# 区间随机小数
def node_RandomSetter(node):
    max_key = node["_targetKey"]+"_max" #别问，yj的逻辑真的这么写的
    min_key = node["_targetKey"]+"_min" #别问，yj的逻辑真的这么写的
    if node["_convertToInt"]: # 最终向下取整
        return {
            "main" : f"设置 [{node['_targetKey']}] 为 [{min_key}] ~ [{max_key}] 的一个随机浮点数（不包含[{max_key}]），随后令其向下取整",
            "description" : f"若上下限均为整数，此逻辑相当于取 [{min_key}] ~ ([{max_key}]-1) 的一个随机整数"
        }
    else:
        return {"main" : f"设置 [{node['_targetKey']}] 为 [{min_key}] ~ [{max_key}] 的一个随机浮点数（不包含[{max_key}]）"}