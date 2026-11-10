#----------------------------------------
# 数据库加载（Catalog的后置方法）
#----------------------------------------
import json

from app_paths import app_path, app_path_file_missing
from game_class import Buff, BuffTemplate, GlobalBuff, RogueItem

# 准备工作
def prepare_tables(catalog):
    if app_path_file_missing("table_dummies", "global_buff_dummy.json"):
        print("[贝娜]全局Buff伪表不存在...没办法加载全局Buff，可能会影响藏品机制翻译")

# 加载数据
def load_tables(catalog):
    # 制作角色名称对照表（全名+短名均可对照）
    for key, data in catalog.read("character_table.json").items():
        catalog.character_display_names[key] = data["name"]
        if "_" in key:
            catalog.character_display_names["_".join(key.split("_")[2:])] = data["name"]

    # 制作敌人名称对照表（全名+短名均可对照）
    json_data = catalog.read("enemy_database.json")
    items = ((x["Key"], x["Value"]) for x in json_data["enemies"]) if "enemies" in json_data else json_data.items()
    for key, data in items:
        catalog.enemy_display_names[key] = data[0]["enemyData"]["name"]["m_value"]
        if "_" in key:
            catalog.enemy_display_names["_".join(key.split("_")[2:])] = data[0]["enemyData"]["name"]["m_value"]

    # Buff表加载
    for key, data in catalog.read("buff_table.json").items():
        catalog.add("buff", key, Buff(key, data))
    
    # Buff模板表加载
    for key, data in catalog.read("buff_template_data.json").items():
        catalog.add("buff_template", key, BuffTemplate(key, data))

    # Dummy表加载
    if not app_path_file_missing("table_dummies", "global_buff_dummy.json"):
        with app_path("table_dummies", "global_buff_dummy.json").open(encoding="utf-8") as stream:
            for key, data in json.load(stream).items():
                catalog.add("global_buff", key, GlobalBuff(key, data))

    
    catalog.loaded_tables.update(("buff", "buff_template", "global_buff"))

    # 加载肉鸽极度
    seasons = [t for t in catalog.tables if t.startswith("rogue_")]
    if seasons:
        details = catalog.read("roguelike_topic_table.json")["details"]
        for season in seasons:
            if season not in details:
                catalog.warnings.append(f"数据中尚无 {season}")
        # All themes share one file. Keep their contents available while
        # table preferences only control which groups are shown.
        for season, data in details.items():
            if not season.startswith("rogue_"):
                continue
            for key, info in data.get("items", {}).items():
                catalog.add("rogue_item", key, RogueItem(season, key, info, data.get("relics", {}).get(key)), season)
            catalog.loaded_tables.add(season)

def install_tables(catalog):
    from bena.translate_buff_name import translate_buff_name
    for entry in catalog.entries.values():
        if entry.category != "rogue_item":
            entry.obj.display_name = translate_buff_name(entry.key)
    catalog.names = {}
    for entry in catalog.entries.values():
        if entry.category != "rogue_item":
            catalog.names.setdefault(entry.name, []).append(entry)