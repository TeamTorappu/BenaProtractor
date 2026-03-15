'''
量角器 - UI
'''
import tkinter as tk
from tkinter import ttk
from tkinter import font
import os
import json
import bena
import anne

os.environ['PYTHONWARNINGS'] = 'ignore:libpng warning:'
PROTRACTOR = None

# 定义UI主类
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
        self.main_panel = ttk.Notebook(self.frame)
        self.main_panel.pack(fill="both",expand=True)
        # 译文区
        self.display_panel = ttk.Frame(self.main_panel)
        self.main_panel.add(self.display_panel, text="译文")
        self.display_links = {}
        self.display_area = Displayview(self.display_panel,selectmode="browse",show="tree")
        # 滚动条
        self.display_area_scrollbar_x = ttk.Scrollbar(self.display_panel,orient=tk.HORIZONTAL,command=self.display_area.xview)
        self.display_area_scrollbar_y = ttk.Scrollbar(self.display_panel,orient=tk.VERTICAL,command=self.display_area.yview)
        self.display_area.configure(xscrollcommand=self.display_area_scrollbar_x.set)
        self.display_area.configure(yscrollcommand=self.display_area_scrollbar_y.set)
        self.display_area_scrollbar_x.pack(fill="x",side="bottom")
        self.display_area_scrollbar_y.pack(fill="y",side="right")
        # 点击事件
        self.display_area.bind('<Button-1>',self.display_area_left_clicked)
        self.display_area.bind('<Button-3>',self.display_area_right_clicked)
        self.display_area.pack(fill="both",expand=True)
        self.displaying = ""
        # 原文区
        self.origin_panel = ttk.Frame(self.main_panel)
        self.main_panel.add(self.origin_panel, text="原文")
        self.origin_area = tk.Text(self.origin_panel,bg="#1F1F1F",fg="#9CDCF0")
        # 滚动条
        self.origin_area_scrollbar_x = ttk.Scrollbar(self.origin_panel,orient=tk.HORIZONTAL,command=self.origin_area.xview)
        self.origin_area_scrollbar_y = ttk.Scrollbar(self.origin_panel,orient=tk.VERTICAL,command=self.origin_area.yview)
        self.origin_area.configure(xscrollcommand=self.origin_area_scrollbar_x.set)
        self.origin_area.configure(yscrollcommand=self.origin_area_scrollbar_y.set)
        self.origin_area_scrollbar_x.pack(fill="x",side="bottom")
        self.origin_area_scrollbar_y.pack(fill="y",side="right")
        self.origin_area.pack(fill="both",expand=True)
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
                self.display_name = "[模板]"+data_reference.display_name
            elif self.data_type == "buff":
                self.display_name = "[Buff]"+data_reference.display_name
            elif self.data_type == "rogue_item":
                self.display_name = "["+data_reference.display_type+"]"+data_reference.display_name
            else:
                self.display_name = data_reference
        # 显示元素，带双向链接
        def view(self,tree_view):
            label = tree_view.insert("","end",text=self.display_name,values=(self.index))#,open=True
            
    # 读取列表
    def load_directory(self,data_type,data_dict):
        for data_key,data_reference in data_dict.items():
            if not data_reference.hidden: # 隐藏的不加入列表
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
                item.view(self.directory)
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
                obj = linked.data_reference
                if obj:
                    # 使用安妮进行翻译
                    if linked.data_type == "buff_template":
                        translation = anne.translate_whole_buff_template(obj)
                        self.display(translation)
                        self.display_origin(obj.raw_buff_data) 
                    elif linked.data_type == "rogue_item":
                        translation = anne.translate_whole_rogue_item(obj)
                        self.display(translation)
                        if obj.has_effect:
                            self.display_origin([obj.item_info,obj.item_data])
                        else:
                            self.display_origin(obj.item_info)
                    else: # 无法处理，那先尝试直接展示优化的原文？
                        if isinstance(obj,dict) or isinstance(obj,list):
                            self.display_raw(obj)
                            self.display_origin(obj)
    
    # 展示特定ID的内容（使用贝娜获取数据，然后由安妮来翻译）
    def display_by_id(self,item_id=""):
        # 优先搜索肉鸽物品
        if item_id in bena.ROGUELIKE_TOPIC_KEYS:
            data = bena.ROGUELIKE_TOPIC_TABLE[item_id]
            translation = anne.translate_whole_rogue_item(data)
            self.display(translation)
        elif item_id in bena.BUFF_TEMPLATE_KEYS:
            data = bena.BUFF_TEMPLATE_DATA[item_id]
            translation = anne.translate_whole_rogue_item(data)
            self.display(translation)
    
    # 将结构体展示至展示区
    def display(self,struct,master=""):
        if master == "":
            self.display_links = {}
            self.display_area.set_children([])
        # 递归处理
        if "main" in struct:
            text = struct.get("main","")
            link = struct.get("link","")
            if text == None: # 空指针，直接返回
                return
            # 默认开启，可以改为关闭
            tree_open = True
            if "style_closed" in struct and struct["style_closed"]:
                tree_open = False
            # 真值结果，如果留到这一步，说明只有可以缩写
            if "true" in struct:
                text += f"，{struct['true']}："
            label = self.display_area.insert(master,"end",text=text,open=tree_open,values=(link))
            if "description" in struct:
                self.display_area.insert(label,"end",text=f"（{struct['description']}）",open=tree_open)
            #self.display_area.rowheight(label, self.default_line_height * text.count('\n'))
            if "children" in struct:
                for child in struct["children"]:
                    self.display(child,label)
        elif isinstance(struct,list): # 列表？为什么会是个列表？
            for child in struct:
                self.display(child,master)
        else: # 纯文本之类的？
            label = self.display_area.insert(master,"end",text=str(struct),open=tree_open,values=(""))

    
    # 将json数据展示至展示区，用于无法解析的情况
    def display_raw(self,datas,master=""):
        if master == "":
            self.display_links = {}
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
    
    # 将原文展示至展示区
    def display_origin(self,data_dict_or_dicts):
        self.origin_area.delete("1.0", "end")
        if isinstance(data_dict_or_dicts,list):
            data_strs = []
            for data_dict in data_dict_or_dicts:
                data_strs.append(json.dumps(data_dict,indent=4,ensure_ascii=False))
            self.origin_area.insert("end",",\n".join(data_strs))
        elif isinstance(data_dict_or_dicts,dict):
            data_str = json.dumps(data_dict_or_dicts,indent=4,ensure_ascii=False)
            self.origin_area.insert("end",data_str)
        else: # 尝试直接显示
            self.origin_area.insert("end",data_dict_or_dicts)

    # 显示区域的左键点击事件
    def display_area_left_clicked(self,event=None):
        # 获取所选
        selected = self.display_area.selection()
        if selected == None:
            return
        selected_text = self.display_area.item(selected,"text")
        selected_values = self.display_area.item(selected,"values")
        selected_link = selected_values[0] if len(selected_values) > 0 else ""
    
    # 显示区域的右键点击事件
    def display_area_right_clicked(self,event=None):
        # 获取所选
        #selected = self.display_area.selection()
        selected = self.display_area.identify_row(event.y)
        if selected == None:
            return
        self.display_area.focus(selected)
        selected_text = self.display_area.item(selected,"text")
        selected_values = self.display_area.item(selected,"values")
        selected_link = selected_values[0] if len(selected_values) > 0 else ""
        if selected_text != "":# 显示右键菜单
            context_menu = tk.Menu(self.window, tearoff=0)
            # 转跳
            if len(selected_link) != None and selected_link != "":
                context_menu.add_command(label="转跳到至 "+selected_link, command=lambda: self.display_by_id(selected_link))
            # 复制文本
            context_menu.add_command(label="复制", command=lambda: self.copy_selection(selected_text))
            if ":" in selected_text: # 如果是 A : B 的json格式，选择复制前后哪边
                keys = [key.strip() for key in selected_text.split(":")]
                if keys[1].startswith("$type"):  # 只要内容，不要Node的那一大段
                    keys[1] = keys[1][28:-17]
                context_menu.add_command(label="复制Key", command=lambda: self.copy_selection(keys[0]))
                context_menu.add_command(label="复制Value", command=lambda: self.copy_selection(keys[1]))
            elif selected_text.endswith("（未翻译）"): # 复制未翻译文本
                context_menu.add_command(label="复制未翻译文本", command=lambda: self.copy_selection(selected_text[:-5]))
            elif "（" in selected_text and selected_text.endswith("）"): # 如果是 A（B） 的括号格式，选择复制前后哪边
                keys = [key.strip() for key in selected_text.split("（")]
                keys[1] = keys[1][:-1].strip()
                context_menu.add_command(label="复制前半内容", command=lambda: self.copy_selection(keys[0]))
                context_menu.add_command(label="复制括号内内容", command=lambda: self.copy_selection(keys[1]))
            context_menu.post(event.x_root, event.y_root)
    
    # 复制所选条目整个文本
    # 开发用功能，方便写翻译器用的
    def copy_selection(self,given_text):
        self.window.clipboard_clear()
        self.window.clipboard_append(given_text)
        print("已复制："+given_text)
            
    # 开启界面
    def open(self):
        self.window.mainloop()
    
    # 关闭界面
    def close(self):
        self.window.destroy()

# 定义显示区域的自制TreeView类
class Displayview(ttk.Treeview):
    def __init__(self,master,*args,**kwargs):
        super(Displayview,self).__init__(master,*args,**kwargs)

PROTRACTOR = Protractor()