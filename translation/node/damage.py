#----------------------------------------
# 伤害类Node
#----------------------------------------
from .analyzer import anne_dictionary, analyze_damage, analyze_target_options, to_percent

# 造成无来源伤害
def node_NoSourceDamage(node):
    damage_name = analyze_damage(node,"无来源的") # 直接把整个node传参进去
    return {"main" : "对持有者造成X点"+damage_name}
    
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

# 造成群体伤害
#def node_AOEDamage(node):
#    return analyze_target_options(node["_targetOptions"])
