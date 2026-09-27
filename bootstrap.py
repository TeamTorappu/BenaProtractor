'''
核心 - 引擎装配
把「下载数据、建立目录、加载条目」这套与界面无关的流程集中在这里，
UI 层（tkinter / Qt）只负责展示，不重复实现一遍。
'''
import json
import os
import traceback

import bena
import downloader
from downloader import prepare_files

CACHE = "./.cache"
CONFIG_PATH = "./config.json"

LOAD_TYPES = {
    "buff" : "常见Buff",
    "buff_template" : "Buff模板（机制底层）",
    "global_buff" : "全局Buff（藏品、关卡、活动机制）",
}

# 肉鸽季度不写死：季度号与名称都从游戏数据推导（bena.roguelike_season_catalog）。
# 以前这里是 rogue_1..rogue_6 六个常量，游戏出新季度就得改这里 + 导航 + range(1,7)；
# 现在新季度会自动出现在「选择要加载的内容」和左侧导航里。
ROGUE_LOAD_SUFFIX = "肉鸽物品（藏品等）"


def all_load_types():
    '''完整的加载项清单（基础类型 + 数据里实际存在的肉鸽季度）'''
    types = dict(LOAD_TYPES)
    for key,label in bena.roguelike_season_catalog().items():
        types[key] = f"{label}{ROGUE_LOAD_SUFFIX}"
    return types


def default_load():
    '''默认加载项：基础类型 + 最后一个肉鸽季度（跟以前 Default 行为一致）'''
    seasons = bena.roguelike_seasons()
    loads = ["buff","buff_template","global_buff"]
    if seasons:
        loads.append(seasons[-1])
    return loads


DEFAULT_LOAD = ["buff","buff_template","global_buff","rogue_6"]

# 当前挂着的界面实例
UI = None

# 界面偏好配置（窗口大小、分栏、侧边栏等；与 .cache 的加载项记忆互不干扰）
DEFAULT_CONFIG = {
    "ui" : "qt",
    "theme" : "auto",
    "accent" : "",
    "colors" : {"preset" : "default","overrides" : {}},
    "window" : {},
    "splitter" : [],
    "splitters" : {},
    "sidebar" : {},
    "enable_ai_fragments" : True
}
_CONFIG = None


def set_ui(ui):
    global UI
    UI = ui
    return UI


def get_ui():
    return UI


# ----------------------------------------
# 界面配置读写
# ----------------------------------------
def load_config():
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = json.loads(json.dumps(DEFAULT_CONFIG)) # 深拷贝一份默认值
        if os.path.exists(CONFIG_PATH):
            try:
                # utf-8-sig：有人（或某些编辑器/PowerShell）会写入 BOM，用 utf-8 读会直接失败
                with open(CONFIG_PATH,'r',encoding="utf-8-sig") as file:
                    loaded = json.load(file)
                if isinstance(loaded,dict):
                    _CONFIG.update(loaded)
            except Exception:
                print("[量角器]config.json 读取失败，使用默认配置")
                traceback.print_exc()
    return _CONFIG


def save_config():
    if _CONFIG is None:
        return
    try:
        # 一律不带 BOM 写
        with open(CONFIG_PATH,'w',encoding="UTF-8",newline="\n") as file:
            file.write(json.dumps(_CONFIG,indent=4,ensure_ascii=False))
    except Exception:
        print("[量角器]config.json 写入失败")
        traceback.print_exc()


def config_get(section,key,default=None):
    config = load_config()
    if section is None:
        return config.get(key,default)
    return config.get(section,{}).get(key,default)


def config_set(section,key,value,save=True):
    config = load_config()
    if section is None:
        config[key] = value
    else:
        config.setdefault(section,{})[key] = value
    if save:
        save_config()


def config_section(section,default=None):
    '''取一整节（例如 "colors"），没有就返回 default'''
    config = load_config()
    value = config.get(section)
    if isinstance(value,dict):
        return value
    return default if default is not None else {}


def config_update_section(section,values,save=True):
    '''合并写入一整节（不会把没提到的键丢掉）'''
    config = load_config()
    current = config.get(section)
    if not isinstance(current,dict):
        current = {}
    current.update(values or {})
    config[section] = current
    if save:
        save_config()
    return current


# ----------------------------------------
# 加载项记忆
# ----------------------------------------
def load_cache():
    loads = []
    with open(CACHE,"r") as file:
        loads = file.read().splitlines()
    return [line for line in loads if line != ""]


def save_cache(loads):
    with open(CACHE,"w") as file:
        file.write("\n".join(loads))


# ----------------------------------------
# 按选择装配目录
# ----------------------------------------
def start_with(loads, ui=None):
    target = ui if ui is not None else get_ui()
    if target is None:
        print("[量角器]还没有界面实例，无法建立目录")
        return
    if "buff" in loads:
        bena.load_buff_table()
        target.load_directory("buff",bena.BUFF_TABLE)
    if "buff_template" in loads:
        bena.load_buff_template_data()
        target.load_directory("buff_template",bena.BUFF_TEMPLATE_DATA)
    if "global_buff" in loads:
        bena.load_global_buff_dummy()
        target.load_directory("global_buff",bena.GLOBAL_BUFF_DUMMY)
    for season_key in bena.roguelike_seasons():
        if season_key not in loads:
            continue
        bena.load_roguelike_topic_table(season_key)
        # 关键：用**本季度自己的表**，而不是全局别名——
        # 六个季度共用一份全局表时，页面会显示成最后加载那季的内容（已修）。
        table = bena.roguelike_season_table(season_key)
        target.load_directory("rogue_item",table,section_key=season_key)


# ----------------------------------------
# 引擎初始化（下载 + 名称表）
# ----------------------------------------
def download_data(progress=None,cancel=None):
    '''只做「把游戏数据下载齐」这件事（首次启动时用，可能要几分钟）

    progress 可选回调：progress(stage_text, current, total)
    cancel   可选 threading.Event：置位后下载会在下一个数据块处停下
    '''
    def report(stage,current=0,total=0):
        if progress is not None:
            try:
                progress(stage,current,total)
            except Exception:
                traceback.print_exc()
    callback = _download_callback(progress,cancel) if progress is not None else None
    prepare_files(callback)
    return downloader.missing_files()


def init_engine(progress=None,skip_download=False):
    '''初始化引擎：下载数据（可跳过）+ 读取干员/敌人名称表

    progress 可选回调：progress(stage_text, current, total)
    无回调时使用各模块原有的控制台输出。
    '''
    def report(stage,current=0,total=0):
        if progress is not None:
            try:
                progress(stage,current,total)
            except Exception:
                # 界面回调自己出错不该拖垮引擎初始化
                traceback.print_exc()
    if not skip_download:
        report("检查游戏数据文件")
        prepare_files(_download_callback(progress) if progress is not None else None)
    else:
        report("检查游戏数据文件")
    report("读取干员名称表")
    bena.load_character_names()
    report("读取敌人名称表")
    bena.load_enemy_names()
    report("引擎就绪",1,1)


def _download_callback(progress,cancel=None):
    '''把下载器的回调转成界面好用的 (stage, current, total)

    下载器的签名是 (name, current, total, stage)，界面只知道「当前在干什么、进度多少」。
    '''
    def _cb(name,current,total,stage=None):
        if cancel is not None and cancel.is_set():
            raise IOError("下载已取消")
        if stage == "all_done":
            progress("游戏数据下载完成",1,1)
            return
        if stage == "done":
            progress(f"{name} 下载完成",1,1)
            return
        if isinstance(stage,str) and stage.startswith("retry"):
            progress(f"{name} 下载中断，正在续传重试…",0,0)
            return
        progress(f"下载 {name}",current,total)
    return _cb


def bootstrap(loads=None, ui=None, progress=None):
    '''一步到位：初始化引擎 + 建立目录。返回实际使用的 loads'''
    init_engine(progress)
    if loads is None:
        if os.path.exists(CACHE):
            loads = load_cache()
        else:
            loads = default_load()
    start_with(loads,ui)
    return loads


__all__ = [
    "CACHE","CONFIG_PATH","LOAD_TYPES","DEFAULT_LOAD","all_load_types","default_load",
    "UI","set_ui","get_ui",
    "load_config","save_config","config_get","config_set",
    "load_cache","save_cache","start_with","init_engine","bootstrap",
]
