
import json

ENUMS = None

# 加载常量表
def load_enums():
    global ENUMS
    with open("./enums.json","r") as _f:
        ENUMS = json.load(_f)

# 获取常量值对照的常量名
def ask_enum_key(base,index):
    for _key, _var in ENUMS[base].items():
        if _var == index:
            return _key
    return index

BUFF_BOOL_KEYS = [
    "loadFromDB","isDurableBuff","isDamageMissable",
    "isSilenceable","isStunnable","isFreezable","isLevitatable","isGroundBoundable",
    "disableOverride","refreshRemainingTimeWhenStackMax","clearAllStackCntWhenTimeUp",
    "independentCharacterSource","overrideOnEventPriority","takeSnapshotWhenExtend","waitFirstTriggerInterval",
    "stripBlackboardParamsWithBuffKey","enableInitDirectionFromSource"
]
BUFF_ENUM_KEYS = {
    "statusResistable" : "BuffData.StatusResistable",
    "overrideType" : "BuffData.OverrideType",
    "onEventPriority" : "BuffData.OnEventPriority",
    "lifeTimeType" : "LifeType",
    "triggerLifeType" : "LifeType"
}

# 解析并重构Buff
def analyze_buff(buff_data: dict):
    if ENUMS == None:
        load_enums()
    # 布尔值转化
    for key in BUFF_BOOL_KEYS:
        buff_data[key] = (buff_data[key] == 1)
    # 常量值转化
    for key, enum in BUFF_ENUM_KEYS.items():
        buff_data[key] = ask_enum_key(enum,buff_data[key])
    # 异常效果
    if len(buff_data["attributes"]["abnormalFlags"]) > 0:
        new_flags = []
        for flag in buff_data["attributes"]["abnormalFlags"]:
            new_flags.append(ask_enum_key("AbnormalFlag",flag))
        buff_data["attributes"]["abnormalFlags"] = new_flags
    # 异常效果免疫
    if len(buff_data["attributes"]["abnormalImmunes"]) > 0:
        new_flags = []
        for flag in buff_data["attributes"]["abnormalImmunes"]:
            new_flags.append(ask_enum_key("AbnormalFlag",flag))
        buff_data["attributes"]["abnormalImmunes"] = new_flags
    # 异常效果反制
    if len(buff_data["attributes"]["abnormalAntis"]) > 0:
        new_flags = []
        for flag in buff_data["attributes"]["abnormalAntis"]:
            new_flags.append(ask_enum_key("AbnormalFlag",flag))
        buff_data["attributes"]["abnormalAntis"] = new_flags
    # 异常效果组合
    if len(buff_data["attributes"]["abnormalCombos"]) > 0:
        new_combos = []
        for combo in buff_data["attributes"]["abnormalCombos"]:
            new_combos.append(ask_enum_key("AbnormalCombo",combo))
        buff_data["attributes"]["abnormalCombos"] = new_combos
    # 异常效果组合免疫
    if len(buff_data["attributes"]["abnormalComboImmunes"]) > 0:
        new_combos = []
        for combo in buff_data["attributes"]["abnormalComboImmunes"]:
            new_combos.append(ask_enum_key("AbnormalCombo",combo))
        buff_data["attributes"]["abnormalComboImmunes"] = new_combos
    # 属性值加成
    if len(buff_data["attributes"]["attributeModifiers"]) > 0:
        new_attributes = []
        for attribute in buff_data["attributes"]["attributeModifiers"]:
            attribute["attributeType"] = ask_enum_key("AttributeType",attribute["attributeType"])
            attribute["formulaItem"] = ask_enum_key("FormulaItem",attribute["formulaItem"])
            attribute["loadFromBlackboard"] = (attribute["loadFromBlackboard"] == 1)
            attribute["fetchBaseValueFromSourceEntity"] = (attribute["fetchBaseValueFromSourceEntity"] == 1)
        #buff_data["attributeModifiers"] = new_attributes # 对字典进行的操作，理应不需要赋值
    return buff_data

DECK_BUFF_BOOL_KEYS = [
    "affectInHand","affectOutOfHand","wontSpawnWhenRallyPointSwitch","showToastWhenAffect","ignoreSpecialBuild"
]
DECK_BUFF_ENUM_KEYS = {
    "cardEffectType" : "Deck.Card.CardEffectType",
    "lifeType" : "Deck.Card.DeckBuffLifeType"
}

# 解析并重构DeckBuff
def analyze_deck_buff(deck_buff_data: dict,script: str):
    if ENUMS == None:
        load_enums()
    # 布尔值转化
    for key in DECK_BUFF_BOOL_KEYS:
        deck_buff_data[key] = (deck_buff_data[key] == 1)
    # 常量值转化
    for key, enum in DECK_BUFF_ENUM_KEYS.items():
        deck_buff_data[key] = ask_enum_key(enum,deck_buff_data[key])
    deck_buff_data["buff"] = analyze_buff(deck_buff_data["buff"])
    return deck_buff_data


OPTION_BOOL_KEYS = [
    "enableAdvancedOptions",
    "ignoreTargetFree","ignoreAllyTargetFree","ignoreHealFree","ignoreTargetSide","ignoreMotionMode",
    "excludeSomeAbnormalFlags","containSomeAbnormalFlags","checkUnitType","onlyIgnoreSomeOfTargetFreeCase"
]
OPTION_ENUM_KEYS = {
    "targetSide" : "SideType",
    "targetMotion" : "MotionMask",
    #"targetCategory" : "EntityCategory",
    "excludeAbnormalFlag" : "AbnormalFlag",
    "containAbnormalFlag" : "AbnormalFlag",
    "purposeMask" : "ActionPurposeMask",
    #"professionMask" : "ProfessionCategory",
    "unitTypeMask" : "UnitTypeMask",
    "abnormalFlag" : "AbnormalFlag",
    "abnormalCombo" : "AbnormalCombo"
}
# 解析并重构TargetOptions
def analyze_options(options_data: dict):
    if ENUMS == None:
        load_enums()
    # 布尔值转化
    for key in OPTION_BOOL_KEYS:
        options_data[key] = (options_data[key] == 1)
    # 常量值转化
    for key, enum in OPTION_ENUM_KEYS.items():
        options_data[key] = ask_enum_key(enum,options_data[key])
    # 职业掩码处理
    if options_data["professionMask"] == 0:
        options_data["professionMask"] = "NONE"
    else:
        professions = []
        for _key, _mask in ENUMS["ProfessionCategory"].items():
            if options_data["professionMask"] & _mask:
                professions.append(_key)
        options_data["professionMask"] = ", ".join(professions)
    # 实体类型处理
    if options_data["targetCategory"] == 0:
        options_data["targetCategory"] = "NONE"
    else:
        professions = []
        for _key, _mask in ENUMS["EntityCategory"].items():
            if options_data["targetCategory"] & _mask:
                professions.append(_key)
        options_data["targetCategory"] = ", ".join(professions)
    return options_data