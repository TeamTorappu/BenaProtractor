#----------------------------------------
# Buff类Node
#----------------------------------------
import math
from .analyzer import analyze_target_options, anne_dictionary, analyze_buff

# 创建Buff
def node_CreateBuff(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    target_name = anne_dictionary("target",node["_buffOwner"])
    buff_name = "本Buff的附属Buff" if node["_isDerivedBuff"] else "Buff"
    result = analyze_buff(node['_buff'])
    result["main"] = f"为{target_name}创建一个{buff_name}：" + result["main"]
    if node["_useSpecialBuffSource"]:
        buff_source = anne_dictionary("target",node["_specialBuffSource"])
        result["main"] = "令" + buff_source + result["main"]
    return result

# 创建多个独立但同名的Buff
def node_CreateBuffs(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    target_name = anne_dictionary("target",node["_buffOwner"])
    buff_name = "Buff"
    result = analyze_buff(node["_buffPair"]["buff"])
    num = node["_buffPair"]["count"]
    if node["_buffPair"]["useBlackboard"]:
        num = "max_times"
        if node["_buffPair"]["peeling"] != 0: # 减值
            num = "max_times - " + str(abs(node["_buffPair"]["peeling"]))
    elif node["_buffPair"]["peeling"] != 0: # 减值，固定值这里一般不用
        num = num + node["_buffPair"]["peeling"]
    result["main"] = f"为{target_name}创建 {num} 个{buff_name}：" + result["main"]
    return result

# 创建多层Buff
def node_CreateBuffStacked(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    target_name = anne_dictionary("target",node["_buffOwner"])
    buff_name = "本Buff的附属Buff" if node["_isDerivedBuff"] else "Buff"
    result = analyze_buff(node['_buff'])
    # 只有两种情况下可以创建多层Buff：1. Buff叠层类型为STACK；2. Buff不开启覆盖且"_isDisableOverrideBuff"参数为真
    # 其他情况下与CreateBuff基本相同，创建一个Buff
    if (node["_buff"]["overrideType"] == "STACK") or (node["_isDisableOverrideBuff"] and node["_buff"]["disableOverride"]):
        stacks = node["_stackCnt"] if node["_stackCntKey"] == None else node["_stackCntKey"]
        result["main"] = f"为{target_name}创建{stacks}个{buff_name}：" + result["main"]
    else:
        result["main"] = f"为{target_name}创建一个{buff_name}：" + result["main"]
    return result

# 依照ID创建数据库Buff
def node_CreateBuffById(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    target_name = anne_dictionary("target",node["_buffOwner"])
    buff_name = "本Buff的附属Buff" if node["_isDerivedBuff"] else "Buff"
    if node["_loadFromBlackboard"]:
        return {"main" : f"为{target_name}创建一个{buff_name}（读取自数据库中 [buff_key] 所记述的Buff）"}
    else:
        return {
            "main" : f"为{target_name}创建一个{buff_name}：<{node['_buffKey']}>（读取自数据库）",
            "link" : "buff."+node["_buffKey"]
        }
    
# 创建Buff，将召唤物主人作为来源
def node_CreateBuffUseHostAsSource(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    target_name = anne_dictionary("target",node["_targetType"])
    source_name = anne_dictionary("target",node["_sourceType"])
    buff_name = "Buff"
    result = analyze_buff(node['_buffData'])
    if node["_isDerivedBuff"]: # 属于附属Buff
        buff_name = "本Buff的附属Buff"
    if node["_createOnTargetHost"]: # 对目标召唤物的本尊
        target_name = target_name + "（召唤物）的持有者"
    result["main"] = f"让{source_name}为{target_name}创建一个{buff_name}：" + result["main"]
    return result

# 由召唤物给主人创建Buff
def node_CreateBuffToHost(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    source_name = anne_dictionary("target",node["_sourceType"])
    buff_name = "Buff"
    result = analyze_buff(node['_buffData'])
    if node["_isDerivedBuff"]: # 属于附属Buff
        buff_name = "本Buff的附属Buff"
    result["main"] = f"让{source_name}（召唤物）为其持有者创建一个{buff_name}：" + result["main"]
    return result

# 随机创建以下Buff之一
def node_RandomCreateBuff(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    if len(node["_datas"]) == 0:
        return {"main" : "随机创建Buff，但是随机列表为空"}
    result = {
        "main" : "随机创建以下Buff之一：",
        "children" : []
    }
    same_target = True
    target = ""
    # 预处理，先检查一下是不是所有Buff都上给同一个人
    for _data in node["_datas"]:
        if target == "":
            target = _data["buffOwner"]
        elif target != _data["buffOwner"]:
            same_target = False
            break
    if same_target:
        if node["_isDerivedBuff"]:
            result["main"] = f"为{anne_dictionary('target',target)}随机创建下列附属Buff之一（均为本Buff的附属Buff）："
        else:
            result["main"] = f"为{anne_dictionary('target',target)}随机创建下列Buff之一："
    else:
        if node["_isDerivedBuff"]:
            result["main"] = f"随机进行以下一项Buff的创建："
        else:
            result["main"] = f"随机进行以下一项附属Buff的创建（均为本Buff的附属Buff）："
    # 创建Buff列表
    if node["_buffWithWeight"]: # 带权重
        result["description"] = "将根据权重分配概率"
        for _data in node["_datas"]:
            buff = analyze_buff(_data["buff"])
            weight = _data["weight"]
            if _data["weightKey"] != None and _data["weightKey"] != "":
                weight = "[" + _data["weightKey"] + "]"
            if not same_target:
                owner = anne_dictionary("target",_data["buffOwner"])
                buff["main"] = "为"+owner+"创建："+buff["main"]
            buff["main"] = weight+" - "+buff["main"]
            result["children"].append(buff)
    else:
        for _data in node["_datas"]:
            buff = analyze_buff(_data["buff"])
            if not same_target:
                owner = anne_dictionary("target",_data["buffOwner"])
                buff["main"] = "为"+owner+"创建："+buff["main"]
            result["children"].append(buff)
    return result

# 在一定区域内创建Buff
def node_CreateBuffInRange(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    source_name = anne_dictionary("target",node["_sourceType"])
    target_name = anne_dictionary("target",node["_targetType"])
    target_options = analyze_target_options(node["_targetOptions"])
    buffs = []
    for buff_data in node["_buffs"]:
        buffs.append(analyze_buff(buff_data))
    range_name = ""
    max_target = "所有"
    # 处理基本信息
    if node["_targetType"] != "BUFF_OWNER":
        range_name = f"以{target_name}为中心，"
    if node["_useHostAsSource"]:
        source_name = source_name + "(召唤物)的主人"
        
    if node["_limitMaxTarget"]:
        if node["_maxTargetKey"] != None:
            max_target += f"的[{node['_maxTargetKey']}]个"
        else:
            max_target += f"的[max_target]个"
    # 处理范围信息
    if node["_useRadius"]: # 半径制（最高优先度）
        range_name += target_name + f"半径[range_radius]（默认{node['_radius']}）内"
    elif node["_useRangeToShow"]: # 特定模式的显示范围制
        mode_name = "当前模式" if node["_rangeModeIndex"] == -1 else f"{node['_rangeModeIndex']}号模式"
        if node["_useTargetRangeInsteadOfSource"]:
            range_name += target_name
        else:
            range_name += source_name
        range_name += mode_name
        if node["_rangeTargetSideType"] == "ALLY":
            range_name += "的\"青色\"显示范围内"
        elif node["_rangeTargetSideType"] == "ENEMY":
            range_name += "的\"橙色\"显示范围内"
        else:
            range_name += "的显示范围内"
    elif node["_useAttackRange"]: # 攻击范围数据制
        if node["_useTargetRangeInsteadOfSource"]:
            range_name += target_name + "攻击范围（数据）内"
        else:
            range_name += source_name + "攻击范围（数据）内"
    elif node["_useCurrentModeRange"]: # 当前模式的攻击范围制
        if node["_useTargetRangeInsteadOfSource"]:
            range_name += target_name + f"当前模式的攻击范围内"
        else:
            range_name += source_name + f"当前模式的攻击范围内"
    elif node["_useGlobalRange"]: # 全局范围
        range_name = "场上所有"
    elif node["_checkGiantTrapAllLocateTiles"]: # 巨大装置
        range_name += target_name +"（巨型装置）占据的地块上" # 存疑
    else:
        range_name = "？"
    # 部署类型额外判定
    if node["_filterByBuildableType"]:
        target_options["main"] = "部署类型为"+anne_dictionary("buildable_type_filter",node['_allowedBuildableType'])+"的"+target_options["main"]
    # 返回结果
    result = {
        "main" : f"选择{range_name}{max_target}{target_options['main']}，\"依次\"为这些单位创建以下Buff：" ,
        "description" : f"Buff来源为{source_name}",
        "children" : buffs
    }
    # 额外信息
    if node["_isDerivedBuff"]:
        result["description"] += "，且均为本Buff的附属Buff"
    if node["_excludeTarget"]:
        result["description"] += f"；不包含{target_name}本身"
    if node["_alwaysIncudeCurAtkTarget"]:
        result["description"] += f"；始终包含当前攻击的主目标"
    if node["_alwaysIncludeSourceBlocker"]:
        result["description"] += f"；始终包含阻挡来源的单位"
    if "description" in target_options:
        result["description"] += "；" + target_options["description"]
    # 排序
    if node["_randomTarget"]:
        result["main"] = f"选择{range_name}随机一名{target_options['main']}，为该单位创建以下Buff：" ,
    elif node["_filterTargets"] and node["_filterType"] != "ALL":
        result["main"] = result["main"][:-1] + f"（使用 {node['_filterType']} 过滤器）："
    return result

# 为自己的所有召唤物创建Buff
def node_CreateBuffToToken(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    source_name = anne_dictionary("target",node["_sourceType"])
    target_num = "首个" if node["_onlyToFirstTarget"] else "所有"
    conditions = []
    buff_name = "Buff"
    if node["_isDerivedBuff"]: # 属于附属Buff
        buff_name = "本Buff的附属Buff"
    result = analyze_buff(node["_buffData"])
    if node["_excludeTarget"]: # 排除目标召唤物
        target_name = anne_dictionary("target",node["_targetType"])
        conditions.append(f"非{target_name}的")
    if node["_excludeByBuffKey"]: # 排除具有指定Buff的召唤物
        conditions.append(f"不具有 <{node['_excludeBuffKey']}> Buff的")
        if "link" in result:
            result["link"] = "buff." + node['_excludeBuffKey'] + "," + result["link"]
    result["main"] = f"为{source_name}{target_num}{'且'.join(conditions)}召唤物创建{buff_name}：" + result["main"]
    return result

# 使用能力选择器创建Buff
def node_CreateBuffUseAbilitySelector(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    buff_source_name = anne_dictionary("target",node["_buffSourceType"] if node["_overrideBuffSourceType"] else node["_sourceType"]) # 覆写Buff来源
    ability_source_name = anne_dictionary("target",node["_abilityFromTargetType"] if node["_useAbilityFromTarget"] else node["_sourceType"]) # 覆写能力来源  
    ability_name = node["_abilityName"]
    if buff_source_name != ability_source_name:
        ability_name = f"{ability_source_name}的{ability_name}"
    result = analyze_buff(node['_buff'])
    buff_name = "Buff"
    if node["_isDerivedBuff"]: # 属于附属Buff
        buff_name = "本Buff的附属Buff"
    if node["_actionFailedIfNoTarget"]:
        result["true"] = "若该选择器存在可选目标"
        result["false"] = "若该选择器不存在可选目标"
    if node["_targetType"] != node["_sourceType"]: # 起点
        position_name = anne_dictionary("target",node["_targetType"])
        result["main"] = f"让{buff_source_name}借用{position_name}所在位置和部署方向，使用{ability_name}能力的选择器，对选中目标创建{buff_name}：" + result["main"]
    else:
        result["main"] = f"让{buff_source_name}使用{ability_name}能力的选择器，对选中目标创建{buff_name}：" + result["main"]
    return result

# 向特定阵营的所有单位创建Buff
def node_CreateBuffToCertainSideUnits(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    side_name = anne_dictionary("side_type",node["_sideMask"])
    buff_name = "Buff"
    result = analyze_buff(node['_buff'])
    if node["_isDerivedBuff"]: # 属于附属Buff
        buff_name = "本Buff的附属Buff"
    if node["_noSource"]:
        result["main"] = f"为所有{side_name}单位创建{buff_name}（无来源）：" + result["main"]
    else:
        result["main"] = f"让持有者为所有{side_name}单位创建{buff_name}：" + result["main"]
    return result


# 触发此Buff（常用于循环或控制附属Buff）
def node_TriggerBuff(node):
    if node["_force"]:
        if node["_triggerDerivedBuffs"]:
            return {"main" : "强制触发此Buff与旗下所有附属Buff"}
        else:
            return {"main" : "强制触发此Buff"}
    else:
        if node["_triggerDerivedBuffs"]:
            return {"main" : "触发此Buff与旗下所有附属Buff"}
        else:
            return {"main" : "触发此Buff"}

# 结束此Buff
def node_FinishBuff(node):
    # 未解析参数：_updateOverrideMap
    if node["_decCntIfStack"]:
        return {"main" : "此Buff叠层减少一层（若减少至0层则此Buff结束）"}
    else:
        return {"main" : "此Buff结束"}

# 结束特定Buff(s)
def node_FinishBuffsById(node):
    # 未解析参数：_updateOverrideMap _finishHostBuff
    target_name = anne_dictionary("target",node["_targetType"])
    buff_name = "黑板[buff_key]指定的Buff" if node["_loadFromBlackboard"] else f" <{node['_buffKey']}> "
    # 仅限某人的buff
    if node["_checkBuffSource"]:
        source_name = anne_dictionary("target",node["_sourceType"])
        if node["_alsoClearNullSource"]:
            buff_name = "来源于" + source_name + "或无来源的" + buff_name
        else:
            buff_name = "来源于" + source_name + "的" + buff_name
    action = f"结束"
    if node["_decCntIfStack"]:
        if node["_decCntKey"] != None:
            action = f"减少黑板{node['_decCntKey']}值层叠层（变为0层时将结束）"
        else:
            action = f"减少{node['_decCnt']}层叠层（变为0层时将结束）"
    result = {"main" : f"令{target_name}身上的{buff_name}{action}"}
    if node["_loadFromBlackboard"]:
        result["link"] = "buff." + node["_buffKey"]
    return result

# 结束此Buff的所有附属Buff
def node_FinishDerivedBuff(node):
    # 未解析参数：_updateOverrideMap
    return {"main" : "结束此Buff的所有附属Buff"}
    
# 结束某Buff的所有附属Buff
def node_FinishDerivedBuffById(node):
    # 未解析参数：_updateOverrideMap _decCntIfStack
    result = {}
    if node["_decCntIfStack"]:
        result["main"] = f"结束 <{node['_buffKey']}> 的所有无叠层的附属Buff；而可叠层的附属Buff将减少一层叠层（变为0层时将结束）"
    else:
        result["main"] = f"结束 <{node['_buffKey']}> 的所有附属Buff"
    result["link"] = "buff." + node["_buffKey"]
    return result

# 将自己挂载为其他Buff的附属Buff
# 实际逻辑是挂一个附属Buff，然后结束自身
def node_AttachAsDerivedBuffById(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    target_name = anne_dictionary("target",node["_sourceType"])
    if node["_attachToSourceHost"]:
        target_name += "(召唤物)的主人"
    buff_key = "黑板[buff_key]指定的Buff" if node["_loadFromBlackboard"] else f" <{node['_buffKey']}> "
    result = {"main" : f"若此Buff不是附属Buff，复制一个相同数据的Buff作为{target_name}下{buff_key}的附属Buff，然后结束此Buff"}
    if node["_finishDerivedBuffIfNoParent"]:
        result["description"] = "若不存在目标Buff，仅结束此Buff"
    if node["_loadFromBlackboard"]:
        result["link"] = "buff." + node["_buffKey"]
    return result
