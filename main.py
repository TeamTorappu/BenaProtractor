'''
核心
'''
import tkinter as tk
import os
import bena
import anne
from protractor import PROTRACTOR
from downloader import prepare_files

CACHE = "./.cache"

LOAD_TYPES = {
    "buff" : "常见Buff",
    "buff_template" : "Buff模板（机制底层）",
    "global_buff" : "全局Buff（藏品、关卡、活动机制）",
    "rogue_1" : "傀影肉鸽物品（藏品、剧目等）",
    "rogue_2" : "水月肉鸽物品（藏品、启示等）",
    "rogue_3" : "萨米肉鸽物品（藏品、密文板等）",
    "rogue_4" : "萨卡兹肉鸽物品（藏品、思绪等）",
    "rogue_5" : "界园肉鸽物品（藏品、钱等）"
}

DEFAULT_LOAD = ["buff","buff_template","rogue_5"]

# 直接打开
def start_with(loads):
    if "buff" in loads:
        bena.load_buff_table()
        PROTRACTOR.load_directory("buff",bena.BUFF_TABLE)
    if "buff_template" in loads:
        bena.load_buff_template_data()
        PROTRACTOR.load_directory("buff_template",bena.BUFF_TEMPLATE_DATA)
    if "global_buff" in loads:
        bena.load_global_buff_dummy()
        PROTRACTOR.load_directory("global_buff",bena.GLOBAL_BUFF_DUMMY)
    if "rogue_1" in loads:
        bena.load_roguelike_topic_table(1)
        PROTRACTOR.load_directory("rogue_item",bena.ROGUELIKE_TOPIC_TABLE)
    if "rogue_2" in loads:
        bena.load_roguelike_topic_table(2)
        PROTRACTOR.load_directory("rogue_item",bena.ROGUELIKE_TOPIC_TABLE)
    if "rogue_3" in loads:
        bena.load_roguelike_topic_table(3)
        PROTRACTOR.load_directory("rogue_item",bena.ROGUELIKE_TOPIC_TABLE)
    if "rogue_4" in loads:
        bena.load_roguelike_topic_table(4)
        PROTRACTOR.load_directory("rogue_item",bena.ROGUELIKE_TOPIC_TABLE)
    if "rogue_5" in loads:
        bena.load_roguelike_topic_table(5)
        PROTRACTOR.load_directory("rogue_item",bena.ROGUELIKE_TOPIC_TABLE)

# 读取缓存
def load_cache():
    loads = None
    with open(CACHE,"r") as file:
        loads = file.read().splitlines()
    return loads

# 选择加载哪些东西的逻辑
class Selector:
    def __init__(self):
        self.root = tk.Toplevel(PROTRACTOR.window)
        self.root.title("选择要加载的内容")
        tk.Label(self.root,text="请选择要加载的内容：").pack()
        self.frame = tk.Frame(self.root,bg="#FFFFFF")
        self.vars = []
        for type,title in LOAD_TYPES.items():
            var = tk.StringVar()
            if type in DEFAULT_LOAD:
                var.set(type)
            tk.Checkbutton(self.frame,text=title,variable=var,onvalue=type,offvalue="",bg="#FFFFFF",anchor="w").pack()
            self.vars.append(var)
        self.frame.pack(fill="x")
        self.remember = tk.BooleanVar()
        self.remember.set(True)
        tk.Checkbutton(self.root, text="记住选择", variable=self.remember, onvalue=True, offvalue=False).pack(fill="x")

        tk.Button(self.root, text="贝娜！部署！", command=self.confirm).pack()
    
    # 确认
    def confirm(self):
        global start_with
        loads = []
        for index in range(len(self.vars)):
            value = self.vars[index].get()
            if value != "":
                loads.append(value)
        # 如果选择了记住选择，保存一个缓存文件用于后续每次加载
        if self.remember.get():
            with open(CACHE,"w") as file:
                file.write("\n".join(loads))
        self.root.destroy()
        #打开
        start_with(loads)
        


if __name__ == "__main__":
    prepare_files()
    bena.load_character_names()
    bena.load_enemy_names()
    if os.path.exists(CACHE):
        start_with(load_cache())
    else:
        Selector()
    PROTRACTOR.open()