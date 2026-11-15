#----------------------------------------
# 数据库
#----------------------------------------
import json
from dataclasses import dataclass
from app_paths import app_path

@dataclass
class Entry:
    table: str
    key: str
    obj: object

    @property
    def target(self):
        return type(self.obj).__name__ + "." + self.key
    
    @property
    def type_name(self):
        return type(self.obj).__name__

    @property
    def catagory(self):
        return self.obj.catagory

    @property
    def name(self):
        return self.obj.get_display_name()
    
    @property
    def search_key(self):
        return (self.key+" "+self.obj.get_display_name()+" "+self.obj.catagory).casefold()

# 大目录
class Catalog:
    def __init__(self, tables):
        self.tables = list(tables)
        self.loaded_tables = set()
        self.entries = {}
        self.groups = {}
        self.characters = {}
        self.enemies = {}
        self.character_display_names = {}
        self.enemy_display_names = {}
        self.warnings = []
        self.names = {}

    def add(self, table, key, obj):
        entry = Entry(table, key, obj)
        self.groups.setdefault(table, {})[key] = obj
        self.entries[entry.target] = entry

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
        categories = dict.fromkeys(
            category for category in
            (prefer, "buff", "buff_template", "global_buff", "rogue_item", *self.groups)
            if category
        )
        for category in categories:
            entry = self.entries.get(f"{category}.{target}")
            if entry:
                return entry
        matches = self.names.get(target, [])
        return matches[0] if len(matches) == 1 else None

    def template_for(self, entry):
        if entry.category == "buff_template":
            return entry.obj
        if entry.category == "buff":
            return self.groups.get("buff_template", {}).get(entry.obj.buff_data.get("templateKey"))
        return None