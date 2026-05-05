import json

ANNE_DICTIONARY_PATH = "translation/anne_dictionary.json"
ANNE_DICTIONARY = None
BENA_DICTIONARY_PATH = "translation/bena_dictionary.json"
BENA_DICTIONARY = None

# 读取字典数据
if BENA_DICTIONARY == None:
    with open(BENA_DICTIONARY_PATH,'r',encoding="UTF-8") as _f:
        BENA_DICTIONARY = json.load(_f)
# 读取字典数据
if ANNE_DICTIONARY == None:
    with open(ANNE_DICTIONARY_PATH,'r',encoding="UTF-8") as _f:
        ANNE_DICTIONARY = json.load(_f)
        
# 贝娜的查字典方法
# 如果查不到会返回空
def bena_dictionary(catalogue,type_str):
    return BENA_DICTIONARY[catalogue].get(type_str,"")
    
# 安妮的查字典方法
# 如果查不到会返回原文
def anne_dictionary(catalogue,type_str):
    return ANNE_DICTIONARY[catalogue].get(type_str,type_str)
    
# 获取贝娜的字典
def get_bena_dictionary():
    return BENA_DICTIONARY

# 获取安妮的字典
def get_anne_dictionary():
    return ANNE_DICTIONARY

# 检查贝娜字典是否包含某个类
def is_bena_catalogue(catalogue):
    return (catalogue in BENA_DICTIONARY)

# 检查安妮字典是否包含某个类
def is_anne_catalogue(catalogue):
    return (catalogue in ANNE_DICTIONARY)

# 检查贝娜字典某一类中是否包含某个值
def is_bena_key(catalogue,key):
    return (key in BENA_DICTIONARY[catalogue])

# 检查贝娜字典某一类中是否包含某个值
def is_anne_key(catalogue,key):
    return (key in ANNE_DICTIONARY[catalogue])