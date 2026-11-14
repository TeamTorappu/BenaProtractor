#----------------------------------------
# 解析伤害
#----------------------------------------
from dictionary import enum_dictionary

# 解析伤害类的详细信息
# 返回字符串
def analyze_damage(damage_data,prefix="",suffix=""):
    features = []
    # 伤害类型
    damage_type = damage_data["_damageType"] if "_damageType" in damage_data else "NONE"
    damage_type_name = enum_dictionary("damage_type",damage_type)
    # 攻击类型
    attack_type = "NONE"
    if "_attackType" in damage_data:
        attack_type = damage_data["_attackType"]
    attack_type_name = enum_dictionary("attack_type",attack_type)
    # 无来源处理
    if "_onlyUseSourceOnCalculateDamage" in damage_data and damage_data["_onlyUseSourceOnCalculateDamage"]:
        features.append("计算后改为无来源")
    elif "_noSource" in damage_data and damage_data["_noSource"]:
        prefix += "无来源的"
    elif  "_noSourceDamage" in damage_data and damage_data["_noSourceDamage"]:
        prefix += "无来源的"
    elif "_isNoSourceDamage" in damage_data and damage_data["_isNoSourceDamage"]:
        prefix += "无来源的"
    # 特征处理
    if "_ignoreForSp" in damage_data and damage_data["_ignoreForSp"]:
        features.append("不触发受击回复")
    if "_forceUseProjectileCachedAtk" in damage_data and damage_data["_forceUseProjectileCachedAtk"]:
        features.append("强制使用弹道的缓存攻击力")
    elif "_getCachedAtkFromBlackboard" in damage_data and damage_data["_getCachedAtkFromBlackboard"]:
        if "_cachedAtkKey" in damage_data:
            features.append(f"使用黑板中({damage_data['_cachedAtkKey']})作为缓存攻击力")
    # 伤害类型覆盖
    if "_damageTypeKey" in damage_data and damage_data["_damageTypeKey"] != None and damage_data["_damageTypeKey"] != "":
        damage_type_name = f"优先使用黑板 [{damage_data['_damageTypeKey']}] 所记述的伤害类型"
    # 各种SharedFlags处理（两种写法都有，因此两种写法都判断一遍）
    if "_skipModifierEvent" in damage_data and damage_data["_skipModifierEvent"]:
        if "_considerUnhurtable" in damage_data and damage_data["_considerUnhurtable"]:
            features.append("生命流失+强制生命流失")
        else:
            features.append("生命流失")
    if "_isEnvDamage" in damage_data and damage_data["_isEnvDamage"]:
        features.append("环境伤害")
    if "_isUndeadable" in damage_data and damage_data["_isUndeadable"]:
        features.append("不会致命")
    if "_instantKillLikeDamage" in damage_data and damage_data["_instantKillLikeDamage"]:
        features.append("类斩杀伤害")
    if "_isNotChangeableValue" in damage_data and damage_data["_isNotChangeableValue"]:
        features.append("无法增/减/免/重设")
    elif "_forceDisplayDamageNum" in damage_data and damage_data["_forceDisplayDamageNum"]:
        features.append("强制红字")
    #if "_damageWithoutModify" in damage_data and damage_data["_damageWithoutModify"]: #似乎没有任何用途
    #    features.append("damageWithoutModify")
    if "_setSharedFlag" in damage_data and damage_data["_setSharedFlag"]:
        if "_sharedFlagIndex" in damage_data:
            shared_flag_name = enum_dictionary("sharedflag",damage_data["_sharedFlagIndex"])
            if shared_flag_name not in features:
                features.append(shared_flag_name)
    # 疑似是火陈的小巧思，限定伤害类型的无视闪避
    if "_ignoreMissFlag" in damage_data and damage_data["_ignoreMissFlag"] != "NONE":
        features.append("无视"+enum_dictionary("damage_type",damage_data["_ignoreMissFlag"])+"闪避")
    # 乘以黑板值
    #if "_multiplierByKey" in damage_data and damage_data["_multiplierByKey"]:
    #    if "_multiplierKey" in damage_data and damage_data["_multiplierKey"]:
    #        features.append("乘以黑板值"+damage_data["_multiplierKey"])
    # 伤害标签
    if "_modifierKey" in damage_data and damage_data["_modifierKey"] != "":
        suffix = suffix + f"（具有 {damage_data['_modifierKey']} 标记）"
    # 无视闪避/格挡那些的掩码，不过yj只用几个特定掩码，所以没必要做掩码解析
    if "_ignoreCancelReasonMask" in damage_data and damage_data["_ignoreCancelReasonMask"] != "NONE":
        if damage_data["_ignoreCancelReasonMask"] == "MISS":
            features.append("无视闪避")
        elif damage_data["_ignoreCancelReasonMask"] == "BLOCK":
            features.append("无视格挡")
        elif damage_data["_ignoreCancelReasonMask"] == "HIT_FAILED":
            features.append("不受命中率判定影响")
        else: # 不行的话全展示吧
            reason_mask = damage_data["_ignoreCancelReasonMask"].split(", ")
            reasons = []
            for reason in reason_mask:
                reasons.append(enum_dictionary("cancel_reason",reason))
            features.append("不受"+"/".join(reasons)+"影响")
    if len(features) > 0:
        suffix += "（"+"；".join(features)+"）"
    return prefix + damage_type_name + attack_type_name + "伤害"+suffix