#----------------------------------------
# 数据库
#----------------------------------------
import json
from dataclasses import dataclass
from app_paths import app_path

GROUPS = ["buff", "buff_template", "global_buff", "rogue_item"]

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
        self.groups = {key: {} for key in GROUPS}
        self.characters = {}
        self.enemies = {}
        self.character_display_names = {}
        self.enemy_display_names = {}
        self.paths = paths or {}
        self.warnings = []
        self.names = {}

    def add(self, category, key, obj, table=None):
        entry = Entry(category, key, obj, table or category)
        self.groups[category][key] = obj
        self.entries[entry.target] = entry

    def read(self, name):
        path = self.paths.get(name, app_path("tables", name))
        with open(path, encoding="utf-8-sig") as stream:
            return json.load(stream)

    def load(self):
        from bena.catalog_load import load_tables, prepare_tables

        prepare_tables(self)
        load_tables(self)
        return self

    def install(self):
        import bena
        from bena.catalog_load import install_tables

        bena.CATALOG = self
        install_tables(self)
        return self

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