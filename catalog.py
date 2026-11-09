"""Build snapshots off the UI thread; install them between UI events."""
from dataclasses import dataclass
import json
import bena
from app_paths import app_path
from game_class import Buff, BuffTemplate, GlobalBuff, RogueItem

BASE_FILES = ["buff_table.json", "buff_template_data.json", "character_table.json", "enemy_database.json"]


def required_files(tables):
    return BASE_FILES + (["roguelike_topic_table.json"] if any(t.startswith("rogue_") for t in tables) else [])


@dataclass
class Entry:
    category: str
    key: str
    obj: object
    table: str

    @property
    def target(self):
        return f"{self.category}.{self.key}"

    @property
    def name(self):
        return self.obj.display_name

# 大目录
class Catalog:
    def __init__(self, tables, paths=None):
        self.tables = list(tables)
        self.loaded_tables = set()
        self.entries = {}
        self.groups = {key: {} for key in ("buff", "buff_template", "global_buff", "rogue_item")}
        self.characters = {}
        self.enemies = {}
        self.paths = paths or {}
        self.warnings = []
        self.names = {}

    def read(self, name):
        with open(self.paths.get(name, app_path("tables", name)), encoding="utf-8-sig") as stream:
            return json.load(stream)

    def add(self, category, key, obj, table=None):
        entry = Entry(category, key, obj, table or category)
        self.groups[category][key] = obj
        self.entries[entry.target] = entry

    def load(self):
        for key, data in self.read("character_table.json").items():
            self.characters["_".join(key.split("_")[2:]) if "_" in key else key] = data.get("name", key)
        enemies = self.read("enemy_database.json")
        items = ((x["Key"], x["Value"]) for x in enemies["enemies"]) if "enemies" in enemies else enemies.items()
        for key, values in items:
            if values:
                self.enemies["_".join(key.split("_")[2:]) if "_" in key else key] = values[0]["enemyData"]["name"]["m_value"]
        for category, filename, cls in (("buff", "buff_table.json", Buff),
                                        ("buff_template", "buff_template_data.json", BuffTemplate)):
            for key, data in self.read(filename).items():
                self.add(category, key, cls(key, data))
        with app_path("dummy", "global_buff_dummy.json").open(encoding="utf-8") as stream:
            for key, data in json.load(stream).items():
                self.add("global_buff", key, GlobalBuff(key, data))
        self.loaded_tables.update(("buff", "buff_template", "global_buff"))
        seasons = [t for t in self.tables if t.startswith("rogue_")]
        if seasons:
            details = self.read("roguelike_topic_table.json")["details"]
            for season in seasons:
                if season not in details:
                    self.warnings.append(f"数据中尚无 {season}")
            # All themes share one file. Keep their contents available while
            # table preferences only control which groups are shown.
            for season, data in details.items():
                if not season.startswith("rogue_"):
                    continue
                for key, info in data.get("items", {}).items():
                    self.add("rogue_item", key, RogueItem(season, key, info, data.get("relics", {}).get(key)), season)
                self.loaded_tables.add(season)
        return self

    def install(self):
        bena.CHARACTER_NAMES = self.characters
        bena.ENEMY_NAMES = self.enemies
        for category, attr, keys in (("buff", "BUFF_TABLE", "BUFF_KEYS"),
                                     ("buff_template", "BUFF_TEMPLATE_DATA", "BUFF_TEMPLATE_KEYS"),
                                     ("global_buff", "GLOBAL_BUFF_DUMMY", "GLOBAL_BUFF_KEYS"),
                                     ("rogue_item", "ROGUELIKE_TOPIC_TABLE", "ROGUELIKE_TOPIC_KEYS")):
            setattr(bena, attr, self.groups[category])
            setattr(bena, keys, list(self.groups[category]))
        for entry in self.entries.values():
            if entry.category != "rogue_item":
                entry.obj.display_name = bena.translate_buff_name(entry.key)
        self.names = {}
        for entry in self.entries.values():
            if entry.category != "rogue_item":
                self.names.setdefault(entry.name, []).append(entry)

    def visible(self, show_hidden=False):
        return [entry for entry in self.entries.values() if entry.table in self.tables
                and (show_hidden or not entry.obj.hidden)]

    def resolve(self, target, prefer=None):
        if target in self.entries:
            return self.entries[target]
        if target.split(".", 1)[0] in self.groups and "." in target:
            return None
        for category in dict.fromkeys([prefer, "buff", "buff_template", "global_buff", "rogue_item"]):
            entry = self.entries.get(f"{category}.{target}")
            if entry:
                return entry
        matches = self.names.get(target, [])
        return matches[0] if len(matches) == 1 else None

    def template_for(self, entry):
        if entry.category == "buff_template":
            return entry.obj
        if entry.category == "buff":
            return self.groups["buff_template"].get(entry.obj.buff_data.get("templateKey"))
        return None
