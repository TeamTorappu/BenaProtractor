'''
核心
'''
import tkinter as tk
import os
import bena
import anne
from protractor import PROTRACTOR

if __name__ == "__main__":
    bena.load_buff_template_data()
    bena.load_roguelike_topic_table()
    PROTRACTOR.load_directory("buff_template",bena.BUFF_TEMPLATE_DATA)
    PROTRACTOR.load_directory("rogue_item",bena.ROGUELIKE_TOPIC_TABLE["rogue_5"])
    PROTRACTOR.open()
    # 随便挑一个来测试
    #picked_buff = bena.BUFF_TEMPLATE_DATA["skadi2_t_2"]
    #lines = anne.translate_whole_buff_template(picked_buff)
    #for line in lines:
    #    print(line)