'''
贝娜 - 分析组件
将yj的json解读为可以阅读的格式，主要是node
'''
import json
from data_class import *

BUFF_TEMPLATE_KEYS = []
BUFF_TEMPLATE_TABLE = {}
BUFF_TEMPLATE_TABLE_PATH = "./tables/test_template_data.json"
print("[贝娜]我叫贝娜，来找一个出门就忘了回家的笨蛋。听说她还有些活要干，没办法，我也在这陪她一会好了。")

# 读取buff_template_table.json，并解析
def load_buff_template_table():
    print(f"[贝娜]开始读取buff_template_table.json")
    json_data = {}
    # 获取文件数据
    with open(BUFF_TEMPLATE_TABLE_PATH, 'r') as _f:
        json_data = json.load(_f)
    # 开始解析
    for buff_template_key in json_data.keys():
        BUFF_TEMPLATE_KEYS.append(buff_template_key)
        BUFF_TEMPLATE_TABLE[buff_template_key] = BuffTemplate(buff_template_key,json_data[buff_template_key])
        print(f"[贝娜]已读取 {buff_template_key}")
    print(f"[贝娜]已完成对buff_template_table.json的读取！")