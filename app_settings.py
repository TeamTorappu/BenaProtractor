"""Persistent preferences with legacy .cache migration."""
import json
import os
from app_paths import app_path
from data_sources import DEFAULT_SOURCE, SOURCE_LABELS

LOAD_TYPES = {
    "buff": "常见 Buff",
    "buff_template": "Buff 模板 · 机制底层",
    "global_buff": "全局 Buff · 藏品 / 盟约",
    "rogue_1": "傀影 · 收藏品",
    "rogue_2": "水月 · 收藏品 / 排异反应",
    "rogue_3": "萨米 · 收藏品 / 密文板效果",
    "rogue_4": "萨卡兹 · 收藏品",
    "rogue_5": "界园 · 收藏品 / 通宝",
    "rogue_6": "树海 · 收藏品 / 天气",
}
DEFAULT_LOAD = list(LOAD_TYPES)
DEFAULTS = {
    "tables": DEFAULT_LOAD,
    "auto_update": True,
    "update_hours": 24,
    "font_size": 11,
    "ui_font_size": 10,
    "show_hidden": False,
    "theme": "light",
    "download_source": DEFAULT_SOURCE
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
        result["tables"] = list(dict.fromkeys(x for x in data["tables"] if isinstance(x, str) and x in LOAD_TYPES))
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
    return normalize_settings(json.loads(path.read_text(encoding="utf-8")))

# 保存设置
def save_settings(settings, path=None):
    path = path or app_path(".settings.json")
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(normalize_settings(settings), ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)
