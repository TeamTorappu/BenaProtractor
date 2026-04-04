#----------------------------------------
# 卫戍协议的Node
#----------------------------------------
from .analyzer import anne_dictionary

# 检查难度
def node_AutoChessCheckDifficulty(node):
    if node["_difficultyMode"] == "TRAINING":
        return {
            "main" : "检查当前卫戍协议的关卡难度",
            "true" : "若当前为入门协议（教学模式）",
            "false" : "若当前不为入门协议（教学模式）"
        }
    elif node["_difficultyMode"] == "FUNNY":
        return {
            "main" : "检查当前卫戍协议的关卡难度",
            "true" : "若当前为标准模拟（简单难度）",
            "false" : "若当前为标准模拟（简单难度）"
        }
    elif node["_difficultyMode"] == "NORMAL":
        return {
            "main" : "检查当前卫戍协议的关卡难度",
            "true" : "若当前为险境模拟/绝境模拟/终极模拟（普通/困难/极限难度）",
            "false" : "若当前不为险境模拟/绝境模拟/终极模拟（普通/困难/极限难度）"
        }

# 在黑板记录盟约生效人数
def node_AutoChessAssignBondCharCntToBB(node):
    # 未解析参数：_target、_filterAllSides
    bond_id = anne_dictionary("bond_id",node["_bondId"])
    if node["_filterCount"]: # 判断模式
        compare = anne_dictionary("compare",node["_condType"])
        compare_not = anne_dictionary("compare_not",node["_condType"])
        return {
            "main" : f"将{bond_id}盟约生效人数记录至黑板{node['_keyToStoreCnt']}，并判断人数",
            "true" : f"若生效人数 {compare} {node['_keyToCompare']}",
            "false" : f"若生效人数 {compare_not} {node['_keyToCompare']}"
        }
    else:
        return {
            "main" : f"将{bond_id}盟约生效人数记录至黑板{node['_keyToStoreCnt']}。"
        }

# 在黑板记录盟约生效层数
def node_AutoChessAssignBondStackCntToBB(node):
    # 未解析参数：_target、_assignAllPlayerIndex
    bond_id = "???"
    if node["_assignCurrentMaxBond"]:
        bond_id = "最高层数盟约"
    elif node["_bondId"] != None and node["_bondId"] not in ["","none"]:
        bond_id = anne_dictionary("bond_id",node["_bondId"])+"盟约"
        if node["_bondBlackboardKey"] != None and node["_bondBlackboardKey"] not in ["","none"]: # 没有人类了
            result["description"] =f"会读取黑板上的{node['_bondBlackboardKey']}，以黑板指定的盟约为准"
    elif node["_bondBlackboardKey"] != None and node["_bondBlackboardKey"] not in ["","none"]: # 没有人类了
        bond_id = f"黑板{node['_bondBlackboardKey']}记录的盟约"
        
    
    result = {
        "main" : f"读取{bond_id}的叠加层数，并记录至黑板{node['_keyToStoreCnt']}"
    }
    if node["_checkDiffWithOldStoreCnt"]: # 写作差异，读作”更大“
        result["main"] += "，随后检查层数"
        result["true"] = f"若层数大于之前记录的值（或者之前未记录）"
        result["false"] = f"若层数小于等于之前记录的值"
    return result

# 在黑板记录装备数量
def node_AutochessAssignEquipCntToBlackboard(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_onlyGoldenEquip"]:
        return {
            "main" : f"读取{target_name}携带的已进阶装备数量，并记录至黑板{node['_blackboardKey']}",
            "description" : "此处所指的装备为卫戍协议的装备"
        }
    else:
        return {
            "main" : f"读取{target_name}携带的装备数量，并记录至黑板{node['_blackboardKey']}",
            "description" : "此处所指的装备为卫戍协议的装备"
        }

# 在黑板记录同名/精锐人数
def node_AutoChessAssignChessCntToBB(node):
    bb_key = node["_assignKey"]
    if node["_assignGoldenChess"]: # 罗素队的检查
        return {"main" : f"统计在场精锐单位，将数量记录至黑板{bb_key}"}
    elif node["_assignSameId"]: # 夕队的检查同名单位
        target_name = anne_dictionary("target",node["_targetType"])
        return {"main" : f"统计在场与{target_name}同名的单位（包括其自身），将数量记录至黑板{bb_key}"}
    else: # 记录0
        return {"main" : f"尝试统计在场同名/精锐单位数，但未给定检查条件，因此设 {bb_key} = 0"}
        

# 检查角色是否已进阶
def node_AutoChessFilterChess(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_filterGolden"]:
        return {
            "main" : f"检查{target_name}进阶状态",
            "true" : f"若{target_name}已进阶",
            "false" : f"若{target_name}还未进阶",
        }
    else:
        return {
            "main" : f"检查{target_name}进阶状态",
            "true" : f"若{target_name}还未进阶",
            "false" : f"若{target_name}已进阶",
        }

# 检查角色/范围内角色是否属于XX盟约
def node_AutoChessFilterCharacterBondIds(node):
    bond_ids = [anne_dictionary("bond_id",bond) for bond in node["_bondIds"]]
    bond_filter = ""
    
    if len(bond_ids) > 1:
        bond_filter = "同时隶属于"+"、".join(bond_ids)+"盟约"
    elif len(bond_ids) == 1:
        bond_filter = f"隶属{bond_ids[0]}盟约"
    else: # 0个，你在检查什么？
        return {
            "main" : "检查盟约，但未配置盟约条件",
            "true" : "始终通过",
            "false" : "始终不通过"
        }
    #考虑调和盟约
    if node["_considerManiShip"]:
        for bond in node["_bondIds"]:
            if anne_dictionary("bond_can_mani",bond) == "true": #字典里有就行
                bond_filter += "/隶属调和盟约"
                break
    # 处理对象
    target_name = anne_dictionary("target",node["_target"])
    if node["_checkTargetInRangeId"]: # 检查目标范围内是否存在符合盟约单位
        return {
            "main" : f"检查{target_name}的{node['_checkTargetInRangeId']}范围内所有角色的盟约",
            "true" : f"若任一角色{bond_filter}",
            "false" : f"若所有角色均不{bond_filter}"
        }
    else: # 检查目标盟约
        return {
            "main" : f"检查{target_name}的盟约",
            "true" : f"若其{bond_filter}",
            "false" : f"若其不{bond_filter}"
        }

# 检查目标的InstID，或者检查黑板里是否有目标的UID
def node_AutochessCheckTarget(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_checkCardUidInBlackboard"]:
        return {
            "main" : f"检查本Buff的黑板上是否记录有{target_name}的UID",
            "description" : "通常是以AssignCardUIDToBlackBoard，格式为{\"UID\" : 1.0}的格式记录",
            "true" : f"若黑板中存在{target_name}的UID",
            "false" : f"若黑板中不存在{target_name}的UID"
        }
    elif node["_checkTargetIsBlackboardInstID"]: # 这个我也没看懂
        return {
            "main" : f"检查{target_name}的InstID是否为黑板中记载的InsId",
            "true" : f"若其InstID正确",
            "false" : f"若其不InstID不正确"
        }
    else:
        return {
            "main" : f"检查{target_name}，但未配置条件",
            "true" : f"始终通过",
            "false" : f"始终不通过"
        }

# 触发核心盟约能力
def node_AutoChessTriggerGarrisonAbility(node):
    target_name = anne_dictionary("target",node["_target"])
    return {"main" : f"触发{target_name}的核心盟约能力（不是盟约特质）"}