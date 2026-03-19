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
# 如果查不到会返回原文
def bena_dictionary(catalogue,type_str):
    return BENA_DICTIONARY[catalogue].get(type_str,type_str)
    
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