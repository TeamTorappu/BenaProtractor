#----------------------------------------
# 概率类Node
#----------------------------------------
# 100面骰
def node_Dice(node):
    return {
        "main" : "取1~100之内的随机整数（投掷100面骰，类似COC规则）",
        "true" : f"若出值 ≤ {node['_probKey']}（检定成功)",
        "false" : f"若出值 ＞ {node['_probKey']}（检定失败）"
    }

# 100面骰，伪随机分布算法
def node_DicePRD(node):
    return {
        "main" : f"取1~100之内的随机整数（投掷100面骰，类似COC规则）",
        "description" : f"初始概率为零，每未通过一次检定概率加一倍直至成功时重置；记录于全局黑板{node['_prdKey']}",
        "true" : f"若出值 ≤ {node['_probKey']}（检定成功)",
        "false" : f"若出值 ＞ {node['_probKey']}（检定失败）"
    }