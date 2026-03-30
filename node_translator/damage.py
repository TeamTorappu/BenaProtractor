#----------------------------------------
# 伤害类Node
#----------------------------------------
from .analyzer import anne_dictionary, analyze_damage, analyze_target_options, to_percent
    
# 造成伤害
def node_AdvancedApplyDamage(node):
    # 未解析参数：_modifierKey _emitSourceOnCalculateDamage
    source_name = anne_dictionary("target",node["_sourceType"])
    target_name = anne_dictionary("target",node["_targetType"])
    damage_name = analyze_damage(node) # 直接把整个node传参进去
    default_atk_scale = to_percent(node["_defaultAtkScale"])
    return {
        "main" : f"让{source_name}对{target_name}造成{str(default_atk_scale)}{damage_name}",
        "description" : f"会读取黑板中的{node['_atkScaleVar']}作为攻击力倍率使用"
    }

# 造成无来源伤害
def node_NoSourceDamage(node):
    damage_name = analyze_damage(node,"无来源的") # 直接把整个node传参进去
    return {"main" : f"对持有者造成{node['_damageKey']}点{damage_name}"}

# 造成固定值伤害
def node_FixedValueDamage(node):
    # 未解析参数：_devideDamageFromAbilityCnt
    source_name = anne_dictionary("target",node["_damageSourceType"])
    target_name = anne_dictionary("target",node["_damageTargetType"])
    damage_name = analyze_damage(node,"预计算") # 直接把整个node传参进去
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
    if node["_modifierKey"]:
        features.append(f"带有\"{node['_modifierKey']}\"标记")
    
    if len(features) > 0:
        result["description"] = "；".join(features)
    if node["_noSourceDamage"]:
        result["main"] = f"对{target_name}造成damage点{damage_name}"
    else:
        result["main"] = f"令{source_name}对{target_name}造成damage点的{damage_name}"
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

# 造成群体伤害
#def node_AOEDamage(node):
#    return analyze_target_options(node["_targetOptions"])
