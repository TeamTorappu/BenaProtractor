"""IDE-style options dialog with navigation categories and fixed actions."""
import time
import tkinter as tk
from tkinter import ttk, font
from app_settings import LOAD_TYPES, normalize_settings
from downloader import read_metadata
from app_settings import DEFAULT_SOURCE, SOURCE_LABELS
from vs_theme import COLORS, style_titlebar
from dpi import DpiScale


class Preferences(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.window)
        self.app = app
        px = self.px = DpiScale(self)
        self.title('选项')
        self.configure(bg=COLORS['panel'])
        scale = font.nametofont('TkDefaultFont').metrics('linespace') / 19
        width = min(round(760 * scale), max(1, self.winfo_screenwidth() - px(64)))
        height = min(round(560 * scale), max(1, self.winfo_screenheight() - px(96)))
        left = min(max(0, app.window.winfo_x() + (app.window.winfo_width() - width) // 2), self.winfo_screenwidth() - width)
        top = min(max(0, app.window.winfo_y() + (app.window.winfo_height() - height) // 2), self.winfo_screenheight() - height - px(64))
        self.geometry(f'{width}x{height}+{left}+{max(0, top)}')
        self.minsize(min(width, px(680)), height)
        self.transient(app.window)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.navigation = ttk.Treeview(self, show='tree', selectmode='browse', height=8)
        self.navigation.column('#0', width=px(140), minwidth=px(20), stretch=False)
        self.navigation.grid(row=0, column=0, sticky='ns', padx=px(8, 4), pady=px(8))
        self.pages = {}
        self.content = ttk.Frame(self, padding=px(15))
        self.content.grid(row=0, column=1, sticky='nsew', padx=px(0, 8), pady=px(8))
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)
        for key, name in [('environment', '环境'), ('tables', '数据 table'), ('updates', '数据更新')]:
            self.navigation.insert('', 'end', iid=key, text=name)
            page = ttk.Frame(self.content)
            page.grid(row=0, column=0, sticky='nsew')
            self.pages[key] = page
        self.navigation.bind('<<TreeviewSelect>>', self.select_page)
        self.theme = tk.StringVar(value='浅色' if app.settings['theme'] == 'light' else '深色')
        self.size = tk.StringVar(value=str(app.settings['font_size']))
        self.ui_size = tk.StringVar(value=str(app.settings['ui_font_size']))
        self.hidden = tk.BooleanVar(value=app.settings['show_hidden'])
        self.auto = tk.BooleanVar(value=app.settings['auto_update'])
        self.hours = tk.StringVar(value=str(app.settings['update_hours']))
        self.source = tk.StringVar(value=SOURCE_LABELS[app.settings['download_source']])
        self.tables = {key: tk.BooleanVar(value=key in app.settings['tables']) for key in LOAD_TYPES}
        self.build_environment()
        self.build_tables()
        self.build_updates()
        actions = ttk.Frame(self, padding=px(10, 8))
        actions.grid(row=1, column=0, columnspan=2, sticky='ew')
        self.error = ttk.Label(actions, text='', foreground=COLORS['red'], wraplength=px(400))
        self.error.pack(side='left')
        ttk.Button(actions, text='取消', command=self.destroy, width=9).pack(side='right')
        ttk.Button(actions, text='确定', style='Primary.TButton', command=self.apply, width=9).pack(side='right', padx=px(8))
        self.navigation.selection_set('environment')
        self.select_page()
        self.bind('<Escape>', lambda event: self.destroy())
        self.bind('<Return>', lambda event: self.apply())
        style_titlebar(self, app.settings['theme'])
        self.grab_set()

    def build_environment(self):
        px = self.px
        page = self.pages['environment']
        ttk.Label(page, text='环境', font=('Microsoft YaHei UI', 11, 'bold')).grid(row=0, column=0, sticky='w', pady=px(0, 20))
        ttk.Label(page, text='颜色主题').grid(row=1, column=0, sticky='w', padx=px(0, 20), pady=px(8))
        ttk.Combobox(page, state='readonly', textvariable=self.theme, values=['浅色', '深色'], width=16).grid(row=1, column=1, sticky='w')
        ttk.Label(page, text='界面字号').grid(row=2, column=0, sticky='w', pady=px(8))
        ttk.Spinbox(page, from_=9, to=12, textvariable=self.ui_size, width=7).grid(row=2, column=1, sticky='w')
        ttk.Label(page, text='阅读字号').grid(row=3, column=0, sticky='w', pady=px(8))
        ttk.Spinbox(page, from_=10, to=18, textvariable=self.size, width=7).grid(row=3, column=1, sticky='w')

    def build_tables(self):
        px = self.px
        page = self.pages['tables']
        ttk.Label(page, text='显示的 table', font=('Microsoft YaHei UI', 11, 'bold')).pack(anchor='w', pady=px(0, 12))
        for key, label in LOAD_TYPES.items():
            ttk.Checkbutton(page, text=label, variable=self.tables[key]).pack(anchor='w')
        ttk.Separator(page).pack(fill='x', pady=px(10))
        ttk.Checkbutton(page, text='显示隐藏条目', variable=self.hidden).pack(anchor='w')

    def build_updates(self):
        px = self.px
        page = self.pages['updates']
        ttk.Label(page, text='游戏数据更新', font=('Microsoft YaHei UI', 11, 'bold')).pack(anchor='w', pady=px(0, 16))
        ttk.Checkbutton(page, text='自动检查更新', variable=self.auto).pack(anchor='w')
        row = ttk.Frame(page)
        row.pack(fill='x', pady=px(12))
        ttk.Label(row, text='检查间隔（小时）').pack(side='left', padx=px(0, 15))
        ttk.Spinbox(row, from_=1, to=168, textvariable=self.hours, width=7).pack(side='left')
        source_row = ttk.Frame(page)
        source_row.pack(fill='x', pady=px(8))
        ttk.Label(source_row, text='下载源').pack(side='left', padx=px(0, 15))
        self.source_picker = ttk.Combobox(source_row, state='readonly', textvariable=self.source,
                                         values=list(SOURCE_LABELS.values()), width=16)
        self.source_picker.pack(side='left')
        self.source_picker.bind('<<ComboboxSelected>>', self.update_checked)
        self.checked_label = ttk.Label(page, style='Muted.TLabel')
        self.checked_label.pack(anchor='w')
        self.update_checked()

    def update_checked(self, event=None):
        try:
            metadata = read_metadata()
            selected = next(key for key, label in SOURCE_LABELS.items() if label == self.source.get())
            checked = metadata.get('checked_at') if metadata.get('source', DEFAULT_SOURCE) == selected else None
            checked = time.strftime('%Y-%m-%d %H:%M', time.localtime(float(checked))) if checked else '未检查'
        except (TypeError, ValueError, OverflowError):
            checked = '未检查'
        self.checked_label.configure(text='上次检查：' + checked)

    def select_page(self, event=None):
        selected = self.navigation.selection()
        if selected:
            self.pages[selected[0]].tkraise()

    def apply(self):
        try:
            hours, size, ui_size = int(self.hours.get()), int(self.size.get()), int(self.ui_size.get())
            if not 1 <= hours <= 168 or not 10 <= size <= 18 or not 9 <= ui_size <= 12:
                raise ValueError
        except ValueError:
            self.error.configure(text='检查间隔：1–168；界面字号：9–12；阅读字号：10–18。')
            return
        candidate = normalize_settings({'tables': [key for key, variable in self.tables.items() if variable.get()],
                                        'theme': 'light' if self.theme.get() == '浅色' else 'dark',
                                        'font_size': size, 'ui_font_size': ui_size, 'show_hidden': self.hidden.get(),
                                        'download_source': next(key for key, label in SOURCE_LABELS.items() if label == self.source.get()),
                                        'auto_update': self.auto.get(), 'update_hours': hours})
        try:
            self.app.apply_settings(candidate)
        except OSError as error:
            self.error.configure(text=str(error))
            return
        self.destroy()
