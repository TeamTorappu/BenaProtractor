#----------------------------------------
# 数据库加载（Catalog的后置方法）
#----------------------------------------
import json

from app_paths import app_path, app_path_file_exists, app_path_file_missing
from bena.split_activity_table import split_activity_table
from anne import Buff, BuffTemplate, GlobalBuff, RogueItem
from anne.autochess_band import AutochessBand
from anne.autochess_char_chess import AutochessCharChess
from anne.autochess_effect import AutochessEffect
from anne.crisis import Crisis

# 准备工作
def prepare_tables(catalog):
    if app_path_file_missing("table_dummies", "global_buff_dummy.json"):
        print("[贝娜]GlobalBuff伪表不存在...没办法加载GlobalBuff，可能会影响藏品机制翻译")
    if app_path_file_exists("tables","activity_table.json") and app_path_file_missing("table_dummies", "activity_table_autochess.json"):
        split_activity_table()

# 加载数据
def load_tables(catalog):
    # 制作角色名称对照表（全名+短名均可对照）
    with open(app_path("tables","character_table.json"), encoding="utf-8") as _f:
        for key, data in json.load(_f).items():
            catalog.character_display_names[key] = data["name"]
            if "_" in key:
                catalog.character_display_names["_".join(key.split("_")[2:])] = data["name"]

    # 制作敌人名称对照表（全名+短名均可对照）
    with open(app_path("tables","enemy_database.json"), encoding="utf-8") as _f:
        json_data = json.load(_f)
        items = ((x["Key"], x["Value"]) for x in json_data["enemies"]) if "enemies" in json_data else json_data.items()
        for key, data in items:
            catalog.enemy_display_names[key] = data[0]["enemyData"]["name"]["m_value"]
            if "_" in key:
                catalog.enemy_display_names["_".join(key.split("_")[2:])] = data[0]["enemyData"]["name"]["m_value"]

    # Buff表加载
    with open(app_path("tables","buff_table.json"), encoding="utf-8") as _f:
        for key, data in json.load(_f).items():
            catalog.add("buff", key, Buff(key, data))
    
    # Buff模板表加载
    with open(app_path("tables","buff_template_data.json"), encoding="utf-8") as _f:
        for key, data in json.load(_f).items():
            catalog.add("buff", key, BuffTemplate(key, data))

    # GlobalBuff表加载
    if app_path_file_exists("table_dummies", "global_buff_dummy.json"):
        with open(app_path("table_dummies", "global_buff_dummy.json"), encoding="utf-8") as _f:
            for key, data in json.load(_f).items():
                catalog.add("buff", key, GlobalBuff(key, data))
                
    catalog.loaded_tables.add("buff")
    

    # 加载肉鸽季度
    seasons = [t for t in catalog.tables if t.startswith("rogue_")]
    if seasons:
        with open(app_path("tables", "roguelike_topic_table.json"), encoding="utf-8") as _f:
            details = json.load(_f)["details"]
            for season in seasons:
                if season not in details:
                    catalog.warnings.append(f"数据中尚无 {season}")
            for season, data in details.items():
                if not season.startswith("rogue_"):
                    continue
                for key, info in data.get("items", {}).items():
                    catalog.add(season, key, RogueItem(season, key, info, data.get("relics", {}).get(key)))
                catalog.loaded_tables.add(season)
            
    # 加载卫戍协议
    if "autochess_3" in catalog.tables and app_path_file_exists("table_dummies", "activity_table_autochess.json"):
        with open(app_path("table_dummies", "activity_table_autochess.json"), encoding="utf-8") as _f:
            json_data = json.load(_f)
            act_data = json_data["activity"]["act3autochess"]["V3_1"]
            info_data = json_data["autoChessData"]
            # 干员棋子
            for key, data in act_data["charShopChessDatas"].items():
                chess_data = act_data["charChessDataDict"].get(data["chessId"],{})
                golden_chess_data = act_data["charChessDataDict"].get(data["goldenChessId"],{})
                garrison_data = {}
                if "garrisonIds" in chess_data and chess_data["garrisonIds"] != None:
                    for garrison in chess_data["garrisonIds"]:
                        garrison_data[garrison] = act_data["garrisonDataDict"].get(garrison,{})
                golden_garrison_data = {}
                if "garrisonIds" in golden_chess_data and golden_chess_data["garrisonIds"] != None:
                    for garrison in golden_chess_data["garrisonIds"]:
                        golden_garrison_data[garrison] = act_data["garrisonDataDict"].get(garrison,{})
                catalog.add("autochess_3", key, AutochessCharChess(key,data,chess_data,garrison_data,golden_chess_data,golden_garrison_data))
            # 卫戍效果
            for key, data in act_data["effectInfoDataDict"].items():
                effect_buff = act_data["effectBuffInfoDataDict"].get(key,{})
                catalog.add("autochess_3", key, AutochessEffect(key, data, effect_buff))
            # 策略/分队
            for key, data in act_data["bandDataListDict"].items():
                band_info = info_data["bandDataDict"].get(key,{})
                if data["effectId"] != None:
                    band_effect_info = act_data["effectInfoDataDict"].get(data["effectId"],{})
                    band_effect_buff = act_data["effectBuffInfoDataDict"].get(data["effectId"],{})
                    band_effect = AutochessEffect(data["effectId"], band_effect_info, band_effect_buff)
                    catalog.add("autochess_3", key, AutochessBand(key, data, band_info, band_effect))
                else:
                    catalog.add("autochess_3", key, AutochessBand(key, data, band_info))
        catalog.loaded_tables.add("autochess_3")

    # 加载全息作战矩阵
    if "recal_rune" in catalog.tables:
        with open(app_path("tables", "crisis_v2_table.json"), encoding="utf-8") as _f:
            json_data = json.load(_f)
            for season_key, season_data in json_data["recalRuneData"]["seasons"].items():
                stages = season_data["stages"]
                for stage_key, stage_data in stages.items():
                    level_name = stage_data["levelCode"] + " " + stage_data["levelName"]
                    for key, crisis_data in stage_data["runes"].items():
                        crisis = Crisis(key, crisis_data)
                        crisis.catagory = level_name
                        catalog.add("recal_rune", key, crisis)
        catalog.loaded_tables.add("recal_rune")



# 后处理table
def install_tables(catalog):
    from bena.translate_buff_name import translate_buff_name
    for entry in catalog.entries.values():
        if entry.table in ["buff","buff_template","global_buff"]:
            entry.obj.display_name = translate_buff_name(entry.key)
        else:
            entry.obj.display_name = entry.obj.get_display_name()
    catalog.names = {}
    for entry in catalog.entries.values():
        if not entry.table.startswith("rogue_"):
            catalog.names.setdefault(entry.name, []).append(entry)