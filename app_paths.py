#----------------------------------------
# 程序绝对路径逻辑
#----------------------------------------
from pathlib import Path
import sys

BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
BASE_FILES = [
    "buff_table.json",
    "buff_template_data.json",
    "character_table.json",
    "enemy_database.json"
]
EXTRA_FILES = [
    "roguelike_topic_table.json",
    "activity_table.json"
]

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
def required_files(tables):
    files = [] + BASE_FILES
    # 如果加载肉鸽内容，额外需要读取肉鸽表格
    if any(t.startswith("rogue_") for t in tables):
        files.append("roguelike_topic_table.json")
    # 如果加载卫戍协议内容，额外需要读取活动表格
    if any(t == "autochess" or t.startswith("autochess_") for t in tables):
        files.append("activity_table.json")
    return files