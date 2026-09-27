'''
tkinter 版「选择要加载的内容」对话框（备用后端）
行为与原 main.py 里的 Selector 保持一致，只是改成可以返回值、可复用。
'''
import tkinter as tk

import bootstrap


class TkSelector:
    def __init__(self,parent=None,current=None):
        self.result = None
        self.root = tk.Toplevel(parent) if parent is not None else tk.Tk()
        self.root.title("选择要加载的内容")
        tk.Label(self.root,text="请选择要加载的内容：").pack()
        self.frame = tk.Frame(self.root,bg="#FFFFFF")
        self.vars = []
        checked = current if current else bootstrap.DEFAULT_LOAD
        for type,title in bootstrap.all_load_types().items():
            var = tk.StringVar()
            if type in checked:
                var.set(type)
            tk.Checkbutton(self.frame,text=title,variable=var,onvalue=type,offvalue="",
                           bg="#FFFFFF",anchor="w").pack()
            self.vars.append(var)
        self.frame.pack(fill="x")
        self.remember = tk.BooleanVar()
        self.remember.set(True)
        tk.Checkbutton(self.root, text="记住选择", variable=self.remember,
                       onvalue=True, offvalue=False).pack(fill="x")
        tk.Button(self.root, text="贝娜！部署！", command=self.confirm).pack()

    # 确认
    def confirm(self):
        loads = []
        for var in self.vars:
            value = var.get()
            if value != "":
                loads.append(value)
        if self.remember.get():
            bootstrap.save_cache(loads)
        self.result = loads
        self.root.destroy()

    # 阻塞直到对话框关闭；返回 loads 列表或 None（取消）
    def exec(self):
        # 用户直接点右上角关闭：视为取消
        self.root.protocol("WM_DELETE_WINDOW",self.cancel)
        try:
            self.root.grab_set()
        except tk.TclError:
            pass
        self.root.wait_window()
        return self.result

    def cancel(self):
        self.result = None
        self.root.destroy()
