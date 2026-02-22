'''
量角器 - UI
'''
import tkinter as tk
from tkinter import ttk
import os
import bena
import anne

os.environ['PYTHONWARNINGS'] = 'ignore:libpng warning:'
PROTRACTOR = None

# 定义UI类
class Protractor:
    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry("800x600")
        self.window.title('贝娜的量角器')
        self.frame = ttk.Frame(self.window, padding=10)
        self.frame.pack(fill="both",expand=True)
        # 控制区域
        self.control_panel = ttk.Frame(self.frame,width=300)
        self.control_panel.pack(fill="y",side="left")
        # 目录
        self.directory_items = []
        self.directory_index = 0 # 用于为每个目录编号
        self.search_entry = ttk.Entry(self.control_panel,text="按回车键搜索...")
        self.search_entry.bind("<Return>", self.try_search)
        self.search_entry.pack(fill="x",side="top")
        self.searching = False
        self.directory = ttk.Treeview(self.control_panel,selectmode="browse",show="tree")
        self.directory_scrollbar = ttk.Scrollbar(self.control_panel,orient=tk.VERTICAL,command=self.directory.yview)
        self.directory.configure(yscrollcommand=self.directory_scrollbar.set)
        self.directory_scrollbar.pack(fill="y",side="left")
        self.directory.bind('<ButtonRelease-1>',self.display)
        self.directory.pack(fill="both",expand=True)
        # 核心区域
        self.main_panel = ttk.Frame(self.frame)
        self.main_panel.pack(fill="both",expand=True)
        # 显示
        self.display_area = ttk.Treeview(self.main_panel,selectmode="browse")
        self.display_area.pack(fill="both",expand=True)
        self.displaying = ""
    
    # 定义目录物品类
    # 可选类型有：buff_template buff relic
    class Item:
        def __init__(self,index,data_type,data_reference):
            self.data_type = data_type
            self.data_reference = data_reference
            self.display_name = ""
            self.index = index
            if self.data_type == "buff_template":
                self.display_name = "[模板]"+data_reference #待翻译
            elif self.data_type == "buff":
                self.display_name = "[Buff]"+data_reference #待翻译
            elif self.data_type == "relic":
                self.display_name = "[藏品]"+data_reference #待翻译
        # 显示元素，带双向链接
        def view(self,tree_view):
            label = tree_view.insert("","end",text=self.display_name,values=(self.index))#,open=True
            #label.link = self
            
    # 读取列表
    def load_directory(self,data_type,data_list):
        for data in data_list:
            new_item = self.Item(self.directory_index,data_type,data)
            self.directory_items.append(new_item)
            self.directory_index += 1
            new_item.view(self.directory)
    
    # 搜索
    def try_search(self,event=None):
        #try:
        keywords = self.search_entry.get().strip().lower().split(" ")
        if len(keywords) == 0 and self.searching:
            # 恢复列表
            self.directory.set_children([])
            for item in self.directory_items:
                new_item.view(self.directory)
            self.searching = False
        else:
            # 重新筛选列表（与模式）
            self.directory.set_children([])
            for item in self.directory_items:
                haskey = True 
                for keyword in keywords:
                    if keyword not in item.display_name and keyword not in item.data_reference:
                        haskey = False
                        break
                if haskey:
                    item.view(self.directory)
            self.searching = True
                        
        #except:
        #    print("[量角器]尝试搜索，但是失败了。")
    
    # 展示内容（使用安妮来翻译）
    def display(self,event=None):
        selected = self.directory.selection()
        if selected:
            linked_index = int(self.directory.item(selected[0],"values")[0])
            linked = self.directory_items[linked_index]
            if self.displaying != linked.data_reference: #如果相同说明是同一个，不需要显示
                self.displaying = linked.data_reference
            self.display_area.set_children([])
            # 使用贝娜解析的数据
            if linked.data_type == "buff_template":
                data = bena.BUFF_TEMPLATE_TABLE[linked.data_reference]
                if data:
                    # 使用安妮进行翻译
                    lines = anne.translate_whole_buff_template(data)
                    for line in lines:
                        #print(line)
                        label = self.display_area.insert("","end",text=line)
        
    # 开启界面
    def open(self):
        self.window.mainloop()
    
    # 关闭界面
    def close(self):
        self.window.destroy()

PROTRACTOR = Protractor()