#----------------------------------------
# 解析职业或职业掩码
#----------------------------------------
from dictionary import enum_dictionary

# 职业筛选的处理
# 返回职业的字符串。说明筛选的职业以及“干员”和“召唤物”这样的称呼
def analyze_profession(profession_mask,condition_like=False):
    # 职业掩码分析
    professions = []
    has_trap = False
    has_token = False
    if isinstance(profession_mask,float) or isinstance(profession_mask,int) or profession_mask.isdigit(): # 二进制掩码
        int_mask = int(profession_mask)
        if int_mask & 1: # 近卫
            professions.append("WARRIOR")
        if int_mask & 2: # 狙击
            professions.append("SNIPER")
        if int_mask & 4: # 重装
            professions.append("TANK")
        if int_mask & 8: # 医疗
            professions.append("MEDIC")
        if int_mask & 16: # 辅助
            professions.append("SUPPORT")
        if int_mask & 32: # 术师
            professions.append("CASTER")
        if int_mask & 64: # 特种
            professions.append("SPECIAL")
        if int_mask & 128: # 召唤物
            professions.append("TOKEN")
            has_token = True
        if int_mask & 256: # 装置
            professions.append("TRAP")
            has_trap = True
        if int_mask & 512: # 先锋
            professions.append("PIONEER")
    else: # 被解析成字符串的掩码
        str_mask = str(profession_mask).upper()
        if "WARRIOR" in str_mask: # 近卫
            professions.append("WARRIOR")
        if "SNIPER" in str_mask: # 狙击
            professions.append("SNIPER")
        if "TANK" in str_mask: # 重装
            professions.append("TANK")
        if "MEDIC" in str_mask: # 医疗
            professions.append("MEDIC")
        if "SUPPORT" in str_mask: # 辅助
            professions.append("SUPPORT")
        if "CASTER" in str_mask: # 术师
            professions.append("CASTER")
        if "SPECIAL" in str_mask: # 特种
            professions.append("SPECIAL")
        if "TOKEN" in str_mask: # 召唤物
            professions.append("TOKEN")
            has_token = True
        if "TRAP" in str_mask: # 装置
            professions.append("TRAP")
            has_trap = True
        if "PIONEER" in str_mask: # 先锋
            professions.append("PIONEER")
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
    if len(professions) == 0:
        return "\"没有人\""
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