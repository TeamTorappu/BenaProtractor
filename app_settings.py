"""Persistent preferences with legacy .cache migration."""
import json
import os
from app_paths import app_path,TABLES

DEFAULT_LOAD = ["buff","rogue_6","autochess_3"]
DEFAULT_SOURCE = "github"
DEFAULTS = {
    "tables" : DEFAULT_LOAD,
    "auto_update" : True,
    "update_hours" : 24,
    "font_size" : 11,
    "ui_font_size" : 10,
    "show_hidden" : False,
    "theme" : "light",
    "download_source" : DEFAULT_SOURCE
}
SOURCE_LABELS = {
    "github" : "GitHub",
    "github2" : "GitHub（备用）",
    "prts" : "PRTS"
}
SOURCE_URLS = {
    'github' : 'https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/refs/heads/master/zh_CN/gamedata/',
    'github2' : 'https://raw.githubusercontent.com/ArknightsAssets/ArknightsGamedata/refs/heads/master/cn/gamedata/',
    'prts' : 'https://torappu.prts.wiki/gamedata/latest/',
}

# 标准化设置
def normalize_settings(data):
    result = dict(DEFAULTS, tables=list(DEFAULT_LOAD))
    if not isinstance(data, dict):
        return result
    if data.get('theme') in ('light', 'dark'):
        result['theme'] = data['theme']
    source = data.get('download_source')
    if isinstance(source, str) and source in SOURCE_LABELS:
        result['download_source'] = source
    if isinstance(data.get("tables"), list):
        selected = (x for x in data["tables"] if isinstance(x, str) and x in TABLES)
        result["tables"] = list(dict.fromkeys(("buff", *selected)))
    for key in ("auto_update", "show_hidden"):
        if isinstance(data.get(key), bool):
            result[key] = data[key]
    for key, low, high in (("font_size", 10, 18), ("ui_font_size", 9, 12), ("update_hours", 1, 168)):
        try:
            result[key] = max(low, min(high, int(data.get(key, result[key]))))
        except (ValueError, TypeError):
            pass
    return result

# 加载设置
def load_settings(path=None):
    path = path or app_path(".settings.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return normalize_settings({})
    return normalize_settings(data)

# 保存设置
def save_settings(settings, path=None):
    path = path or app_path(".settings.json")
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(normalize_settings(settings), ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)
