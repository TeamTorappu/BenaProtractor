#----------------------------------------
# 计算类Node
#----------------------------------------
# 用各种参数计算黑板值
def node_CalculateBlackboardValueViaParams(node):
    # 未解析参数：
    place_name = ""
    input_key = node["_inputKey"]
    output_key = node["_outputKey"]
    formula = input_key
    # 确认处理上下文
    if node["_useAbilityBlackboard"] and node["_abilityName"] != "":
        place_name = f"在能力{node['_abilityName']}的黑板中，"
    # 解析计算方式
    if node["_multiplyParamKey"] != None and node["_multiplyParamKey"] != "": # 乘法运算
        formula += " × " + node["_multiplyParamKey"]
    if node["_dividedParamKey"] != None and node["_dividedParamKey"] != "": # 除法运算
        if node["_useRemainder"]: # 取余
            formula += " rem " + node["_dividedParamKey"]
        else:
            formula += " ÷ " + node["_dividedParamKey"]
    if node["_addParamKey"] != None and node["_addParamKey"] != "": # 加法运算
        formula += " + " + node["_addParamKey"]
    if node["_minusParamKey"] != None and node["_minusParamKey"] != "": # 减法运算
        formula += " - " + node["_minusParamKey"]
    # 上下限
    if node["_minValueKey"] != None and node["_minValueKey"] != "": # 下限
        if node["_maxValueKey"] != None and node["_maxValueKey"] != "":
            formula = "clamp("+formula+","+node["_minValueKey"]+","+node["_maxValueKey"]+")"
        else:
            formula = "max("+formula+","+node["_minValueKey"]+")"
    elif node["_maxValueKey"] != None and node["_maxValueKey"] != "": # 上限
        formula = "min("+formula+","+node["_maxValueKey"]+")"
    # 后续处理
    if node["_finalAbs"]: # 绝对值
        formula = "| "+formula+" |"
    if node["_finalCeil"]: # 向上取整
        formula += "（向上取整）"
    elif node["_finalFloor"]: # 向上取整
        formula += "（向下取整）"
    elif node["_finalRound"]: # 向上取整
        formula += "（就近取整，四舍六入五成双）"
    # 返回完整公式
    return {"main" : f"{place_name}计算黑板值。将 {output_key} 设置为 {formula}"}