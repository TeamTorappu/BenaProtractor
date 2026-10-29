"""IDE shell composed specifically for Bena: commands, documents and dock windows."""
import tkinter as tk
from tkinter import ttk, font
from vs_theme import COLORS, menu
from editor_views import TranslationView, SourceView
from dpi import DpiScale


class Workspace:
    def __init__(self, app):
        self.app = app
        root = app.window
        px = self.px = DpiScale(root)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)
        self.menus = ttk.Frame(root, style='Chrome.TFrame', padding=px(4, 0))
        self.menus.grid(row=0, column=0, sticky='ew')
        self.make_menus()
        tools = ttk.Frame(root, style='Chrome.TFrame', padding=px(4, 3))
        tools.grid(row=1, column=0, sticky='ew')
        app.back_button = ttk.Button(tools, text='←', width=3, style='Tool.TButton', command=lambda: app.go_history(-1), state='disabled')
        app.back_button.pack(side='left')
        app.forward_button = ttk.Button(tools, text='→', width=3, style='Tool.TButton', command=lambda: app.go_history(1), state='disabled')
        app.forward_button.pack(side='left')
        ttk.Separator(tools, orient='vertical').pack(side='left', fill='y', padx=px(6))
        app.update_button = ttk.Button(tools, text='↻  更新数据', style='Tool.TButton', command=app.refresh)
        app.update_button.pack(side='left')
        app.settings_button = ttk.Button(tools, text='选项', style='Tool.TButton', command=app.open_settings)
        app.settings_button.pack(side='left', padx=px(4, 0))
        ttk.Separator(tools, orient='vertical').pack(side='left', fill='y', padx=px(6))
        ttk.Button(tools, text='复制全文', style='Tool.TButton', command=app.copy_all).pack(side='left')
        ttk.Button(tools, text='展开', style='Tool.TButton', command=lambda: app.translation.expand_all()).pack(side='left')
        ttk.Button(tools, text='折叠', style='Tool.TButton', command=lambda: app.translation.expand_all(True)).pack(side='left')
        app.progress = ttk.Progressbar(tools, mode='determinate', length=px(90))
        app.progress.pack(side='right', padx=px(8))
        self.theme_choice = tk.StringVar(value='浅色' if app.settings['theme'] == 'light' else '深色')
        self.theme_picker = ttk.Combobox(tools, textvariable=self.theme_choice, state='readonly', values=['浅色', '深色'], width=5)
        self.theme_picker.pack(side='right', padx=px(5))
        self.theme_picker.bind('<<ComboboxSelected>>', lambda event: app.change_theme('light' if self.theme_choice.get() == '浅色' else 'dark'))
        ttk.Label(tools, text='主题', style='Chrome.TLabel').pack(side='right')

        self.vertical = ttk.Panedwindow(root, orient='vertical')
        self.vertical.grid(row=2, column=0, sticky='nsew', padx=px(4))
        self.horizontal = ttk.Panedwindow(self.vertical, orient='horizontal')
        self.vertical.add(self.horizontal, weight=1)
        document = ttk.Frame(self.horizontal, style='Editor.TFrame')
        self.horizontal.add(document, weight=1)
        document.columnconfigure(0, weight=1)
        document.rowconfigure(1, weight=1)
        navigation = ttk.Frame(document, style='Chrome.TFrame', padding=px(7, 4))
        navigation.grid(row=0, column=0, sticky='ew')
        app.breadcrumb = ttk.Label(navigation, text='', style='Chrome.TLabel')
        app.breadcrumb.pack(side='left')
        app.key_label = ttk.Label(navigation, text='', style='Chrome.TLabel')
        app.key_label.pack(side='left', padx=px(10))
        app.main_panel = ttk.Notebook(document)
        app.main_panel.grid(row=1, column=0, sticky='nsew')
        app.translation = TranslationView(app.main_panel, app.navigate, size=app.settings['font_size'])
        app.source = SourceView(app.main_panel, size=app.settings['font_size'])
        app.main_panel.add(app.translation, text='中文伪代码')
        app.main_panel.add(app.source, text='原始代码')

        self.explorer_width = round(320 * font.nametofont('TkDefaultFont').metrics('linespace') / 19)
        self.explorer = ttk.Frame(self.horizontal, width=self.explorer_width)
        self.horizontal.add(self.explorer, weight=0)
        self.explorer.columnconfigure(0, weight=1)
        self.explorer.rowconfigure(4, weight=1)
        ttk.Label(self.explorer, text='数据资源管理器', style='Dock.TLabel').grid(row=0, column=0, sticky='ew')
        search = ttk.Frame(self.explorer, padding=px(5, 5))
        search.grid(row=1, column=0, sticky='ew')
        search.columnconfigure(1, weight=1)
        ttk.Label(search, text='搜索').grid(row=0, column=0, padx=px(0, 5))
        app.search_var = tk.StringVar()
        app.search_entry = ttk.Entry(search, textvariable=app.search_var, width=18)
        app.search_entry.grid(row=0, column=1, sticky='ew')
        app.search_var.trace_add('write', app.queue_search)
        app.filter_var = tk.StringVar(value='全部 table')
        app.filter = ttk.Combobox(self.explorer, textvariable=app.filter_var, state='readonly', values=['全部 table'], width=22)
        app.filter.grid(row=2, column=0, sticky='ew', padx=px(5), pady=px(0, 5))
        app.filter.bind('<<ComboboxSelected>>', app.try_search)
        app.count_label = ttk.Label(self.explorer, text='0 条目', style='Muted.TLabel', padding=px(6, 2))
        app.count_label.grid(row=3, column=0, sticky='ew')
        listing = ttk.Frame(self.explorer)
        listing.grid(row=4, column=0, sticky='nsew')
        listing.rowconfigure(0, weight=1)
        listing.columnconfigure(0, weight=1)
        app.directory = ttk.Treeview(listing, show='tree', selectmode='browse')
        app.directory.column('#0', width=px(270), minwidth=px(140), stretch=True)
        app.directory.grid(row=0, column=0, sticky='nsew')
        vertical = ttk.Scrollbar(listing, orient='vertical', command=app.directory.yview)
        horizontal = ttk.Scrollbar(listing, orient='horizontal', command=app.directory.xview)
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        app.directory.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        app.directory.bind('<<TreeviewSelect>>', app.display_directory_selected_item)
        ttk.Label(self.explorer, text='属性', style='Dock.TLabel').grid(row=5, column=0, sticky='ew', pady=px(4, 0))
        app.properties = ttk.Treeview(self.explorer, columns=('value',), show='tree', height=4, selectmode='none')
        app.properties.column('#0', width=px(68), minwidth=px(55), stretch=False)
        app.properties.column('value', width=px(205), minwidth=px(100), stretch=True)
        app.properties.grid(row=6, column=0, sticky='ew')

        self.output = ttk.Frame(self.vertical, height=px(115))
        header = ttk.Frame(self.output, style='Chrome.TFrame')
        header.pack(fill='x')
        ttk.Label(header, text='输出', style='Dock.TLabel').pack(side='left')
        ttk.Button(header, text='×', width=3, style='Tool.TButton', command=self.toggle_output).pack(side='right')
        self.output_text = tk.Text(self.output, height=4, bg=COLORS['editor'], fg=COLORS['text'],
                                   font=('Consolas', 10), relief='flat', borderwidth=0, padx=px(8), pady=px(4), state='disabled', wrap='word')
        self.output_text.pack(fill='both', expand=True)
        self.output_visible = False
        self.explorer_visible = True

        status = tk.Frame(root, bg=COLORS['status'], height=px(24))
        status.grid(row=3, column=0, sticky='ew')
        status.columnconfigure(0, weight=1)
        app.status = tk.StringVar(value='就绪')
        app.status_label = tk.Label(status, textvariable=app.status, bg=COLORS['status'], fg='white', anchor='w', padx=px(7), pady=px(3))
        app.status_label.grid(row=0, column=0, sticky='ew')
        tk.Label(status, text='只读    UTF-8    JSON', bg=COLORS['status'], fg='white', padx=px(12)).grid(row=0, column=1)
        app.status.trace_add('write', self.record_status)
        self._last_message = ''
        root.after_idle(self.position_panes)

    def position_panes(self):
        if self.explorer_visible:
            width = self.horizontal.winfo_width()
            if width > self.px(600):
                sidebar = min(self.explorer_width, int(width * 0.38))
                self.horizontal.sashpos(0, width - sidebar)

    def apply_metrics(self):
        self.explorer_width = round(320 * font.nametofont('TkDefaultFont').metrics('linespace') / 19)
        self.explorer.configure(width=self.explorer_width)
        self.app.window.after_idle(self.position_panes)

    def make_menus(self):
        app = self.app
        px = self.px
        commands = {
            '文件(F)': [('复制 ID', app.copy_id, ''), ('退出', app.close, 'Alt+F4')],
            '编辑(E)': [('复制全文', app.copy_all, ''), ('搜索', app.focus_search, 'Ctrl+F')],
            '视图(V)': [('中文伪代码', lambda: app.select_view(0), ''), ('原始代码', lambda: app.select_view(1), ''), None,
                         ('数据资源管理器', self.toggle_explorer, ''), ('输出', self.toggle_output, '')],
            '工具(T)': [('更新数据', app.refresh, 'F5'), ('数据历史与差异', app.open_table_history, ''), ('选项', app.open_settings, '')],
        }
        for label, items in commands.items():
            button = tk.Menubutton(self.menus, text=label, bg=COLORS['panel'], fg=COLORS['text'],
                                   activebackground=COLORS['hover'], activeforeground=COLORS['text'], relief='flat', padx=px(8), pady=px(4), font='TkMenuFont')
            dropdown = menu(button)
            for item in items:
                if item is None:
                    dropdown.add_separator()
                else:
                    text, callback, shortcut = item
                    dropdown.add_command(label=text, command=callback, accelerator=shortcut)
            button.configure(menu=dropdown)
            button.pack(side='left')

    def toggle_output(self):
        if self.output_visible:
            self.vertical.forget(self.output)
        else:
            self.vertical.add(self.output, weight=0)
            self.app.window.after_idle(lambda: self.vertical.sashpos(0, max(self.px(250), self.vertical.winfo_height() - self.px(120))))
        self.output_visible = not self.output_visible

    def toggle_explorer(self):
        if self.explorer_visible:
            self.horizontal.forget(self.explorer)
        else:
            self.horizontal.add(self.explorer, weight=0)
            # Finish reattaching the pane before restoring its sash position.
            self.horizontal.update_idletasks()
        self.explorer_visible = not self.explorer_visible
        self.position_panes()

    def record_status(self, *args):
        value = self.app.status.get()
        if value == self._last_message:
            return
        self._last_message = value
        self.output_text.configure(state='normal')
        self.output_text.insert('end', value + '\n')
        if int(self.output_text.index('end-1c').split('.')[0]) > 500:
            self.output_text.delete('1.0', '100.0')
        self.output_text.see('end')
        self.output_text.configure(state='disabled')

    def set_document(self, entry):
        app = self.app
        app.window.title(f'{entry.name} - 贝娜的量角器')
        files = {'buff': 'buff_table.json', 'buff_template': 'buff_template_data.json',
                 'global_buff': 'global_buff_dummy.json', 'rogue_item': 'roguelike_topic_table.json'}
        app.breadcrumb.configure(text=files[entry.category])
        app.key_label.configure(text='›  ' + entry.key)
        children = app.properties.get_children()
        if children:
            app.properties.delete(*children)
        template = getattr(entry.obj, 'buff_data', {}).get('templateKey', '')
        for key, value in [('名称', entry.name), ('ID', entry.key), ('Table', entry.table), ('模板', template)]:
            app.properties.insert('', 'end', text=key, values=(value,))

    def apply_palette(self):
        def recolor(widget):
            if isinstance(widget, tk.Menubutton):
                widget.configure(bg=COLORS['panel'], fg=COLORS['text'], activebackground=COLORS['hover'], activeforeground=COLORS['text'])
            elif isinstance(widget, tk.Menu):
                widget.configure(bg=COLORS['panel'], fg=COLORS['text'], activebackground=COLORS['selection'], activeforeground=COLORS['selected_text'])
            for child in widget.winfo_children():
                recolor(child)
        recolor(self.menus)
        self.output_text.configure(bg=COLORS['editor'], fg=COLORS['text'])
        self.theme_choice.set('浅色' if self.app.settings['theme'] == 'light' else '深色')
        for widget in (self.theme_picker, self.app.filter):
            dropdown = widget.tk.call('ttk::combobox::PopdownWindow', str(widget))
            widget.tk.call(dropdown + '.f.l', 'configure', '-background', COLORS['field'],
                           '-foreground', COLORS['text'], '-selectbackground', COLORS['selection'],
                           '-selectforeground', COLORS['selected_text'], '-font', 'TkTextFont')
