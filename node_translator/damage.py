#----------------------------------------
# 伤害类Node
#----------------------------------------
from .analyzer import analyze_buff, anne_dictionary, analyze_damage, analyze_target_options, to_percent
    
# 造成伤害
def node_AdvancedApplyDamage(node):
    # 未解析参数：_emitSourceOnCalculateDamage
    source_name = anne_dictionary("target",node["_sourceType"])
    target_name = anne_dictionary("target",node["_targetType"])
    damage_name = analyze_damage(node) # 直接把整个node传参进去
    default_atk_scale = to_percent(node["_defaultAtkScale"])
    return {
        "main" : f"让{source_name}对{target_name}造成{str(default_atk_scale)}的{damage_name}",
        "description" : f"会读取黑板中的 [{node['_atkScaleVar']}] 覆盖此处的攻击力倍率"
    }

# 造成无来源伤害
def node_NoSourceDamage(node):
    damage_name = analyze_damage(node,"无来源的") # 直接把整个node传参进去
    return {"main" : f"对持有者造成 [{node['_damageKey']}] 点{damage_name}"}

# 造成固定值伤害
def node_FixedValueDamage(node):
    # 未解析参数：_devideDamageFromAbilityCnt
    source_name = anne_dictionary("target",node["_damageSourceType"])
    target_name = anne_dictionary("target",node["_damageTargetType"])
    damage_name = analyze_damage(node,"预计算") # 直接把整个node传参进去
    damage_key = node["_damageKey"]
    result = {}
    features = []
    multiplier = ""
    if node["_triggerOnCalculateDamage"]:
        features.append("会触发伤害计算时事件")
    if node["_multiplierByKey"]:
        multiplier = " × " + node["_multiplierKey"]
    # 记录至黑板
    if node["_assignFinalDamageToBB"]:
        features.append("将产生的生命值变化量记录至黑板")
    elif node["_assignRealDamageToBB"]: # 和上一个是平行的，不过开了前面那个这里这个会被覆盖掉...
        features.append("将计算后伤害记录至黑板")
    
    if len(features) > 0:
        result["description"] = "；".join(features)
    if node["_noSourceDamage"]:
        result["main"] = f"对{target_name}造成 [{damage_key}] 点{damage_name}"
    else:
        result["main"] = f"令{source_name}对{target_name}造成 [{damage_key}] 点的{damage_name}"
    return result

# 造成基于某种属性的伤害（主要由刻俄柏与泡泡使用）
def node_DamageViaAttr(node):
    source_name = anne_dictionary("target",node["_sourceType"])
    target_name = anne_dictionary("target",node["_targetType"])
    attribute = anne_dictionary("attribute",node["_attributeType"])+"属性"
    damage_name = analyze_damage(node) # 直接把整个node传参进去
    scale = "100%"
    multiplier = ""
    if node["_blackboardKey"] != None and node["_blackboardKey"] != "": # 属性倍率
        scale = node["_blackboardKey"]
    if node["_multiplierByKey"]:
        multiplier = " × " + node["_multiplierKey"]
    if not node["_getAttrFromTarget"]: #这个参数是反的，关了才FromTarget，开了就FromSource，神经病
        return {
            "main" : f"取{target_name}的 {attribute}{multiplier} 作为\"攻击力\"，令{source_name}对{target_name}依此造成{scale}倍率的{damage_name}"
        }
    else:
        return {
            "main" : f"取{source_name}的 {attribute}{multiplier} 作为\"攻击力\"，令{source_name}对{target_name}依此造成{scale}倍率的{damage_name}"
        }

# 根据记录生命值，制造一次伤害来匹配记录的生命值
def node_FetchHpToBlackboard(node):
    target_name = anne_dictionary("target",node["_targetType"])
    damage_type = anne_dictionary("damage_type",node["_damageType"])
    if node["_skipModifierEvent"]:
        if node["_damageType"] == "PURE":
            damage_type = "生命流失"
        else:
            damage_type += "流失"
    else:
        damage_type = damage_type + "普通伤害"
    hp_type = "生命比例（伤害值 = 当前比例 - 目标比例）" if node["_isHpRatio"] else "生命值（伤害值 = 当前生命值 - 目标生命值）"
    if node["_buffNameOfBlackboard"] != None and node["_buffNameOfBlackboard"] != "":
        return {
            "main" : f"对{target_name}造成一次{damage_type}，以此来匹配记录的{hp_type}",
            "description" : f"使用{target_name}的 {node['_buffNameOfBlackboard']} Buff黑板上的{node['_blackboardStr']}的值作为{hp_type}"
        }
    else:
        return {
            "main" : f"对{target_name}造成一次{damage_type}，以此来匹配记录黑板上（{node['_blackboardStr']}）记录的{hp_type}"
        }

# 根据当前生命值，制造一次伤害
def node_DamageViaCurHpRatio(node):
    target_name = anne_dictionary("target",node["_targetType"])
    damage_num = "造成 来源当前生命值 × [hp_ratio] "
    damage_name = analyze_damage(node,"预计算") # 直接把整个node传参进去
    features = []
    if node["_damageNoLessThanValueBasedOnSourceAtk"]:
        if node["_atkScaleKey"] != "":
            damage_num += f"或 来源攻击力 × [{node['_atkScaleKey']}] "
        else:
            damage_num += f"或 来源攻击力 × 100% "
        features.append("伤害在两者间取高")
    if node["_ceilingDamageToInt"]:
        features.append("伤害量向上取整")
    if node["_triggerOnCalculateDamage"]:
        features.append("会触发伤害计算时事件")
    result = {
        "main" : f"对{target_name}造成{damage_num}的{damage_name}"
    }
    if len(features) > 0:
        result["description"] = "；".join(features)
    return result


# 造成群体伤害
def node_AOEDamage(node):
    # 未解析参数：_createEffect、_hitEffectKey、_hitEffectUseSourceFaceTo
    source_name = anne_dictionary("target",node["_sourceType"])
    target_name = anne_dictionary("target",node["_targetType"])
    damage_name = analyze_damage(node,"预计算") # 直接把整个node传参进去
    damage = f" [{node['_damageKey']}] × [{node['_damageScale']}] " if node["_useDamageFromBB"] else f" {source_name}攻击力 × [{node['_damageScale']}] "
    features = []
    buffs = []
    selector = ""
    # 处理“用什么选择目标”
    if node["_useRadius"]:
        target_options = analyze_target_options(node["_targetOptions"])
        selector = f"对位于{target_name}半径{node['_radius']}内的{target_options['main']}"
        features.append(target_options["description"])
        features.append("中点判定")
    elif node["_useAbilitySelector"]:
        if node["_abilityName"] != None:
            selector = f"使用来源的{node['_abilityName']}选择器，对选中的目标"
        else:
            selector = f"使用来源的默认选择器，对选中的目标"
    else: # 使用网格范围
        target_options = analyze_target_options(node["_targetOptions"])
        selector = f"对位于{target_name}周边特定范围({node['_rangeId']})的{target_options['main']}"
        if "description" in target_options:
            features.append(target_options["description"])
        features.append("中点判定")
    result = {
        "main" : selector + "分别造成" + damage + damage_name
    }
    # 额外特性
    if node["_maxTargetCountKey"]:
        features.append(f"最大目标数取自[{node['_maxTargetCountKey']}]")
    if node["_excludeTarget"]:
        features.append(f"排除{target_name}")
    if node["_checkTargetAlive"]:
        features.append(f"生效前检查{target_name}是否存活")
    if node["_filterType"] not in ["ALL",""] and (node["_useRadius"] or not node["_useAbilitySelector"]):
        features.append(f"使用 {node['_filterType']} 过滤器排序")
    if len(features) > 0:
        result["description"] = "；".join(features)
    # 附加buff
    if node["_buffs"] != None and len(node["_buffs"]) > 0:
        if len(node["_buffs"]) > 1:
            result["children"] = [{"main" : "...并对每个目标创建以下这些Buff："}]
            for buff in node["_buffs"]:
                result["children"].append(analyze_buff(buff))
        else:
            buff = analyze_buff(node["_buffs"][0])
            buff["main"] = "...并对每个目标创建Buff："+buff["main"]
            result["children"] = [buff]
    # 返回
    return result

