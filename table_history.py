"""Seven-day table snapshots and entry-level JSON comparisons."""
from dataclasses import dataclass
import difflib
import json
from pathlib import Path
import re
import threading
import time
import zipfile

from app_paths import app_path

TABLE_LOCK = threading.RLock()
RETENTION_SECONDS = 7 * 24 * 3600
SNAPSHOT_NAME = re.compile(r"tables-(\d+)\.zip")
CATEGORIES = {
    "buff_table.json": "buff",
    "buff_template_data.json": "buff_template",
    "character_table.json": "character",
    "enemy_database.json": "enemy",
    "roguelike_topic_table.json": "rogue_item",
}
MISSING = object()
SORT_KEYS = frozenset(("sortID", "sortId", "sortIndex"))


def snapshot_time(path):
    return int(SNAPSHOT_NAME.fullmatch(path.name).group(1)) / 1_000_000_000


def list_snapshots(directory=None, now=None):
    """Remove only our expired archives; newest replacement comes first."""
    directory = Path(directory or app_path("tables"))
    cutoff = (time.time() if now is None else now) - RETENTION_SECONDS
    with TABLE_LOCK:
        snapshots = []
        for path in (directory / ".history").glob("tables-*.zip"):
            if not SNAPSHOT_NAME.fullmatch(path.name) or not path.is_file():
                continue
            if snapshot_time(path) <= cutoff:
                path.unlink()
            else:
                snapshots.append(path)
        return sorted(snapshots, key=snapshot_time, reverse=True)


def stage_snapshot(directory, stage, names):
    """Prepare a complete pre-update archive; publish only with a successful batch."""
    files = [directory / name for name in names if (directory / name).is_file()]
    if not files:
        return None
    metadata = directory / ".update.json"
    if metadata.is_file():
        files.append(metadata)
    archive = stage / f"tables-{time.time_ns()}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as output:
        for path in files:
            output.write(path, path.name)
    return archive


def same_json(left, right, *, ignored_keys=frozenset()):
    # JSON booleans and numbers must not compare equal (False == 0 in Python).
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        left_keys, right_keys = left.keys() - ignored_keys, right.keys() - ignored_keys
        return left_keys == right_keys and all(
            same_json(left[key], right[key], ignored_keys=ignored_keys) for key in left_keys)
    if isinstance(left, list):
        return len(left) == len(right) and all(
            same_json(a, b, ignored_keys=ignored_keys) for a, b in zip(left, right))
    return left == right


def same_content(old, new):
    try:
        return same_json(json.loads(old.read_text(encoding="utf-8-sig")), new)
    except (OSError, ValueError):
        return False


def table_entries(filename, data):
    if filename == "enemy_database.json" and isinstance(data.get("enemies"), list):
        entries = {item["Key"]: item["Value"] for item in data["enemies"]}
        entries.update({"/" + key: value for key, value in data.items() if key != "enemies"})
        return entries
    if filename != "roguelike_topic_table.json":
        return data
    entries = {"/" + key: value for key, value in data.items() if key != "details"}
    for season, detail in data.get("details", {}).items():
        items, relics = detail.get("items", {}), detail.get("relics", {})
        for key in items.keys() | relics.keys():
            value = {}
            if key in items:
                value["item_info"] = items[key]
            if key in relics:
                value["item_data"] = relics[key]
            entries[f"{season}/items/{key}"] = value
        for section, value in detail.items():
            if section not in ("items", "relics"):
                if isinstance(value, dict) and value:
                    entries.update({f"{season}/{section}/{key}": item for key, item in value.items()})
                else:
                    entries[f"{season}/{section}"] = value
    return entries


@dataclass
class Change:
    table: str
    key: str
    before: object
    after: object

    @property
    def status(self):
        return "新增" if self.before is MISSING else "删除" if self.after is MISSING else "修改"

    @property
    def target(self):
        category = CATEGORIES[self.table]
        if category in ("buff", "buff_template"):
            return f"{category}.{self.key}"
        if category == "rogue_item" and "/items/" in self.key:
            return "rogue_item." + self.key.split("/items/", 1)[1]
        return ""

    @property
    def name(self):
        data = self.before if self.after is MISSING else self.after
        if isinstance(data, dict):
            return data.get("item_info", data).get("name", self.key)
        if self.table == "enemy_database.json" and isinstance(data, list) and data:
            return data[0].get("enemyData", {}).get("name", {}).get("m_value", self.key)
        return self.key

    def diff(self):
        def lines(value):
            if value is MISSING:
                return []
            return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").splitlines(True)
        return "".join(difflib.unified_diff(
            lines(self.before), lines(self.after),
            fromfile=f"历史/{self.table}/{self.key}", tofile=f"当前/{self.table}/{self.key}"))


def compare_snapshot(snapshot, directory=None):
    """Compare raw data, retaining only changed entries in memory."""
    directory = Path(directory or app_path("tables"))
    changes = []
    with TABLE_LOCK, zipfile.ZipFile(snapshot) as archive:
        saved = set(archive.namelist())
        for filename in CATEGORIES:
            old = json.loads(archive.read(filename).decode("utf-8-sig")) if filename in saved else {}
            path = directory / filename
            new = json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
            before, after = table_entries(filename, old), table_entries(filename, new)
            for key in sorted(before.keys() | after.keys()):
                left, right = before.get(key, MISSING), after.get(key, MISSING)
                if not same_json(left, right, ignored_keys=SORT_KEYS):
                    changes.append(Change(filename, key, left, right))
    return changes
