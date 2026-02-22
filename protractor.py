'''
量角器 - UI
'''
import tkinter as tk
from tkinter import ttk
from tkinter import font
import os
import anne

os.environ['PYTHONWARNINGS'] = 'ignore:libpng warning:'
PROTRACTOR = None

# 定义UI类
class Protractor:
    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry("800x600")
        self.window.title('贝娜的量角器')
        self.style = ttk.Style()
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
        self.directory_scrollbar_x = ttk.Scrollbar(self.control_panel,orient=tk.HORIZONTAL,command=self.directory.yview)
        self.directory_scrollbar_y = ttk.Scrollbar(self.control_panel,orient=tk.VERTICAL,command=self.directory.yview)
        self.directory.configure(xscrollcommand=self.directory_scrollbar_x.set)
        self.directory.configure(yscrollcommand=self.directory_scrollbar_y.set)
        self.directory_scrollbar_x.pack(fill="x",side="bottom")
        self.directory_scrollbar_y.pack(fill="y",side="left")
        self.directory.bind('<ButtonRelease-1>',self.display_directory_selected_item)
        self.directory.pack(fill="both",expand=True)
        # 核心区域
        self.main_panel = ttk.Frame(self.frame)
        self.main_panel.pack(fill="both",expand=True)
        # 显示
        self.display_area = ttk.Treeview(self.main_panel,selectmode="browse",show="tree")
        self.display_area_scrollbar_x = ttk.Scrollbar(self.main_panel,orient=tk.HORIZONTAL,command=self.display_area.xview)
        self.display_area_scrollbar_y = ttk.Scrollbar(self.main_panel,orient=tk.VERTICAL,command=self.display_area.yview)
        self.display_area.configure(xscrollcommand=self.display_area_scrollbar_x.set)
        self.display_area.configure(yscrollcommand=self.display_area_scrollbar_y.set)
        self.display_area_scrollbar_x.pack(fill="x",side="bottom")
        self.display_area_scrollbar_y.pack(fill="y",side="right")
        self.display_area.bind('<ButtonRelease-1>',self.display_area_copy)
        self.display_area.pack(fill="both",expand=True)
        self.displaying = ""
        # 默认行高
        font_name = self.style.lookup("Treeview", "font")
        if not font_name:
            font_name = "TkDefaultFont"
        self.default_line_height = font.nametofont(font_name).metrics("linespace")
    
    # 定义目录物品类
    # 可选类型有：buff_template buff rogue_item
    class Item:
        def __init__(self,index,data_type,data_key,data_reference):
            self.data_type = data_type
            self.data_key = data_key
            self.data_reference = data_reference
            self.display_name = ""
            self.index = index
            if self.data_type == "buff_template":
                self.display_name = "[模板]"+data_key #待翻译
            elif self.data_type == "buff":
                self.display_name = "[Buff]"+data_key #待翻译
            elif self.data_type == "rogue_item":
                self.display_name = "["+data_reference.display_type+"]"+data_reference.display_name
            else:
                self.display_name = data_reference
        # 显示元素，带双向链接
        def view(self,tree_view):
            label = tree_view.insert("","end",text=self.display_name,values=(self.index))#,open=True
            
    # 读取列表
    # 支持的类型有 buff_template
    def load_directory(self,data_type,data_dict):
        for data_key,data_reference in data_dict.items():
            new_item = self.Item(self.directory_index,data_type,data_key,data_reference)
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
                    if keyword not in item.display_name and keyword not in item.data_key:
                        haskey = False
                        break
                if haskey:
                    item.view(self.directory)
            self.searching = True
                        
        #except:
        #    print("[量角器]尝试搜索，但是失败了。")
    
    # 展示选择查看的内容（使用安妮来翻译）
    def display_directory_selected_item(self,event=None):
        selected = self.directory.selection()
        if selected:
            linked_index = int(self.directory.item(selected[0],"values")[0])
            linked = self.directory_items[linked_index]
            if self.displaying != linked.data_key: #如果相同说明是同一个，不需要显示
                self.displaying = linked.data_key
                data = linked.data_reference
                if data:# 使用安妮进行翻译
                    if linked.data_type == "buff_template":
                        translation = anne.translate_whole_buff_template(data)
                        self.display(translation)
                    elif linked.data_type == "rogue_item":
                        translation = anne.translate_whole_rogue_item(data)
                        self.display(translation)
                    else: # 无法处理，那先尝试直接展示原文？
                        
                        if isinstance(data,dict) or isinstance(data,list):
                            self.display_raw(data)
    
    # 将结构体展示至展示区
    def display(self,struct,master=""):
        if master == "":
            self.display_area.set_children([])
        # 递归处理
        if "main" in struct:
            text = struct["main"]
            if text == None: # 空指针，直接返回
                return
            tree_open = True
            if "style_closed" in struct and struct["style_closed"]:
                tree_open = False
            if "true" in struct:
                text += f"，{struct['true']}："
            label = self.display_area.insert(master,"end",text=text,open=tree_open)
            if "description" in struct:
                self.display_area.insert(label,"end",text=f"（{struct['description']}）",open=tree_open)
            #self.display_area.rowheight(label, self.default_line_height * text.count('\n'))
            if "children" in struct:
                for child in struct["children"]:
                    self.display(child,label)
    
    # 将json数据展示至展示区，用于无法解析的情况
    def display_raw(self,datas,master=""):
        if master == "":
            self.display_area.set_children([])
        # 字典与列表将递归处理；剩下的按需返回
        if isinstance(datas,dict):
            for data_key,data_content in datas.items():
                if isinstance(data_content,dict):
                    label = self.display_area.insert(master,"end",text=data_key+" : {",open=True)
                    self.display_raw(data_content,label)
                    self.display_area.insert(master,"end",text="}")
                elif isinstance(data_content,list):
                    label = self.display_area.insert(master,"end",text=data_key+" : [",open=True)
                    self.display_raw(data_content,label)
                    self.display_area.insert(master,"end",text="]")
                elif isinstance(data_content,str):
                    self.display_area.insert(master,"end",text=data_key+" : \""+data_content+"\"")
                elif isinstance(data_content,bool):
                    state = "true" if data_content else "false"
                    self.display_area.insert(master,"end",text=data_key+" : "+state)
                else:
                    self.display_area.insert(master,"end",text=data_key+" : "+str(data_content))
        elif isinstance(datas,list):
            for data_content in datas:
                if isinstance(data_content,dict):
                    label = self.display_area.insert(master,"end",text="{",open=True)
                    self.display_raw(data_content,label)
                    self.display_area.insert(master,"end",text="}")
                elif isinstance(data_content,list):
                    label = self.display_area.insert(master,"end",text="[",open=True)
                    self.display_raw(data_content,label)
                    self.display_area.insert(master,"end",text="]")
                elif isinstance(data_content,str):
                    self.display_area.insert(master,"end",text="\""+data_content+"\"")
                elif isinstance(data_content,bool):
                    state = "true" if data_content else "false"
                    self.display_area.insert(master,"end",text=state)
                else:
                    self.display_area.insert(master,"end",text=str(data_content))
        elif isinstance(data_content,str):
            self.display_area.insert(master,"end",text="\""+data_content+"\"")
        elif isinstance(data_content,bool):
            state = "true" if data_content else "false"
            self.display_area.insert(master,"end",text=state)
        else:
            self.display_area.insert(master,"end",text=str(data_content))
        
    # 复制未翻译的内容（方便写翻译器用的）
    def display_area_copy(self,event=None):
        selected = self.display_area.selection()
        selected_text = self.display_area.item(selected)["text"]
        if " : " in selected_text:
            if selected_text.startswith("$type"):
                selected_text = selected_text.split(" : ")[1][28:-17] # 只要内容
            else:
                selected_text = selected_text.split(" : ")[0] # 只要变量名
            self.window.clipboard_clear()
            self.window.clipboard_append(selected_text)
            print("已复制："+selected_text)
        elif selected_text.endswith("（未翻译）"):
            selected_text = selected_text[:-5]
            self.window.clipboard_clear()
            self.window.clipboard_append(selected_text)
            print("已复制："+selected_text)
        
    # 开启界面
    def open(self):
        self.window.mainloop()
    
    # 关闭界面
    def close(self):
        self.window.destroy()

PROTRACTOR = Protractor()