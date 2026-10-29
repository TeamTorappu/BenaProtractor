#----------------------------------------
# 量角器UI
#----------------------------------------
import copy
import logging
import queue
import threading
import time
import tkinter as tk

import anne
from app_paths import app_path
from app_settings import LOAD_TYPES, load_settings, normalize_settings, save_settings
from catalog import Catalog, required_files
from downloader import prepare_files, update_due
from vs_theme import install_theme
from ide_shell import Workspace
from preferences_view import Preferences
from table_history import list_snapshots
from table_history_view import TableHistory
from dpi import DpiScale, enable_dpi_awareness

log = logging.getLogger(__name__)


class Protractor:
    def __init__(self, window=None, settings=None):
        if window is None:
            enable_dpi_awareness()
        self.window = window or tk.Tk()
        px = DpiScale(self.window)
        self.settings = normalize_settings(settings) if settings is not None else load_settings()
        self.window.title('贝娜的量角器')
        screen_width, screen_height = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        width = min(px(1280), max(1, screen_width - px(64)))
        height = min(px(800), max(1, screen_height - px(96)))
        left = max(0, (screen_width - width) // 2)
        top = max(0, (screen_height - height - px(64)) // 2)
        self.window.geometry(f'{width}x{height}+{left}+{top}')
        self.window.minsize(min(px(960), width), min(px(600), height))
        icon = app_path('icon', 'icon.ico')
        if icon.exists():
            self.window.iconbitmap(str(icon))
        self.catalog = None
        self.current = None
        self.history = []
        self.history_index = -1
        self.busy = False
        self.closed = False
        self.settings_window = None
        self.table_history_window = None
        self.pending_search = None
        self.messages = queue.Queue()
        self.next_auto_attempt = 0
        self.style = install_theme(self.window, self.settings['theme'], self.settings['ui_font_size'])
        self.workspace = Workspace(self)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.bind('<Control-f>', self.focus_search)
        self.window.bind('<Alt-Left>', lambda event: self.go_history(-1))
        self.window.bind('<Alt-Right>', lambda event: self.go_history(1))
        self.window.bind('<F5>', lambda event: self.refresh())
        self.poll_token = self.window.after(100, self.poll)
        self.auto_token = self.window.after(60000, self.auto_check)

    def focus_search(self, event=None):
        if not self.workspace.explorer_visible:
            self.workspace.toggle_explorer()
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, 'end')
        return 'break'

    def queue_search(self, *args):
        if self.pending_search:
            self.window.after_cancel(self.pending_search)
        self.pending_search = self.window.after(160, self.try_search)

    def try_search(self, event=None):
        if self.pending_search:
            self.window.after_cancel(self.pending_search)
            self.pending_search = None
        if self.catalog is None:
            return
        terms = self.search_var.get().casefold().split()
        selected_table = next((key for key, label in LOAD_TYPES.items() if label == self.filter_var.get()), None)
        entries = self.catalog.visible(self.settings['show_hidden'])
        visible = [entry for entry in entries if (selected_table is None or entry.table == selected_table)
                   and all(term in f'{entry.name} {entry.key}'.casefold() for term in terms)]
        expanded = {self.directory.item(key, 'text'): self.directory.item(key, 'open') for key in self.directory.get_children()}
        roots = self.directory.get_children()
        if roots:
            self.directory.delete(*roots)
        groups = {}
        for entry in visible:
            groups.setdefault(entry.table, []).append(entry)
        for table, items in groups.items():
            group = 'table:' + table
            label = LOAD_TYPES[table]
            self.directory.insert('', 'end', iid=group, text=label, open=True if terms else expanded.get(label, True))
            for entry in items:
                self.directory.insert(group, 'end', iid=entry.target, text=entry.name)
        self.count_label.configure(text=f'{len(visible):,} / {len(entries):,} 条目')
        self.sync_selection()

    def sync_selection(self):
        if self.current and self.directory.exists(self.current.target):
            if self.directory.selection() != (self.current.target,):
                self.directory.selection_set(self.current.target)
            self.directory.see(self.current.target)

    def display_directory_selected_item(self, event=None):
        selection = self.directory.selection()
        if self.catalog and selection and selection[0] in self.catalog.entries:
            self.navigate(selection[0])

    def navigate(self, target, record=True):
        if self.catalog is None:
            return False
        entry = self.catalog.resolve(target)
        if entry is None:
            self.status.set('条目不存在：' + target)
            return False
        if self.current is entry:
            return True
        self.current = entry
        if record:
            self.history = self.history[:self.history_index + 1] + [entry.target]
            self.history_index = len(self.history) - 1
        self.update_history_buttons()
        self.workspace.set_document(entry)
        translators = {'buff': anne.translate_whole_buff, 'buff_template': anne.translate_whole_buff_template,
                       'global_buff': anne.translate_whole_global_buff, 'rogue_item': anne.translate_whole_rogue_item}
        try:
            document = translators[entry.category](copy.deepcopy(entry.obj))
        except Exception as error:
            log.exception('翻译失败: %s', target)
            document = {'main': entry.name, 'children': [{'main': '翻译失败', 'description': str(error)}]}
        self.translation.show(document, self.catalog)
        obj = entry.obj
        if entry.category == 'rogue_item':
            raw = {'item_info': obj.item_info, 'item_data': obj.item_data} if obj.has_effect else obj.item_info
        else:
            raw = {entry.key: obj.prefab_data if entry.category == 'global_buff' else obj.buff_data}
        self.source.show(raw)
        self.sync_selection()
        if not self.busy:
            self.status.set(entry.target)
        return True

    display_by_id = navigate

    def update_history_buttons(self):
        self.back_button.configure(state='normal' if self.history_index > 0 else 'disabled')
        self.forward_button.configure(state='normal' if self.history_index < len(self.history) - 1 else 'disabled')

    def go_history(self, delta):
        destination = self.history_index + delta
        if 0 <= destination < len(self.history):
            self.history_index = destination
            self.current = None
            self.navigate(self.history[destination], record=False)
        return 'break'

    def select_view(self, index):
        if index in (0, 1):
            self.main_panel.select(index)

    def copy_all(self):
        view = self.translation if self.main_panel.index(self.main_panel.select()) == 0 else self.source
        view.copy_all()
        self.status.set('已复制全文')

    def copy_id(self):
        if self.current:
            self.window.clipboard_clear()
            self.window.clipboard_append(self.current.key)
            self.status.set('已复制 ID')

    def change_theme(self, theme):
        candidate = normalize_settings(dict(self.settings, theme=theme))
        try:
            save_settings(candidate)
        except OSError as error:
            self.status.set('设置保存失败：' + str(error))
            self.workspace.theme_choice.set('浅色' if self.settings['theme'] == 'light' else '深色')
            return False
        self.settings = candidate
        self.style = install_theme(self.window, candidate['theme'], candidate['ui_font_size'])
        self.workspace.apply_palette()
        self.translation.apply_palette()
        self.source.apply_palette()
        return True

    def apply_settings(self, candidate):
        candidate = normalize_settings(candidate)
        source_changed = candidate['download_source'] != self.settings['download_source']
        save_settings(candidate)
        self.settings = candidate
        self.style = install_theme(self.window, candidate['theme'], candidate['ui_font_size'])
        self.workspace.apply_palette()
        self.workspace.apply_metrics()
        for view in (self.translation, self.source):
            view.set_size(candidate['font_size'])
            view.apply_palette()
        reload_required = self.catalog is None or any(t not in self.catalog.loaded_tables for t in candidate['tables'])
        if source_changed:
            self.refresh(settings=candidate)
        elif reload_required:
            self.refresh(startup=True, settings=candidate)
        else:
            self.catalog.tables = list(candidate['tables'])
            self.install_catalog(self.catalog, candidate)
            self.status.set('设置已保存')

    def open_settings(self):
        if self.busy:
            return
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
        else:
            self.settings_window = Preferences(self)

    def open_table_history(self):
        if self.table_history_window and self.table_history_window.winfo_exists():
            self.table_history_window.lift()
            self.table_history_window.reload()
        else:
            self.table_history_window = TableHistory(self)

    def install_catalog(self, catalog, settings):
        previous = self.current.target if self.current else None
        catalog.install()
        self.catalog, self.settings = catalog, normalize_settings(settings)
        self.current = None
        self.history = [target for target in self.history if target in catalog.entries]
        self.history_index = min(self.history_index, len(self.history) - 1)
        options = ['全部 table'] + [LOAD_TYPES[key] for key in self.settings['tables']]
        self.filter.configure(values=options)
        if self.filter_var.get() not in options:
            self.filter_var.set(options[0])
        for view in (self.translation, self.source):
            view.set_size(self.settings['font_size'])
        self.try_search()
        if previous in catalog.entries:
            self.navigate(previous, record=False)
        else:
            self.history, self.history_index = [], -1
            self.update_history_buttons()
            self.translation.document = None
            self.translation.set_text('')
            self.source.set_text('')
            self.breadcrumb.configure(text='')
            self.key_label.configure(text='')
            self.window.title('贝娜的量角器')
            children = self.properties.get_children()
            if children:
                self.properties.delete(*children)
        try:
            save_settings(self.settings)
        except OSError as error:
            self.messages.put(('error', '设置保存失败：' + str(error)))
        for warning in catalog.warnings:
            self.messages.put(('status', warning))

    def start(self):
        self.refresh(startup=True)

    def refresh(self, startup=False, settings=None):
        if self.busy:
            return
        candidate = normalize_settings(settings if settings is not None else self.settings)
        self.busy = True
        self.next_auto_attempt = time.time() + 900
        self.update_button.configure(state='disabled')
        self.settings_button.configure(state='disabled')
        self.progress.configure(mode='indeterminate')
        self.progress.start(15)
        self.status.set('读取本地数据' if startup else '检查游戏数据更新')

        def progress(message):
            self.messages.put(('status', message))

        def worker():
            try:
                list_snapshots()
                names = required_files(candidate['tables'])
                ready = all(app_path('tables', name).exists() for name in names)
                loaded = False
                if startup and ready:
                    try:
                        snapshot = Catalog(candidate['tables']).load()
                        self.messages.put(('loaded', (snapshot, candidate)))
                        loaded = True
                    except Exception:
                        log.exception('Local data invalid')
                needs_update = not startup or not loaded or candidate['auto_update'] and update_due(candidate['update_hours'], names=names, source=candidate['download_source'])
                if needs_update:
                    changed = prepare_files(force=ready, names=names, progress=progress,
                                            source=candidate['download_source'],
                                            validator=lambda paths: Catalog(candidate['tables'], paths).load())
                    if changed or not loaded or settings is not None:
                        self.messages.put(('loaded', (Catalog(candidate['tables']).load(), candidate)))
                    progress(f'已更新 {len(changed)} 个文件' if changed else '数据已是最新')
                else:
                    progress('本地数据已加载')
            except Exception as error:
                log.exception('Data update failed')
                self.messages.put(('error', str(error)))
            finally:
                self.messages.put(('done', None))
        threading.Thread(target=worker, name='bena-data', daemon=True).start()

    def poll(self):
        if self.closed:
            return
        try:
            while True:
                kind, value = self.messages.get_nowait()
                if kind == 'status':
                    self.status.set(value)
                elif kind == 'loaded':
                    catalog, settings = value
                    # A theme change made while downloading belongs to the user,
                    # not the earlier worker snapshot.
                    settings['theme'] = self.settings['theme']
                    self.install_catalog(catalog, settings)
                elif kind == 'error':
                    self.status.set(('更新失败：' if self.catalog else '数据加载失败：') + value)
                    if self.catalog is None:
                        self.translation.set_text(value)
                    if not self.workspace.output_visible:
                        self.workspace.toggle_output()
                elif kind == 'done':
                    self.busy = False
                    self.progress.stop()
                    self.progress.configure(mode='determinate', value=0)
                    self.update_button.configure(state='normal')
                    self.settings_button.configure(state='normal')
                    if self.table_history_window and self.table_history_window.winfo_exists():
                        self.table_history_window.reload()
        except queue.Empty:
            pass
        except Exception as error:
            log.exception('UI refresh failed')
            self.status.set('刷新失败：' + str(error))
        self.poll_token = self.window.after(100, self.poll)

    def auto_check(self):
        if self.closed:
            return
        if not self.busy and time.time() >= self.next_auto_attempt and self.settings['auto_update'] and update_due(self.settings['update_hours'], names=required_files(self.settings['tables']), source=self.settings['download_source']):
            self.refresh()
        self.auto_token = self.window.after(60000, self.auto_check)

    def open(self):
        self.window.mainloop()

    def close(self):
        self.closed = True
        if self.table_history_window and self.table_history_window.winfo_exists():
            self.table_history_window.close()
        for token in (self.pending_search, self.poll_token, self.auto_token):
            if token:
                self.window.after_cancel(token)
        self.window.destroy()
