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
        self.window.geometry("1000x800")
        self.window.title('贝娜的量角器')
        self.style = ttk.Style()
        self.frame = ttk.Frame(self.window, padding=10)
        self.frame.pack(fill="both",expand=True)
        # 控制区域
        self.control_panel = ttk.Frame(self.frame,width=500)
        self.control_panel.pack(fill="y",side="left")
        # 顶边菜单
        self.menu_bar = tk.Menu(self.window)
        self.window.config(menu=self.menu_bar)
        self.menu_load = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="加载", menu=self.menu_load)
        self.menu_load.add_command(label="Buff模板")
        # 目录
        self.directory_items = []
        self.directory_index = 0 # 用于为每个目录编号
        self.search_frame = tk.Frame(self.control_panel)
        self.search_frame.pack(fill="x",side="top")
        self.search_button = ttk.Button(self.search_frame,text="搜索",command=self.try_search,width=4,padding=-1)
        self.search_button.pack(side="right")
        self.search_entry = ttk.Entry(self.search_frame)
        self.search_entry.bind("<Return>", self.try_search)
        self.search_entry.pack(fill="both")
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
        self.display_area.column(f"#0", stretch=True)
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
        keywords = self.search_entry.get().strip().split(" ")
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
    
    # 搜索特定内容
    def search_by(self,things):
        self.search_entry.delete(0,"end")
        self.search_entry.insert("end",str(things))
        self.try_search()
    
    # 展示选择查看的内容（使用安妮来翻译）
    def display_directory_selected_item(self,event=None):
        selected = self.directory.selection()
        if selected:
            linked_index = int(self.directory.item(selected[0],"values")[0])
            linked = self.directory_items[linked_index]
            full_key = linked.data_type + "." + linked.data_key
            #如果相同说明是同一个，不需要显示
            if self.displaying == full_key:
                return
            self.displaying = full_key
            if not linked.data_reference:
                return
            obj = linked.data_reference
            translation = None
            # 使用安妮进行翻译
            if linked.data_type == "buff":
                translation = anne.translate_whole_buff(obj)
                self.display(translation)
                self.display_origin("\"" + obj.buff_key + "\" :" + obj.raw_buff_data) 
            elif linked.data_type == "buff_template":
                translation = anne.translate_whole_buff_template(obj)
                self.display(translation)
                self.display_origin("\"" + obj.buff_key + "\" :" + obj.raw_buff_data) 
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
        translation = None
        _cat = ""
        # 前缀模式？尝试匹配
        if "." in item_id:
            item_ids = item_id.split(".",1)
            _cat = item_ids[0]
            item_id = item_ids[1]
        # 逐个匹配
        # 优先搜索肉鸽物品
        if (_cat in ["","rogue_item"]) and item_id in bena.ROGUELIKE_TOPIC_KEYS:
            translation = anne.translate_whole_rogue_item(bena.ROGUELIKE_TOPIC_TABLE[item_id])
        elif (_cat in ["","buff"]) and item_id in bena.BUFF_KEYS:
            translation = anne.translate_whole_buff(bena.BUFF_TABLE[item_id])
        elif (_cat in ["","buff_template"]) and item_id in bena.BUFF_TEMPLATE_KEYS:
            translation = anne.translate_whole_buff_template(bena.BUFF_TEMPLATE_DATA[item_id])
        # 如果找到了翻译，返回之
        if translation != None:
            self.display(translation)
            return True
        # 如果找不到...
        return False
    
    # 将结构体展示至展示区
    def display(self,struct,master=""):
        if master == "":
            self.display_links = {}
            self.display_area.set_children([])
        # 递归处理
        if isinstance(struct,dict) and "main" in struct:
            text = struct.get("main","")
            link = struct.get("link","")
            if text == None: # 空指针，直接返回
                return
            # 默认开启，可以改为关闭
            tree_open = True
            if "style_closed" in struct and struct["style_closed"]:
                tree_open = False
            # 真值结果，如果留到这一步，说明只有可以缩写
            if "true" in struct and struct['true'] != "":
                if len(text) == 0:
                    text = f"{struct['true']}："
                else:
                    text += f"，{struct['true']}："
            # buff名处理
            if "<" in text and ">" in text:
                text = bena.translate_buff_name_in_text(text)
            label = self.display_area.insert(master,"end",text=text,open=tree_open,values=(link))
            if "description" in struct and struct['description'] != "":
                description = struct["description"]
                if "<" in description and ">" in description:
                    description = bena.translate_buff_name_in_text(description)
                self.display_area.insert(label,"end",text=f"（{description}）",open=tree_open)
            #self.display_area.rowheight(label, self.default_line_height * text.count('\n'))
            # 嵌套循环
            if "children" in struct:
                for child in struct["children"]:
                    self.display(child,label)
        elif isinstance(struct,list): # 列表？为什么会是个列表？
            for child in struct:
                self.display(child,master)
        else: # 纯文本之类的？
            label = self.display_area.insert(master,"end",text=str(struct),values=(""))

    
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
                links = selected_link.split(",")
                for link in links:
                    context_menu.add_command(label="转跳到至 "+link, command=lambda: self.display_by_id(link))
                    if "." in link:
                        search_key = link.split(".",1)[1]
                        context_menu.add_command(label="搜索 "+search_key, command=lambda: self.search_by(search_key))
                    else:
                        context_menu.add_command(label="搜索 "+link, command=lambda: self.search_by(link))
                    context_menu.add_separator()
            # 复制文本
            context_menu.add_command(label="复制整行", command=lambda: self.copy(selected_text))
            copy_keys = []
            if ":" in selected_text: # 如果是 A : B 的json格式，选择复制前后哪边
                keys = [key.strip() for key in selected_text.split(":")]
                if keys[1].startswith("$type"):  # 只要内容，不要Node的那一大段
                    keys[1] = keys[1][28:-17]
                copy_keys.append(keys[0])
                copy_keys.append(keys[1])
            elif "：" in selected_text: # 如果是 A : B 的json格式，选择复制前后哪边
                keys = [key.strip() for key in selected_text.split("：")]
                copy_keys.append(keys[0])
                copy_keys.append(keys[1])
            elif "（" in selected_text and selected_text.endswith("）"): # 如果是 A（B） 的括号格式，选择复制前后哪边
                keys = [key.strip() for key in selected_text.split("（")]
                keys[1] = keys[1][:-1].strip()
                copy_keys.append(keys[0])
                copy_keys.append(keys[1])
            for copy_key in copy_keys:
                if copy_key not in ["","未翻译","$type"]:
                    context_menu.add_command(label="复制 " + copy_key, command=lambda key=copy_key: self.copy(key))
            # 分割线
            context_menu.add_separator()
            # 复制全文
            context_menu.add_command(label="复制全文", command=lambda: self.copy_all())
            context_menu.post(event.x_root, event.y_root)
    
    # 复制文本
    def copy(self,given_text):
        self.window.clipboard_clear()
        self.window.clipboard_append(given_text)
        print("已复制："+given_text)

    # 复制全部文本
    def copy_all(self):
        data = []
        def get_label(label,depth = 0):
            text = self.display_area.item(label,"text")
            data.append(("    " * depth) + text)
            for child in self.display_area.get_children(label):
                get_label(child,depth+1)
        for label in self.display_area.get_children():
            get_label(label)
        self.window.clipboard_clear()
        self.window.clipboard_append("\n".join(data))
        print("已复制全部翻译文本")
            
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