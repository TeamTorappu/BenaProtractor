"""Read-only table history browser, independent of document translation."""
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

from dpi import DpiScale
from editor_views import TextPane
from table_history import compare_snapshot, list_snapshots, snapshot_time
from vs_theme import COLORS, style_titlebar


class TableHistory(tk.Toplevel):
    def __init__(self, app, directory=None):
        super().__init__(app.window)
        self.app, self.directory = app, directory
        self.versions, self.changes = [], []
        self.generation = 0
        self.messages = queue.Queue()
        self.title('数据历史与差异')
        self.transient(app.window)
        px = DpiScale(self)
        width = min(px(1100), max(1, self.winfo_screenwidth() - px(64)))
        height = min(px(760), max(1, self.winfo_screenheight() - px(96)))
        self.geometry(f'{width}x{height}')
        self.minsize(min(width, px(720)), min(height, px(480)))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        toolbar = ttk.Frame(self, padding=px(8))
        toolbar.grid(row=0, column=0, sticky='ew')
        toolbar.columnconfigure(1, weight=1)
        ttk.Label(toolbar, text='历史快照（保留 7 天）').grid(row=0, column=0, padx=px(0, 8))
        self.version = ttk.Combobox(toolbar, state='readonly')
        self.version.grid(row=0, column=1, sticky='ew')
        self.version.bind('<<ComboboxSelected>>', self.compare)
        ttk.Button(toolbar, text='刷新', command=self.reload).grid(row=0, column=2, padx=px(8, 0))
        searchbar = ttk.Frame(self, padding=px(8, 0, 8, 8))
        searchbar.grid(row=1, column=0, sticky='ew')
        searchbar.columnconfigure(1, weight=1)
        ttk.Label(searchbar, text='筛选条目').grid(row=0, column=0, padx=px(0, 8))
        self.search = tk.StringVar()
        ttk.Entry(searchbar, textvariable=self.search).grid(row=0, column=1, sticky='ew')
        self.search.trace_add('write', lambda *args: self.filter_changes())
        self.open_button = ttk.Button(searchbar, text='打开当前条目', command=self.open_current, state='disabled')
        self.open_button.grid(row=0, column=2, padx=px(8, 0))
        panes = ttk.Panedwindow(self, orient='vertical')
        panes.grid(row=2, column=0, sticky='nsew', padx=px(8))
        listing = ttk.Frame(panes)
        listing.rowconfigure(0, weight=1)
        listing.columnconfigure(0, weight=1)
        self.entries = ttk.Treeview(listing, columns=('status', 'table', 'name', 'key'), show='headings', selectmode='browse', height=8)
        for key, title, size in [('status', '变更', 55), ('table', 'table', 220), ('name', '名称', 240), ('key', 'ID / 路径', 450)]:
            self.entries.heading(key, text=title)
            self.entries.column(key, width=px(size), minwidth=px(45))
        self.entries.grid(row=0, column=0, sticky='nsew')
        vertical = ttk.Scrollbar(listing, command=self.entries.yview)
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal = ttk.Scrollbar(listing, orient='horizontal', command=self.entries.xview)
        horizontal.grid(row=1, column=0, sticky='ew')
        self.entries.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.entries.bind('<<TreeviewSelect>>', self.show_change)
        self.entries.bind('<Double-1>', self.open_current)
        panes.add(listing, weight=1)
        self.diff_view = TextPane(panes, size=app.settings['font_size'], code=True)
        panes.add(self.diff_view, weight=2)
        self.status = tk.StringVar()
        ttk.Label(self, textvariable=self.status, padding=px(8)).grid(row=3, column=0, sticky='ew')
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.bind('<<ThemeChanged>>', lambda event: self.apply_palette())
        self.apply_palette()
        self.poll_token = self.after(100, self.poll)
        self.reload()

    def apply_palette(self):
        if not hasattr(self, 'diff_view'):
            return
        self.configure(bg=COLORS['bg'])
        style_titlebar(self, self.app.settings['theme'])
        self.diff_view.apply_palette()
        self.diff_view.set_size(self.app.settings['font_size'])
        for tag, color in [('added', 'green'), ('removed', 'red'), ('hunk', 'purple')]:
            self.diff_view.text.tag_configure(tag, foreground=COLORS[color])

    def reload(self):
        if self.app.busy:
            self.status.set('数据更新中，完成后刷新差异')
            return
        previous = self.versions[self.version.current()] if self.version.current() >= 0 else None
        try:
            self.versions = list_snapshots(self.directory)
        except OSError as error:
            self.status.set('历史读取失败：' + str(error))
            return
        self.version.configure(values=[time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(snapshot_time(p))) + ' 更新前' for p in self.versions])
        if self.versions:
            self.version.current(self.versions.index(previous) if previous in self.versions else 0)
            self.compare()
        else:
            self.generation += 1
            self.version.set('')
            self.changes = []
            self.filter_changes()
            self.status.set('暂无历史快照；数据发生更新后保留 7 天')

    def compare(self, event=None):
        index = self.version.current()
        if index < 0:
            return
        self.generation += 1
        generation, snapshot = self.generation, self.versions[index]
        self.changes = []
        self.filter_changes()
        self.status.set('正在比较历史快照与当前 tables…')
        def worker():
            try:
                value = compare_snapshot(snapshot, self.directory)
            except Exception as error:
                value = error
            self.messages.put((generation, value))
        threading.Thread(target=worker, name='bena-table-diff', daemon=True).start()

    def poll(self):
        try:
            while True:
                generation, value = self.messages.get_nowait()
                if generation != self.generation:
                    continue
                if isinstance(value, Exception):
                    self.status.set('差异读取失败：' + str(value))
                else:
                    self.changes = value
                    self.filter_changes()
        except queue.Empty:
            pass
        self.poll_token = self.after(100, self.poll)

    def filter_changes(self):
        children = self.entries.get_children()
        if children:
            self.entries.delete(*children)
        self.diff_view.set_text('')
        self.open_button.configure(state='disabled')
        terms = self.search.get().casefold().split()
        count = 0
        for index, change in enumerate(self.changes):
            entry = self.app.catalog.resolve(change.target) if self.app.catalog and change.target else None
            name = entry.name if entry else change.name
            values = (change.status, change.table, name, change.key)
            if all(term in ' '.join(values).casefold() for term in terms):
                self.entries.insert('', 'end', iid=str(index), values=values)
                count += 1
        self.status.set(f'{count} / {len(self.changes)} 个差异条目 · 历史 → 当前')
        if count:
            self.entries.selection_set(self.entries.get_children()[0])

    def selected_change(self):
        selected = self.entries.selection()
        return self.changes[int(selected[0])] if selected else None

    def show_change(self, event=None):
        change = self.selected_change()
        if change is None:
            return
        content = change.diff()
        self.diff_view.set_text(content)
        for line, text in enumerate(content.splitlines(), 1):
            tag = 'added' if text.startswith('+') else 'removed' if text.startswith('-') else 'hunk' if text.startswith('@@') else None
            if tag:
                self.diff_view.text.tag_add(tag, f'{line}.0', f'{line}.end')
        available = change.target and self.app.catalog and self.app.catalog.resolve(change.target)
        self.open_button.configure(state='normal' if available else 'disabled')
        self.diff_view.text.yview_moveto(0)
        self.diff_view.text.xview_moveto(0)

    def open_current(self, event=None):
        change = self.selected_change()
        if change and change.target and self.app.catalog and self.app.catalog.resolve(change.target):
            self.app.navigate(change.target)

    def close(self):
        self.after_cancel(self.poll_token)
        self.destroy()
