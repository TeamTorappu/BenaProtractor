#----------------------------------------
# 弹道类Node
#----------------------------------------
from .analyzer import anne_dictionary

# 发出弹道
def node_EmitProjectile(node):
    # 未解析参数：_buffDataList _extraBlackboard _overwriteBlackboard _useProjectileAsTarget _useSnapshotAbilityWhenFromBuff
    source_name = anne_dictionary("target",node["_sourceType"]) if node["_useSourceAsProjectileSource"] else "持有者"
    target_name = anne_dictionary("target",node["_targetType"])
    target_point = target_name + "的" + anne_dictionary("mount_point",node["_mountPoint"]) + "吸附点"
    start_point = "所在地块中心" if node["_emitOnRootTile"] else (source_name + "的弹道出发点")
    projectile_event = anne_dictionary("projectile_event",node["_ev"])
    projectile = node["_projectileKey"]
    features = []
    result = {}
    # 弹道目的地处理
    if node["_targetPosFromBB"]: # 从黑板中读取目的地数据
        target_point = "黑板记述的地块" if node["_useTileAsTarget"] else "黑板记述的位置"
    elif node["_useTileAsTarget"]:
        if node["_useAbilityTileSelector"]: # 使用专门的能力选择器
            target_point = "选取的特定地块"
            if node["_useAbilityFromOther"]:
                ability_owner = anne_dictionary("target",node["_abilityOwner"])
                features.append(f"使用{ability_owner}的{node['_abilityName']}能力选取目的地块")
            else:
                features.append(f"使用来源的{node['_abilityName']}能力选取目的地块")
        elif node["_useTargetRootTile"]: # 使用目标所在地块中心
            target_point = target_name + "所在地块的中心"
    # 使用缓存攻击力
    if node["_cacheAtkToActions"]:
        features.append("使用缓存攻击力")
    # 使用Buff来源作为弹道的来源
    if node["_useSourceAsProjectileSource"]:
        features.append("使用事件来源作为弹道来源")
    else:
        features.append("使用Buff来源作为弹道来源")
    # 从目标出发
    if node["_useTargetAsStartPoint"]:
        start_point = target_name + "的位置"
    
    #特征
    if len(features) > 0:
        result["description"] = "；".join(features)
    result["main"] = f"从{start_point}，向{target_name}，发射{projectile}弹道"
    # 弹道事件
    if len(node["_actions"]) > 0:
        result["main"] += f"；当{projectile_event}，执行："
        result["sub_nodes"] = node["_actions"]
    return result

# 结束所有目标的弹道
def node_FinishManagedProjectiles(node):
    target_name = anne_dictionary("target",node["_targetType"])
    return {
        "main" : f"结束所有{target_name}发出的弹道"
    }