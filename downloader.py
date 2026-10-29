#----------------------------------------
# 下载器
#----------------------------------------
import json
import os
from pathlib import Path
import tempfile
import time
import urllib.error
import urllib.request
from app_paths import app_path
from table_history import TABLE_LOCK, list_snapshots, same_content, stage_snapshot
from data_sources import DEFAULT_SOURCE, SOURCE_LABELS, SOURCE_URLS

WEB = SOURCE_URLS[DEFAULT_SOURCE]
FILES = {
    "buff_table.json": "buff_table.json",
    "character_table.json": "excel/character_table.json",
    "roguelike_topic_table.json": "excel/roguelike_topic_table.json",
    "buff_template_data.json": "battle/buff_template_data.json",
    "enemy_database.json": "levels/enemydata/enemy_database.json",
}


def read_metadata(directory=None):
    try:
        data = json.loads((Path(directory or app_path("tables")) / ".update.json").read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def update_due(hours, directory=None, names=None, source=DEFAULT_SOURCE):
    if source not in SOURCE_URLS:
        raise ValueError("未知下载源")
    entries = read_metadata(directory).get("files", {})
    now = time.time()
    for name in names or FILES:
        try:
            previous = entries.get(name, {})
            url = SOURCE_URLS[source] + FILES[name]
            if not matches_source(previous, source, url):
                return True
            checked = float(previous.get("checked_at", 0))
        except (TypeError, ValueError, AttributeError):
            return True
        if checked > now or now - checked >= hours * 3600:
            return True
    return False


def matches_source(entry, source, url):
    # Metadata from versions before source selection belongs to GitHub.
    return isinstance(entry, dict) and entry.get('source', DEFAULT_SOURCE) == source and entry.get('url', url) == url


def validate_table(name, path):
    with open(path, encoding="utf-8-sig") as stream:
        data = json.load(stream)
    if not isinstance(data, dict) or not data:
        raise ValueError(f"{name} 不是有效的数据对象")
    if name == "buff_template_data.json":
        if not all(isinstance(v, dict) and isinstance(v.get("eventToActions"), dict)
                   and all(isinstance(nodes, list) for nodes in v["eventToActions"].values()) for v in data.values()):
            raise ValueError("buff_template_data.json 缺少有效的 eventToActions")
    elif name == "buff_table.json":
        if not all(isinstance(v, dict) and "templateKey" in v for v in data.values()):
            raise ValueError("buff_table.json 缺少 templateKey")
    elif name == "roguelike_topic_table.json":
        if not isinstance(data.get("details"), dict):
            raise ValueError("roguelike_topic_table.json 缺少 details")
    elif name == "character_table.json":
        if not all(isinstance(v, dict) and "name" in v for v in data.values()):
            raise ValueError("character_table.json 缺少 name")
    elif name == "enemy_database.json":
        if not isinstance(data.get("enemies", data), (list, dict)):
            raise ValueError("enemy_database.json 格式错误")
    return data


def prepare_files(force=False, names=None, progress=None, directory=None, opener=None, validator=None, source=DEFAULT_SOURCE):
    """Stage the entire batch before replacing anything. force checks existing files.

    HTTP validators avoid downloading unchanged files. An optional validator sees
    the complete candidate before commit, so incompatible data cannot replace it.
    """
    if source not in SOURCE_URLS:
        raise ValueError("未知下载源")
    directory = Path(directory or app_path("tables"))
    directory.mkdir(parents=True, exist_ok=True)
    names = list(FILES if names is None else names)
    if any(name not in FILES for name in names):
        raise ValueError("未知数据文件")
    progress = progress or (lambda message: None)
    opener = opener or urllib.request.urlopen
    old_entries = read_metadata(directory).get("files", {})
    if not isinstance(old_entries, dict):
        old_entries = {}
    entries = dict(old_entries)
    changed = []
    with TABLE_LOCK, tempfile.TemporaryDirectory(prefix=".update-", dir=directory) as temporary:
        list_snapshots(directory)
        stage = Path(temporary)
        for index, name in enumerate(names, 1):
            target = directory / name
            url = SOURCE_URLS[source] + FILES[name]
            previous = old_entries.get(name, {})
            if not isinstance(previous, dict):
                previous = {}
            same_source = matches_source(previous, source, url)
            if target.exists() and not force and same_source:
                continue
            progress(f"检查数据 {index}/{len(names)} · {SOURCE_LABELS[source]} · {name}")
            headers = {"User-Agent": "BenaProtractor/2", "Accept": "application/json"}
            if target.exists() and same_source:
                if previous.get("etag"):
                    headers["If-None-Match"] = previous["etag"]
                if previous.get("last_modified"):
                    headers["If-Modified-Since"] = previous["last_modified"]
            request = urllib.request.Request(url, headers=headers)
            try:
                with opener(request, timeout=30) as response:
                    with (stage / name).open("wb") as output:
                        received = 0
                        last_report = 0
                        while True:
                            block = response.read(256 * 1024)
                            if not block:
                                break
                            output.write(block)
                            received += len(block)
                            if time.monotonic() - last_report > 0.5:
                                progress(f"下载 {index}/{len(names)} · {name} · {received / 1048576:.1f} MB")
                                last_report = time.monotonic()
                    entries[name] = {"source": source, "url": url,
                                     "etag": response.headers.get("ETag", ""),
                                     "last_modified": response.headers.get("Last-Modified", ""),
                                     "checked_at": time.time()}
                data = validate_table(name, stage / name)
                if not same_content(target, data):
                    changed.append(name)
            except urllib.error.HTTPError as error:
                if error.code != 304 or not target.exists() or not same_source:
                    raise
                validate_table(name, target)
                entries[name] = dict(previous, source=source, url=url, checked_at=time.time())
        if validator and changed:
            validator({name: stage / name if name in changed else directory / name for name in names})
        (stage / ".update.json").write_text(json.dumps({"checked_at": time.time(), "source": source, "files": entries}, indent=2), encoding="utf-8")
        snapshot = stage_snapshot(directory, stage, FILES) if changed else None
        replaced = []
        try:
            for name in changed + [".update.json"]:
                target = directory / name
                backup = stage / (name + ".backup")
                if target.exists():
                    os.replace(target, backup)
                replaced.append((target, backup))
                os.replace(stage / name, target)
            if snapshot:
                history = directory / ".history"
                history.mkdir(exist_ok=True)
                os.replace(snapshot, history / snapshot.name)
        except OSError:
            for target, backup in reversed(replaced):
                if backup.exists():
                    os.replace(backup, target)
                elif target.exists():
                    target.unlink()
            raise
    progress(f"数据已更新 · {len(changed)} 个文件" if changed else "已检查 · 数据为最新")
    return changed
