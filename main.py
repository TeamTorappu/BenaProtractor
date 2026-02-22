'''
核心GUI
'''
import tkinter as tk
import os
import bena
import anne

if __name__ == "__main__":
    print("开始处理")
    bena.load_buff_template_table()
    # 随便挑一个来测试
    picked_buff = bena.BUFF_TEMPLATE_TABLE["skadi2_t_2"]
    lines = anne.translate_whole_buff_template(picked_buff)
    for line in lines:
        print(line)