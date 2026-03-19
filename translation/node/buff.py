#----------------------------------------
# Buff类Node
#----------------------------------------
from .analyzer import anne_dictionary, analyze_buff

# 创建Buff
def node_CreateBuff(node):
    # 未解析参数：_useSpecialBuffSource _specialBuffSource _finishDerivedBuffIfParentFinish
    target_name = anne_dictionary("target",node["_buffOwner"])
    buff_name = "Buff"
    if node["_isDerivedBuff"]: # 属于子Buff
        buff_name = "本Buff的子Buff"
    return {
        "main" : f"为{target_name}创建一个{buff_name}：",
        "children" : [analyze_buff(node['_buff'])]
    }
    
# 创建Buff，带召唤物主人处理
def node_CreateBuffUseHostAsSource(node):
    # 未解析参数：_finishDerivedBuffIfParentFinish
    target_name = anne_dictionary("target",node["_targetType"])
    source_name = anne_dictionary("target",node["_sourceType"])
    buff_name = "Buff"
    if node["_isDerivedBuff"]: # 属于子Buff
        buff_name = "本Buff的子Buff",
    if node["_createOnTargetHost"]: # 对目标召唤物的本尊
        target_name = target_name + "(召唤物)的持有者"
    return {
        "main" : f"让{source_name}为{target_name}创建一个{buff_name}：",
        "children" : [analyze_buff(node['_buffData'])]
    }

# 结束此Buff
def node_FinishBuff(node):
    # 未解析参数：_updateOverrideMap
    if node["_decCntIfStack"]:
        return {"main" : "此Buff叠层减少一层；若减少至0层则此Buff结束"}
    else:
        return {"main" : "此Buff结束"}

# 结束特定Buff(s)
def node_FinishBuffsById(node):
    # 未解析参数：_updateOverrideMap _finishHostBuff
    target_name = anne_dictionary("target",node["_targetType"])
    buff_name = "特定Buff（取决于黑板）" if node["_loadFromBlackboard"] else node["_buffKey"]
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
            action = f"减少黑板{node['_decCntKey']}值层叠层（变为0层时该Buff结束）"
        else:
            action += f"减少{node['_decCnt']}层叠层（变为0层时该Buff结束）"
    return {"main" : f"令{target_name}身上的{buff_name}{action}"}
    
# 结束此Buff的所有子Buff
def node_FinishDerivedBuff(node):
    # 未解析参数：_updateOverrideMap
    return {"main" : "结束此Buff的所有子Buff"}
    
# 结束某Buff的所有子Buff
def node_FinishDerivedBuffById(node):
    # 未解析参数：_updateOverrideMap _decCntIfStack
    if node["_decCntIfStack"]:
        return {"main" : f"结束{node['_buffKey']}的所有无叠层的子Buff；可叠层的子Buff减少一层叠层，若减少至0层则其结束"}
    else:
        return {"main" : f"结束{node['_buffKey']}的所有子Buff"}
