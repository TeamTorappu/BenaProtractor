#----------------------------------------
# 格挡Node（超级集成
#----------------------------------------

# 格挡/护盾/屏障（还得根据黑板的具体情况具体分析）
def BlockDamage(node,blackboard):
    # 未解析参数：_useSource _sourceType
    #source_name = anne_dictionary("target",node["_sourceType"])
    name = "格挡此次伤害"
    features = []
    description = "若无法响应/伤害已被无效化本节点视为无法处理"
    # 使用动态值，说明是屏障
    if node["_useDynamicVar"]:
        if "dynamic" in blackboard:
            name = f"\"屏障\"：屏障量记载于[dynamic]，初始为{float(blackboard['dynamic'])}，若 伤害量 ≤ 屏障量 则消耗相应屏障量格挡此次伤害，否则消耗全部屏障量令伤害减少等同于屏障量的量"
        else:
            name = "\"屏障\"：屏障量记载于[dynamic]，若 伤害量 ≤ 屏障量 则消耗相应屏障量格挡此次伤害，否则消耗全部屏障量令伤害减少等同于屏障量的量"
        if node["_allowNegativeDynamicVar"]:
            features.append("允许负屏障值")
        if node["_showShieldUI"]:
            features.append("在血条上显示屏障值")
    elif node["_useFixedValue"]: # 使用定值，说明是林式阈值盾
        if "value" in blackboard:
            name = f"\"琉璃壁\"： 若 伤害量 ≤ {float(blackboard['value'])} 则格挡此次伤害，否则令伤害减少{float(blackboard['value'])}点"
        else:
            name = "\"琉璃壁\"：阈值记载于[value]， 若 伤害量 ≤ 阈值 则格挡此次伤害，否则令伤害减少等同于阈值的量"
    if node["_showDamageNumber"]:
        features.append("即使成功格挡也显示伤害数值")
    if node["_specifyBlockEffect"] != None:
        features.append("使用格挡特效"+node["_specifyBlockEffect"])
    # 检查伤害的施加方式
    if node["_filterApplyWay"]:
        if node["_applyWayFilter"] == "NONE": # 仅无类型
            features.append("仅响应施加方式为“无”的伤害")
        elif node["_applyWayFilter"] == "MELEE": # 无类型与近战
            features.append("仅响应施加方式为“近战”或“无”的伤害")
        elif node["_applyWayFilter"] == "RANGED": # 无类型与远程
            features.append("仅响应施加方式为“远程”或“无”的伤害")
        #elif node["_applyWayFilter"] == "ALL": # 全部都可以就不用写了
    if len(features) > 0:
        description += "；"+"；".join(features)
    return {
        "main" : name,
        "true" : "格挡成功",
        "false" : "格挡失败或无法处理",
        "description" : description
    }