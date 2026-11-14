#----------------------------------------
# 解析职业或职业掩码
#----------------------------------------
from dictionary import enum_dictionary

# 职业筛选的处理
# 返回职业的字符串。说明筛选的职业以及“干员”和“召唤物”这样的称呼
def analyze_profession(profession_mask,condition_like=False):
    profession_mask = profession_mask.upper()
    # 职业掩码分析
    professions = []
    has_trap = False
    has_token = False
    if "PIONEER" in profession_mask:
        professions.append("PIONEER")
    if "WARRIOR" in profession_mask:
        professions.append("WARRIOR")
    if "TANK" in profession_mask:
        professions.append("TANK")
    if "SNIPER" in profession_mask:
        professions.append("SNIPER")
    if "CASTER" in profession_mask:
        professions.append("CASTER")
    if "SUPPORT" in profession_mask:
        professions.append("SUPPORT")
    if "MEDIC" in profession_mask:
        professions.append("MEDIC")
    if "SPECIAL" in profession_mask:
        professions.append("SPECIAL")
    if "TRAP" in profession_mask:
        professions.append("TRAP")
        has_trap = True
    if "TOKEN" in profession_mask:
        professions.append("TOKEN")
        has_token = True
    # 全职业，相当于没判
    if len(professions) >= 10:
        return "" if condition_like else "干员、召唤物、装置"
    # 如果大于等于8职业的话有可能是用于筛所有干员的，进行缩减处理
    if len(professions) == 9 and has_trap and not has_token:
        return "非召唤物职业的" if condition_like else "干员、装置"
    if len(professions) == 9 and has_token and not has_trap:
        return "非装置职业的" if condition_like else "干员、召唤物"
    if len(professions) == 8 and not has_token and not has_trap:
        return "干员"
    if len(professions) == 1:
        if has_token:
            return "召唤物"
        if has_trap:
            return "装置"
        return enum_dictionary("profession",professions[0])+"干员"
    # 保留处理
    if condition_like:
        if len(professions) > 0:
            return "职业为" + "/".join([enum_dictionary("profession",profession) for profession in professions]) + "的"
    op_professions = []
    objects = []
    for profession in professions:
        if profession in ["TOKEN","TRAP"]:
            objects.append(enum_dictionary("profession",profession))
        else:
            op_professions.append(enum_dictionary("profession",profession))
    return "、".join(["/".join(op_professions)+"干员"] + objects)

# 子职业筛选的处理
# 返回子职业的字符串。说明筛选的子职业以及“干员”
def analyze_sub_profession(sub_profession_mask):
    sub_profession_mask = sub_profession_mask.lower()
    masked_list = [sub_profession_mask]
    if "," in sub_profession_mask:
        masked_list = sub_profession_mask.split(",")
    elif "|" in sub_profession_mask:
        masked_list = sub_profession_mask.split("|")
    sub_professions = []
    for masked in masked_list:
        sub_professions.append(enum_dictionary("sub_profession",masked))
    return "/".join(sub_professions)+"干员"