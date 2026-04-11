#----------------------------------------
# 概率类Node
#----------------------------------------
# 100面骰
def node_Dice(node):
    return {
        "main" : "投掷一枚\"百面骰\"，进行检定（取1~100之内的随机整数）",
        "true" : f"若出值 ≤ [{node['_probKey']}]（检定成功)",
        "false" : f"若出值 > [{node['_probKey']}]（检定失败）"
    }

# 100面骰，伪随机分布算法
def node_DicePRD(node):
    return {
        "main" : f"投掷一枚\"伪随机分布式百面骰\"，进行检定（取1~100之内的随机整数）",
        "description" : f"基础概率依[{node['_probKey']}]查询，每次失败增加一倍概率直至成功时重置；连续失败次数记录于全局黑板[{node['_prdKey']}]",
        "true" : f"若出值 ≤ (连续失败次数 + 1) * 基础概率（检定成功)",
        "false" : f"若出值 > (连续失败次数 + 1) * 基础概率（检定失败）"
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