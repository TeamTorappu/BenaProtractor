'''
贝娜的剪刀 - 分析组件
将yj的json解读为可以阅读的格式，主要是node
'''
import json
from data_class import *
import anne

BUFF_TEMPLATE_KEYS = []
BUFF_TEMPLATE_TABLE = {}
BUFF_TEMPLATE_TABLE_PATH = "./tables/test_template_data.json"

# 读取buff_template_table.json，并解析
def load_buff_template_table():
    json_data = {}
    # 获取文件数据
    with open(BUFF_TEMPLATE_TABLE_PATH, 'r') as _f:
        json_data = json.load(_f)
    # 开始解析
    for buff_template_key in json_data.keys():
        BUFF_TEMPLATE_KEYS.append(buff_template_key)
        BUFF_TEMPLATE_TABLE[buff_template_key] = BuffTemplate(buff_template_key,json_data[buff_template_key])
        print(f"已读取 {buff_template_key}")
        '''
        try:
            BUFF_TEMPLATE_KEYS.append(buff_template_key)
            BUFF_TEMPLATE_TABLE[buff_template_key] = BuffTemplate(json_data[buff_template_key])
            print(f"已读取 {buff_template_key}")
        except:
            print(f"读取 {buff_template_key} 失败。原因不明。")
        '''