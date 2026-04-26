#----------------------------------------
# 黑板类Node
#----------------------------------------
from .analyzer import anne_dictionary

# 记录黑板值
def node_AssignValueToBB(node):
    result = {
        "main" : f"设 [{node['_blackboardKey']}] = "
    }
    if node["_copyFromKey"] != None:
        result["main"] += "["+node['_copyFromKey']+"]"
        if node["_assignString"]:
            result["main"] += "（字符串格式）"
    elif node["_assignString"]:
        result["main"] += "\""+str(node['_value'])+"\""
    else:
        result["main"] += str(node['_value'])
    return result

# 将属性值记录到黑板中
def node_AssignAttributeToBB(node):
    target_name = anne_dictionary("target",node["_targetType"])
    attribute = anne_dictionary("attribute",node["_attributeType"])
    if node["_scaleVar"] != None and node["_scaleVar"] != "":
        return {"main" : f"取{target_name}的{attribute}，设 [{node['_blackboardKey']}] = {attribute} × [{node['_scaleVar']}]"}
    else:
        return {"main" : f"取{target_name}的{attribute}，设 [{node['_blackboardKey']}] = {attribute}"}

# 将召唤物的数量或最大数量记录到黑板中
def node_AssignTokenCardCntToBB(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_assignMaxCount"]:
        return {"main" : f"设 [{node['_countKey']}] = {target_name}的召唤物最大持有数"}
    else:
        return {"main" : f"设 [{node['_countKey']}] = {target_name}的召唤物当前持有数"}

# 将生命比例记录到黑板中
def node_AssignHpRatioToBB(node):
    target_name = anne_dictionary("target",node["_targetType"])
    return {"main" : f"设 [{node['_blackboardKey']}] = {target_name}的当前生命比例"}

# 三合一节点：记录伤害值、记录模拟的计算伤害值、记录伤害影响差值
def node_AssignDamageValueToBlackboard(node):
    owner_name = anne_dictionary("target",node["_owner"])
    if node["_assignRealDelta"]:
        return {"main" : "设 [damage] 为 本次伤害实际造成的生命值减少量（最低为0）"}
    elif node["_assignValueWithoutCalculate"]:
        return {"main" : f"设 [damage] 为 {owner_name}的攻击力 × [{node['_scaleKey']}]"}
    else:
        damage_type = anne_dictionary("damage_type",node["_damageType"])
        return {"main" : f"设 [damage] 为 本次{damage_type}伤害的值（类型不对则为0）"}

# 确保黑板默认值，防止出错
def node_EnsureBlackboardDefaultValue(node):
    results = []
    has_overrided = False
    if node["_defaultSettings"] != None:
        for setting in node["_defaultSettings"]:
            if setting["overrideIfExists"]: # 默认值里写覆写，也是神人操作了
                has_overrided = True;
                if setting["valStr"] != None and setting["valStr"] != "":
                    results.append({"main" : f"不论是否已定义，设 [{setting['key']}] = \"{setting['valStr']}\""})
                else:
                    results.append({"main" : f"不论是否已定义，设 [{setting['key']}] = {setting['val']}"})
            else:
                if setting["valStr"] != None and setting["valStr"] != "":
                    results.append({"main" : f"若 [{setting['key']}] 未定义，设 {setting['key']} = {setting['valStr']}"})
                else:
                    results.append({"main" : f"若 [{setting['key']}] 未定义，设 {setting['key']} = {setting['val']}"})
    if len(results) > 0:
        if has_overrided:
            return {
                "main" : "为确保黑板具有数据，批量设置以下数据（注意，部分设置会覆盖原有数据）：",
                "children" : results
            }
        else:
            return {
                "main" : "为确保黑板具有数据，批量设置以下数据：",
                "children" : results
            }
    return {"main" : "为黑板记录数据，但无事发生"}

# 从其他Buff的黑板中获取黑板值
def node_AssignBuffBlackboardFromOthers(node):
    target_name = anne_dictionary("target",node["_targetType"])
    buff_name = " <" + node["_buffKey"] + "> Buff"
    if node["_filterBuffSource"]:
        if node["_sourceType"]:
            buff_name = "由同一来源提供的" + buff_name
        else:
            buff_name = "由" + anne_dictionary("target",node["_sourceType"]) + "提供的" + buff_name
    return {
        "main" : f"尝试寻找{target_name}持有的首个{buff_name}，设本Buff的 [{node['_blackboardKey']}] = 该Buff的 [{node['_valueKey']}]"
    }

# 设置其他Buff的黑板值
def node_AssignBuffBlackboard(node):
    target_name = anne_dictionary("target",node["_targetType"])
    source_buff_name = "本Buff"
    target_buff_name = node["_buffKey"]
    target_bb = "[" + node["_blackboardKey"] + "]"
    if node["_valueKey"] != None and node["_valueKey"] != "":
        source_bb = "本黑板上的 [" + node["_valueKey"] + "]"
        if node["_buffKeyAssignFrom"] != None and node["_buffKeyAssignFrom"] != "":
            source_buff_name = node["_buffKeyAssignFrom"]
            target_bb = target_buff_name + " 的 [" + target_bb + "]"
            source_bb = node["_buffKeyAssignFrom"] + " 的 [" + node["_valueKey"] + "]"
            if node["_assignFirstBuff"]:
                return {"main" : f"尝试寻找{target_name}持有的首个 <{source_buff_name}> 与 <{target_buff_name}> Buff，设 {target_bb} = {source_bb}"}
            else:
                return {"main" : f"尝试寻找{target_name}持有的首个 <{source_buff_name}> Buff，设该单位的所有<{target_buff_name}>黑板上的 {target_bb} = {source_bb}"}      
    # 默认处理
    value = node["_defaultValue"]
    if node["_valueKey"] != None and node["_valueKey"] != "":
        value = f"[{node['_valueKey']}]（默认{value}）"
    if node["_assignFirstBuff"]:
        return {"main" : f"尝试寻找{target_name}持有的首个 <{target_buff_name}> Buff，设该Buff的 {target_bb} = {value}"}
    else:
        return {"main" : f"设{target_name}的所有 <{target_buff_name}> Buff黑板上的 {target_bb} = {value}"}

# 添加其他Buff的黑板值
def node_AddBuffBlackboard(node):
    target_name = anne_dictionary("target",node["_targetType"])
    target_buff_name = node["_buffKey"]
    target_bb = "[" + node["_blackboardKey"] + "]"
    addon = node["_addition"]
    if node["_additionKey"] != None and node["_additionKey"] != "":
        if node["_useCurBuffBBWhenDoAddition"]: # 用自己的黑板值
            addon = f"本Buff黑板上的 [{node['_additionKey']}]（默认{node['_addition']}"
        else:
            addon = f"该Buff黑板上的 [{node['_additionKey']}]（默认{node['_addition']}"
    formula = ""
    if node["_maxValueKey"] != None and node["_maxValueKey"] != "":
        if node["_isMinus"]:
            formula = f"{target_bb} = min({target_bb} - {addon},{node['_maxValueKey']})"
        else:
            formula = f"{target_bb} = min({target_bb} + {addon},{node['_maxValueKey']})"
    else:
        if node["_isMinus"]:
            formula = f"{target_bb} -= {addon}"
        else:
            formula = f"{target_bb} += {addon}"
    if node["_checkBuffSource"]:
        return {"main" : f"尝试寻找{target_name}持有的首个同来源的 <{target_buff_name}> Buff，设该Buff的 {formula}"}
    else:
        return {"main" : f"尝试寻找{target_name}持有的首个 <{target_buff_name}> Buff，设该Buff的 {formula}"}

# 记录末影黑板（同UID单位间互通）
def node_AddCharacterSharedBlackboard(node):
    target_name = anne_dictionary("target",node["_target"])
    target_value = None
    action = f"将 [{node['_blackboardKey']}] 设置为"
    # 获取目标值
    if node["_useValueKey"]:
        target_value = "本Buff黑板上 ["+node["_valueKey"] +"] 的值"
    elif node["_isStringBB"]:
        target_value = node["_valueStr"]
    else:
        if not node["_isOverwrite"]: # 如果类型为数值，且不启用覆写，改为加算数值
            action = f"令 {node['_blackboardKey']} 增加"
        target_value = node["_value"]
    return {
        "main" : f"在{target_name}的末影黑板上，{action} {target_value}",
        "style_closed" : True,
        "description" : "\"末影黑板\"为同一UID的干员实例间互通的数据"
    }

# 将一项基础数据记录到黑板中（计算过符文与直接加算后的数值）
def node_AssignAttributeRawDataIntoBlackboard(node):
    target_name = anne_dictionary("target",node["_targetType"])
    attribute = anne_dictionary("attribute",node["_attributeType"])
    return {
        "main" : f"将{target_name}的基础{attribute}记录至黑板 [{node['_blackBoardKey']}]",
        "style_closed" : True,
        "description" : "\"基础值\"为计算过符文、直接加算后的面板值"
    }

# 从末影黑板拉取数据（同UID单位间互通）
def node_AssignCharacterSharedBBToBlackboard(node):
    character_name = anne_dictionary("target",node["_character"])
    if node["_sourceBBKey"] != node["_targetBBKey"]:
        return {
            "main" : f"令本Buff黑板上的 [{node['_targetBBKey']}] = {character_name}的末影黑板上的 [{node['_sourceBBKey']}] 的值",
            "style_closed" : True,
            "description" : "\"末影黑板\"为同一UID的干员实例间互通的数据"
        }
    else:
        return {
            "main" : f"令本Buff黑板上的 [{node['_targetBBKey']}] = {character_name}的末影黑板上同名黑板的值",
            "style_closed" : True,
            "description" : "\"末影黑板\"为同一UID的干员实例间互通的数据"
        }

# 将UID记录到黑板上
# 有两种模式，一种是记录在特定黑板上，一种是把黑板当字典（本来就是），把UID作为Key记录进去占位。
def node_AssignCardUIDToBlackBoard(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_assignHostOrToken"]:
        target_name = target_name+"的召唤物/主人"
    if node["_assignAsKey"]: # 字典模式
        return {"main" : f"将{target_name}的UID作为黑板Key值，记录至本Buff的黑板中（相应的Value为1.0)"}
    # 字符串/数值模式
    if node["_assignAsString"]:
        return {"main" : f"将{target_name}的UID记录至本Buff的黑板 [{node['_blackBoardKey']}] 中（字符串格式）"}
    else:
        return {"main" : f"将{target_name}的UID记录至本Buff的黑板 [{node['_blackBoardKey']}] 中（整数格式）"}

# 将当前重生次数记录到黑板上
def node_AssignRespawnCntToBlackboard(node):
    target_name = anne_dictionary("target",node["_targetType"])
    return {"main" : f"将{target_name}目前已重生的次数记录至黑板 [{node['_blackboardKey']}] 中"}

# 将技能剩余冷却时间记录到黑板上
def node_AssignEnemySkillCoolDownToBB(node):
    owner_name = anne_dictionary("target",node["_ownerType"])
    skill_name = node["_skillName"] if node["_skillName"] != "" else "[skill_name]"
    if node["_checkSkillActive"]:
        return {
            "main" : f"获取{owner_name}当前开启中的名为 {skill_name} 技能的\"剩余冷却时间\"，记录至黑板 [{node['_outputKey']}]（单位为秒）",
            "description" : "非本模式的模式技能、使用次数达上限的技能均无法被识别；若找不到对应技能或技能未开启，视为本节点处理失败"
        }
    return {
        "main" : f"获取{owner_name}名为 {skill_name} 技能的\"剩余冷却时间\"，记录至黑板 [{node['_outputKey']}]（单位为秒）",
        "description" : "非本模式的模式技能、使用次数达上限的技能均无法被识别；若找不到对应技能，视为本节点处理失败"
    }

# 将当前阻挡到的单位数量记录到黑板上
def node_AssignCurrentBlockNumToBB(node):
    target_name = anne_dictionary("target",node["_targetType"])
    return {
        "main" : f"将{target_name}（角色类）当前阻挡的单位数量记录至黑板 [{node['_blackboardKey']}]"
    }

