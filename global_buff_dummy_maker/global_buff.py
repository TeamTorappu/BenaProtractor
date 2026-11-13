import os
import json
from analyzer import analyze_buff, analyze_deck_buff, analyze_options, ask_enum_key
from loader import load_file

KEY_PREFIX = "dyn/battle/prefabs/[uc]globalbuffs/"
KEY_SUFFIX = ".prefab"
PREFAB_LIST_PATH = "./input/AssetBundle/battle_prefabs_[uc]globalbuffs.ab.txt"
PREFAB_LIST = {}
GBUFF_DIRECTORY = "./input/MonoBehaviour/"
GBUFF = {}
SAVE_PATH = "../table_dummies"

# 全局Buff类
#class Gbuff:
    

# 读取prefab对照表
if __name__ == "__main__":
    key_prefix_length = len(KEY_PREFIX)
    key_suffix_length = len(KEY_SUFFIX)
    prefabs = load_file(PREFAB_LIST_PATH)["m_Container"]
    for prefab in prefabs:
        name = prefab["first"][key_prefix_length:-key_suffix_length]
        path_id = prefab["second"]["asset"]["m_PathID"]
        #print(str(path_id)+" : "+name)
        PREFAB_LIST[str(path_id)] = name
    # 获取所有GlobalBuff
    for root, dirs, files in os.walk(GBUFF_DIRECTORY):
        for file in files:
            file_data = load_file(os.path.join(root, file))
            # 数据净化
            script = os.path.splitext(file)[0].split(" ",1)[0]
            file_data["m_Script"] = script
            del file_data["m_Enabled"]
            del file_data["m_Name"]
            gbuff_id = str(file_data["m_GameObject"]["m_PathID"])
            del file_data["m_GameObject"]
            # 解析Buff
            for buff in file_data["_buffs"]:
                analyze_buff(buff)
            # 解析DeckBuff
            for deck_buff in file_data["_deckBuffs"]:
                analyze_deck_buff(deck_buff,file_data["m_Script"])
            # 解析额外Buff
            if "_extraBuff" in file_data:
                analyze_buff(file_data["_extraBuff"])
            # 解析条件
            if "_options" in file_data:
                analyze_options(file_data["_options"])
            # 解析sourceType
            file_data["_sourceType"] = ask_enum_key("SideTypeIndex",file_data["_sourceType"])
            
            # 根据类型，解析额外参数
            if script == "SharedRandomTileGlobalBuff" or script == "RemovableSharedRandomTileGlobalBuff":
                file_data["_tickForEnemy"] = (file_data["_tickForEnemy"] == 1)
                file_data["_excludeBorderTiles"] = (file_data["_excludeBorderTiles"] == 1)
                file_data["_weightType"] = ask_enum_key("RandomTileGlobalBuff.RandomWeightType",file_data["_weightType"])
                file_data["_buildableType"] = ask_enum_key("BuildableType",file_data["_buildableType"])
            elif script == "RandomTileWithExtraRangeGlobalBuff":
                file_data["_extraRangeID"] = "x_4" # 固定的
                file_data["_excludeBorderTiles"] = (file_data["_excludeBorderTiles"] == 1)
                file_data["_weightType"] = ask_enum_key("RandomTileGlobalBuff.RandomWeightType",file_data["_weightType"])
                file_data["_buildableType"] = ask_enum_key("BuildableType",file_data["_buildableType"])
            elif script == "CertainTileWithExtraRangeGlobalBuff":
                file_data["_extraRangeID"] = "x_4" # 固定的
                file_data["_excludeBorderTiles"] = (file_data["_excludeBorderTiles"] == 1)
            elif script == "RandomTileGlobalBuff" or script == "RandomTileWithCertainKeyGlobalBuff":
                file_data["_excludeBorderTiles"] = (file_data["_excludeBorderTiles"] == 1)
                file_data["_weightType"] = ask_enum_key("RandomTileGlobalBuff.RandomWeightType",file_data["_weightType"])
                file_data["_buildableType"] = ask_enum_key("BuildableType",file_data["_buildableType"])
            elif script in ["AbstractBindingTileGlobalBuff","CertainTileAndChoseColTilesGlobalBuff","CertainTileGlobalBuff"]:
                file_data["_excludeBorderTiles"] = (file_data["_excludeBorderTiles"] == 1)
            elif script == "Act7FunSpecialConditionGlobalBuff":
                file_data["_checkWin"] = (file_data["_checkWin"] == 1)
                file_data["_checkPerfectWin"] = (file_data["_checkPerfectWin"] == 1)
                file_data["_checkRestCost"] = (file_data["_checkRestCost"] == 1)
            elif script == "AutoChessTimeOutGlobalBuff":
                file_data["_assginOnTimeNotReach"] = (file_data["_assginOnTimeNotReach"] == 1)
                file_data["_useStateEndTime"] = (file_data["_useStateEndTime"] == 1)
            # 设置值
            gbuff_key = PREFAB_LIST[gbuff_id]
            GBUFF[gbuff_key] = file_data
    
    # 保存
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
    with open(SAVE_PATH+"/global_buff_dummy.json","w",encoding='utf-8') as _f:
        _f.write(json.dumps(GBUFF, indent=4, ensure_ascii=False))
    print("global_buff_dummy.json 制作完毕！")