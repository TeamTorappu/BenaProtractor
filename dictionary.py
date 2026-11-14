#----------------------------------------
# 字典读取
#----------------------------------------
import json
from app_paths import app_path

ENUM_DICTIONARY = None
BUFF_DICTIONARY = None

# 读取字典数据
if BUFF_DICTIONARY == None:
    with open(app_path("translation", "buff_dictionary.json"),'r',encoding="UTF-8") as _f:
        BUFF_DICTIONARY = json.load(_f)
if ENUM_DICTIONARY == None:
    with open(app_path("translation", "enum_dictionary.json"),'r',encoding="UTF-8") as _f:
        ENUM_DICTIONARY = json.load(_f)
        
#----------------------------------------
# 查字典方法
# 如果查不到会返回空
def buff_dictionary(catalogue,type_str):
    return BUFF_DICTIONARY[catalogue].get(type_str,"")
    
# 查字典方法
# 如果查不到会返回原文
def enum_dictionary(catalogue,type_str):
    return ENUM_DICTIONARY[catalogue].get(type_str,type_str)

# 检查是否存在对应ENUM
def if_enum_key(catalogue,key):
    return (key in ENUM_DICTIONARY[catalogue])
