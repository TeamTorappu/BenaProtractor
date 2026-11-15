#----------------------------------------
# 程序绝对路径逻辑
#----------------------------------------
from pathlib import Path
import sys

BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent

BASE_FILES = [
    "character_table",
    "enemy_database"
]
TABLES = {
    "buff" : {
        "label" : "Buff（机制底层）",
        "description" : "Buff数据库 / Buff模板 / GlobalBuff",
        "required" : ["buff_table","buff_template_data"],
        "dummy" : ["global_buff_dummy"]
    },
    "rogue_1" : {
        "label" : "傀影与猩红孤钻",
        "description" : "集成战略#1",
        "required" : ["roguelike_topic_table"]
    },
    "rogue_2" : {
        "label" : "水月与深蓝之树",
        "description" : "集成战略#2",
        "required" : ["roguelike_topic_table"]
    },
    "rogue_3" : {
        "label" : "探索者的银凇止境",
        "description" : "集成战略#3",
        "required" : ["roguelike_topic_table"]
    },
    "rogue_4" : {
        "label" : "萨卡兹的无终奇语",
        "description" : "集成战略#4",
        "required" : ["roguelike_topic_table"]
    },
    "rogue_5" : {
        "label" : "岁的界园志异",
        "description" : "集成战略#5",
        "required" : ["roguelike_topic_table"]
    },
    "rogue_6" : {
        "label" : "沉沦者的黑流树海",
        "description" : "集成战略#6",
        "required" : ["roguelike_topic_table"]
    },
    "autochess_3" : {
        "label" : "卫戍协议:规程",
        "description" : "卫戍协议#3",
        "required" : ["activity_table"],
        "dummy" : ["activity_table_dummy"]
    },
    "vec_break_3" : {
        "label" : "矢量突破#3",
        "description" : "「拟生态」",
        "required" : ["activity_table"],
        "dummy" : ["activity_table_vec_break_v2"]
    },
    "recal_rune" : {
        "label" : "全息作战矩阵",
        "description" : "",
        "required" : ["crisis_v2_table"]
    }
}

# 获取绝对路径
def app_path(*parts):
    return BASE_DIR.joinpath(*parts)

# 获取绝对路径下的文件是否存在
def app_path_file_exists(*parts):
    return BASE_DIR.joinpath(*parts).exists()

# 获取绝对路径下的文件是否不存在
def app_path_file_missing(*parts):
    return not BASE_DIR.joinpath(*parts).exists()

# 获取运行需求文件
def required_files(table_names = []):
    requireds = [] + BASE_FILES
    # 根据读取的表格添加所需内容
    for table_name in table_names:
        for required in TABLES[table_name].get("required",[]):
            if required not in requireds:
                requireds.append(required)
    return requireds