"""Integration checks against locally available tables; no downloads required."""
import copy
import io
import json
import tempfile
from pathlib import Path
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch
import tkinter as tk

from app_paths import app_path, required_files
from app_settings import DEFAULT_LOAD, LOAD_TYPES, normalize_settings
from bena.catalog import Catalog
from protractor import Protractor


class StartupSettingsTests(unittest.TestCase):
    def test_window_starts_without_settings_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.settings.json'
            root = tk.Tk()
            root.withdraw()
            app = None
            try:
                with patch('app_settings.app_path', return_value=path):
                    app = Protractor(root)
                root.update_idletasks()
                self.assertEqual(app.settings, normalize_settings({}))
                self.assertTrue(app.translation.winfo_exists())
                self.assertFalse(path.exists())
            finally:
                if app is not None:
                    app.close()
                else:
                    root.destroy()


@unittest.skipUnless(all(app_path('tables', name).exists() for name in required_files(DEFAULT_LOAD)), 'Local game tables not available')
class WorkbenchIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()
        cls.app = Protractor(cls.root, {'tables': DEFAULT_LOAD, 'auto_update': False})
        cls.catalog = Catalog(DEFAULT_LOAD).load()
        with patch('protractor.save_settings'):
            cls.app.install_catalog(cls.catalog, normalize_settings({'tables': DEFAULT_LOAD, 'auto_update': False}))

    @classmethod
    def tearDownClass(cls):
        cls.app.close()

    def test_navigation_history_and_source_data(self):
        self.app.current = None
        self.app.history = []
        self.app.history_index = -1
        targets = ['buff.sluggish', 'buff_template.skadi2_t_2', 'buff_template.enemy_hymwr_t']
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            for target in targets:
                self.assertTrue(self.app.navigate(target))
            self.app.go_history(-1)
            self.assertEqual(self.app.current.target, targets[1])
            self.app.go_history(1)
            self.assertEqual(self.app.current.target, targets[2])
        self.assertIn('enemy_hymwr_t', self.app.source.text.get('1.0', 'end'))
        self.assertTrue(self.app.source.text.tag_ranges('key'))
        self.assertEqual(str(self.app.source.text['state']), 'disabled')

    def test_inline_links_keep_correct_targets(self):
        self.app.translation.show({'main': '引用测试', 'children': [
            {'main': '停顿 <buff|sluggish> / <buff_template|skadi2_t_2> / <buff|not_an_existing_buff>'}]}, self.catalog)
        self.assertIn('buff.sluggish', self.app.translation.links.values())
        self.assertIn('buff_template.skadi2_t_2', self.app.translation.links.values())
        self.assertFalse(any('not_an_existing_buff' in t for t in self.app.translation.links.values()))
        with redirect_stdout(io.StringIO()):
            self.app.translation.follow('buff_template.skadi2_t_2')
        self.assertEqual(self.app.current.target, 'buff_template.skadi2_t_2')


    def test_only_typed_markers_create_links(self):
        view = self.app.translation
        plain = '庇护 / sluggish / <sluggish> / <buff_template|庇护>'
        view.show({'main': plain, 'link': 'buff.sluggish,prts.浪里玄条'}, self.catalog)
        self.assertFalse(view.links)
        self.assertNotIn('[PRTS]', view.text.get('1.0', 'end-1c'))
        marked = '庇护 / <buff|sluggish> / <buff_template|damage_resistance>'
        view.show({'main': marked}, self.catalog)
        self.assertEqual(list(view.links.values()), ['buff.sluggish', 'buff_template.damage_resistance'])
        self.assertEqual(view.text.get('1.0', 'end-1c').rstrip('\n'), view.full_text())

    def test_create_buff_color_does_not_depend_on_blackboard_children(self):
        from vs_theme import THEMES
        app = self.app
        original_theme = app.settings['theme']
        raw = copy.deepcopy(self.catalog.resolve('buff_template.trap_dice_effects').obj.buff_data)
        try:
            with redirect_stdout(io.StringIO()):
                self.assertTrue(app.navigate('buff_template.trap_dice_effects'))
            view = app.translation
            before = view.full_text()
            for theme in ('dark', 'light'):
                with patch('protractor.save_settings'):
                    self.assertTrue(app.change_theme(theme))
                self.assertEqual(view.full_text(), before)
                lines = view.text.get('1.0', 'end-1c').splitlines()
                for key in ('dice_3[effct]', 'dice_4[effct]'):
                    matches = [(i, line) for i, line in enumerate(lines, 1)
                               if key in line and '创建' in line]
                    self.assertEqual(len(matches), 1)
                    line_number, line = matches[0]
                    indent = len(line) - len(line.lstrip())
                    tags = view.text.tag_names(f'{line_number}.{indent}')
                    self.assertIn('body', tags)
                    self.assertNotIn('section', tags)
                    self.assertEqual(view.text.tag_cget('body', 'foreground'), THEMES[theme]['text'])
            self.assertEqual(self.catalog.resolve('buff_template.trap_dice_effects').obj.buff_data, raw)
        finally:
            with patch('protractor.save_settings'):
                app.change_theme(original_theme)

    def test_relic_title_does_not_link_to_same_named_buff(self):
        with redirect_stdout(io.StringIO()):
            self.assertTrue(self.app.navigate('rogue_item.rogue_6_relic_fight_7'))
        view = self.app.translation
        self.assertTrue(view.text.get('1.0', '1.end').startswith('“庇护”'))
        for position in ('1.1', '1.2'):
            self.assertFalse(any(tag in view.links for tag in view.text.tag_names(position)))

    def test_repeated_translation_preserves_raw_template(self):
        import anne
        template = self.catalog.groups['buff_template']['skadi2_t_2']
        before = copy.deepcopy(template.buff_data)
        with redirect_stdout(io.StringIO()):
            a = anne.translate_whole_buff_template(template)
            b = anne.translate_whole_buff_template(template)
        self.assertEqual(a, b)
        self.assertEqual(template.buff_data, before)

    def test_settings_changes_visible_tables_without_breaking_links(self):
        settings = normalize_settings({'tables': ['buff'], 'show_hidden': True, 'auto_update': False, 'font_size': 14})
        self.catalog.tables = ['buff']
        with patch('protractor.save_settings'), redirect_stdout(io.StringIO()):
            self.app.install_catalog(self.catalog, settings)
        self.assertEqual(self.app.directory.get_children(), ('table:buff',))
        self.assertIsNotNone(self.catalog.resolve('buff_template.skadi2_t_2'))
        self.app.search_var.set('SLUGGISH')
        self.app.try_search()
        self.assertTrue(self.app.directory.exists('buff.sluggish'))
        self.app.search_var.set('')
        self.catalog.tables = DEFAULT_LOAD
        with patch('protractor.save_settings'), redirect_stdout(io.StringIO()):
            self.app.install_catalog(self.catalog, normalize_settings({'tables': DEFAULT_LOAD, 'auto_update': False}))

    def test_rogue_source_not_overwritten(self):
        target = next(e.target for e in self.catalog.entries.values() if e.category == 'rogue_item' and e.obj.has_effect)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.app.navigate(target)
        self.assertIn('item_info', self.app.source.text.get('1.0', 'end'))
        self.assertIn('item_data', self.app.source.text.get('1.0', 'end'))
        self.assertEqual(len(self.app.main_panel.tabs()), 2)

    def test_rogue_theme_switching_and_reenabling_preserve_contents(self):
        app = self.app
        original_settings = dict(app.settings)
        details = self.catalog.read('roguelike_topic_table.json')['details']
        seasons = [key for key in LOAD_TYPES if key.startswith('rogue_')]
        app.search_var.set('')
        app.history, app.history_index = [], -1
        try:
            with patch('protractor.save_settings'), patch.object(app, 'refresh') as refresh, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                app.apply_settings(dict(app.settings, tables=list(DEFAULT_LOAD)))
                for season in seasons:
                    self.assertIn(LOAD_TYPES[season], app.filter.cget('values'))
                    app.filter_var.set(LOAD_TYPES[season])
                    app.try_search()
                    self.assertEqual(app.directory.get_children(), ('table:' + season,))
                    children = app.directory.get_children('table:' + season)
                    self.assertTrue(children)
                    self.assertTrue(all(app.catalog.entries[target].table == season for target in children))
                    expected_keys = set(details[season]['items'])
                    actual_keys = {e.key for e in app.catalog.entries.values() if e.table == season}
                    self.assertEqual(actual_keys, expected_keys)
                    entry = next(app.catalog.entries[target] for target in children
                                 if app.catalog.entries[target].obj.type == 'RELIC' and app.catalog.entries[target].obj.has_effect)
                    self.assertTrue(app.navigate(entry.target))
                    raw = json.loads(app.source.text.get('1.0', 'end'))
                    self.assertEqual(raw['item_info'], details[season]['items'][entry.key])
                    self.assertEqual(raw['item_data'], details[season]['relics'][entry.key])
                    self.assertIn(entry.name, app.translation.text.get('1.0', 'end'))
                    self.assertNotIn('翻译失败', app.translation.text.get('1.0', 'end'))
                app.go_history(-1)
                self.assertEqual(app.current.table, 'rogue_5')
                history = list(app.history)
                app.apply_settings(dict(app.settings, tables=['buff', 'rogue_6']))
                self.assertEqual(app.history, history)
                self.assertEqual(app.current.table, 'rogue_5')
                app.apply_settings(dict(app.settings, tables=['buff', 'rogue_1', 'rogue_6']))
                app.filter_var.set(LOAD_TYPES['rogue_1'])
                app.try_search()
                self.assertEqual(app.directory.get_children(), ('table:rogue_1',))
                self.assertEqual(app.history, history)
                refresh.assert_not_called()
        finally:
            app.filter_var.set('全部 table')
            with patch('protractor.save_settings'), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                app.apply_settings(original_settings)

    def test_theme_switch_preserves_document_and_history(self):
        from vs_theme import THEMES
        with redirect_stdout(io.StringIO()):
            self.app.navigate('buff_template.skadi2_t_2')
        current = self.app.current.target
        history = list(self.app.history)
        source = self.app.source.text.get('1.0', 'end')
        self.app.translation.expand_all(True)
        folded = set(self.app.translation.collapsed)
        for theme in ('dark', 'light'):
            with patch('protractor.save_settings') as saved:
                self.assertTrue(self.app.change_theme(theme))
                self.assertEqual(saved.call_args.args[0]['theme'], theme)
            self.assertEqual(self.app.current.target, current)
            self.assertEqual(self.app.history, history)
            self.assertEqual(self.app.source.text.get('1.0', 'end'), source)
            self.assertEqual(self.app.translation.collapsed, folded)
            self.assertEqual(self.app.source.text.cget('background'), THEMES[theme]['editor'])
            self.assertEqual(self.app.source.text.tag_cget('key', 'foreground'), THEMES[theme]['key'])
            for tag in self.app.translation.links:
                self.assertEqual(self.app.translation.text.tag_cget(tag, 'foreground'), THEMES[theme]['blue'])

    def test_failed_theme_save_keeps_current_theme(self):
        previous = self.app.settings['theme']
        with patch('protractor.save_settings', side_effect=OSError('read only')):
            self.assertFalse(self.app.change_theme('dark' if previous == 'light' else 'light'))
        self.assertEqual(self.app.settings['theme'], previous)

    def test_fold_margin_and_full_copy_content(self):
        document = {'main': 'root', 'children': [{'main': 'section', 'children': [{'main': 'deep'}]}]}
        self.app.translation.show(document, self.catalog)
        self.app.translation.expand_all(True)
        self.assertNotIn('deep', self.app.translation.text.get('1.0', 'end'))
        self.assertIn('deep', self.app.translation.full_text())
        self.assertTrue(self.app.translation.folds)
        self.app.translation.toggle((0,))
        self.assertIn('deep', self.app.translation.text.get('1.0', 'end'))

    def test_node_tree_removed_and_options_save(self):
        self.assertEqual([self.app.main_panel.tab(tab, 'text') for tab in self.app.main_panel.tabs()], ['中文伪代码', '原始代码'])
        self.assertFalse(hasattr(self.app, 'graph_view'))
        self.app.open_settings()
        dialog = self.app.settings_window
        self.assertEqual(set(dialog.pages), {'environment', 'tables', 'updates'})
        dialog.theme.set('深色')
        with patch.object(self.app, 'apply_settings') as applied:
            dialog.apply()
            self.assertEqual(applied.call_args.args[0]['theme'], 'dark')

    def test_download_source_picker_saves_selection_and_starts_refresh(self):
        app = self.app
        previous = dict(app.settings)
        try:
            with patch('protractor.save_settings'), patch.object(app, 'refresh') as refresh:
                app.apply_settings(dict(app.settings, download_source='prts', auto_update=False))
                self.assertEqual(app.settings['download_source'], 'prts')
                refresh.assert_called_once_with(settings=app.settings)
            with patch('preferences_view.read_metadata', return_value={'source': 'github', 'checked_at': 1}):
                app.open_settings()
                dialog = app.settings_window
                self.assertEqual(dialog.source.get(), 'PRTS')
                self.assertEqual(dialog.source_picker.cget('values'), ('GitHub', 'PRTS'))
                self.assertEqual(dialog.checked_label.cget('text'), '上次检查：未检查')
                dialog.source.set('GitHub')
                dialog.update_checked()
                self.assertNotEqual(dialog.checked_label.cget('text'), '上次检查：未检查')
                dialog.source.set('PRTS')
                with patch.object(app, 'apply_settings') as applied:
                    dialog.apply()
                    self.assertEqual(applied.call_args.args[0]['download_source'], 'prts')
        finally:
            if app.settings_window and app.settings_window.winfo_exists():
                app.settings_window.destroy()
            with patch('protractor.save_settings'), patch.object(app, 'refresh'):
                app.apply_settings(previous)


if __name__ == '__main__':
    unittest.main()
