import io
import json
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from app_paths import required_files
from app_settings import DEFAULT_LOAD, normalize_settings, save_settings, load_settings
from bena.catalog import Catalog
from game_class import Buff
from downloader import prepare_files, read_metadata, update_due
from editor_views import reference_parts, json_spans
from app_settings import SOURCE_URLS
from downloader import FILES


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog(['buff'])
        self.catalog.add('buff', 'same_id', Buff('same_id', {}))
        self.catalog.add('buff_template', 'same_id', Buff('same_id', {}))
        self.catalog.add('buff', 'long_id_extra', Buff('long_id_extra', {}))
        self.catalog.install()

    def test_typed_marker_and_missing_target(self):
        parts = reference_parts('添加 <buff_template|same_id>，找不到 <buff|missing_id>', self.catalog)
        links = [target for _, target in parts if target]
        self.assertEqual(links, ['buff_template.same_id'])
        self.assertIn(('missing_id', None), parts)

    def test_bare_ids_do_not_create_links(self):
        parts = reference_parts('same_id / long_id_extra / xsame_id / same_id_tail / same_id[unknown] / [same_id]', self.catalog)
        self.assertEqual([t for _, t in parts if t], [])

    def test_hidden_table_remains_navigable(self):
        self.assertEqual(len(self.catalog.visible()), 2)
        self.assertIsNotNone(self.catalog.resolve('buff_template.same_id'))
        self.assertIsNone(self.catalog.resolve('global_buff.same_id'))

    def test_duplicate_translated_name_is_not_ambiguous_link(self):
        self.catalog.names['重复名字'] = list(self.catalog.entries.values())
        self.assertIsNone(self.catalog.resolve('重复名字'))


class SourceTests(unittest.TestCase):
    def test_escaped_strings_and_json_values(self):
        source = json.dumps({'$type': 'Torappu.Test', 'message': 'quote " true 12', 'n': -1.2e-9, 'yes': True, 'nil': None})
        spans = [(source[a:b], kind) for a, b, kind in json_spans(source)]
        self.assertIn(('"$type"', 'key'), spans)
        self.assertIn(('"Torappu.Test"', 'type'), spans)
        self.assertIn(('true', 'keyword'), spans)
        self.assertIn(('null', 'keyword'), spans)
        self.assertEqual(sum(kind == 'number' for _, kind in spans), 1)


class RogueCatalogTests(unittest.TestCase):
    def test_unselected_themes_are_loaded_and_remain_resolvable(self):
        details = {}
        for season in ('rogue_1', 'rogue_5', 'rogue_6'):
            key = season + '_relic'
            details[season] = {'items': {key: {'name': '同名藏品', 'type': 'RELIC'}},
                               'relics': {key: {'buffs': []}}}
        fixtures = {'character_table.json': {}, 'enemy_database.json': {},
                    'buff_table.json': {}, 'buff_template_data.json': {},
                    'roguelike_topic_table.json': {'details': details}}
        catalog = Catalog(['rogue_6'])
        with patch.object(catalog, 'read', side_effect=fixtures.__getitem__) as read:
            catalog.load()
            self.assertEqual(sum(call.args == ('roguelike_topic_table.json',) for call in read.call_args_list), 1)
        self.assertEqual({e.table for e in catalog.visible()}, {'rogue_6'})
        self.assertTrue(set(details) <= catalog.loaded_tables)
        for season in details:
            entry = catalog.resolve('rogue_item.' + season + '_relic')
            self.assertEqual(entry.table, season)
            self.assertIs(entry.obj.item_info, details[season]['items'][entry.key])
            self.assertIs(entry.obj.item_data, details[season]['relics'][entry.key])
        catalog.tables = ['rogue_1', 'rogue_5']
        self.assertEqual({e.table for e in catalog.visible()}, {'rogue_1', 'rogue_5'})
        self.assertIsNotNone(catalog.resolve('rogue_item.rogue_6_relic'))

    def test_buff_only_load_does_not_require_rogue_file(self):
        fixtures = {'character_table.json': {}, 'enemy_database.json': {},
                    'buff_table.json': {}, 'buff_template_data.json': {}}
        catalog = Catalog(['buff'])
        with patch.object(catalog, 'read', side_effect=fixtures.__getitem__):
            catalog.load()
        self.assertEqual(catalog.loaded_tables, {'buff', 'buff_template', 'global_buff'})
        self.assertFalse(catalog.groups['rogue_item'])


class Response(io.BytesIO):
    def __init__(self, data):
        super().__init__(json.dumps(data).encode())
        self.headers = {'ETag': 'example-tag'}


class UpdateTests(unittest.TestCase):
    def test_both_sources_route_every_table_and_record_origin(self):
        data = {'buff_table.json': {'b': {'templateKey': 'empty'}},
                'buff_template_data.json': {'b': {'eventToActions': {}}},
                'character_table.json': {'c': {'name': '干员'}},
                'enemy_database.json': {'enemies': []},
                'roguelike_topic_table.json': {'details': {}}}
        for source, base in SOURCE_URLS.items():
            with self.subTest(source=source), tempfile.TemporaryDirectory() as directory:
                urls = []
                def opener(request, **kwargs):
                    urls.append(request.full_url)
                    name = next(name for name, path in FILES.items() if request.full_url == base + path)
                    return Response(data[name])
                self.assertEqual(prepare_files(True, list(FILES), directory=directory, opener=opener, source=source), list(FILES))
                self.assertEqual(urls, [base + path for path in FILES.values()])
                metadata = read_metadata(directory)
                self.assertEqual(metadata['source'], source)
                for name in FILES:
                    self.assertEqual(metadata['files'][name]['source'], source)
                    self.assertEqual(metadata['files'][name]['url'], base + FILES[name])

    def test_source_switch_refetches_without_reusing_other_sources_etag(self):
        with tempfile.TemporaryDirectory() as directory:
            prepare_files(True, ['buff_table.json'], directory=directory,
                          opener=lambda *a, **k: Response({'github': {'templateKey': 'empty'}}))
            self.assertTrue(update_due(24, directory, ['buff_table.json'], source='prts'))
            def switched(request, **kwargs):
                self.assertEqual(request.full_url, SOURCE_URLS['prts'] + FILES['buff_table.json'])
                self.assertIsNone(request.get_header('If-none-match'))
                self.assertIsNone(request.get_header('If-modified-since'))
                return Response({'prts': {'templateKey': 'empty'}})
            self.assertEqual(prepare_files(False, ['buff_table.json'], directory=directory, opener=switched, source='prts'), ['buff_table.json'])
            self.assertIn('prts', json.loads((Path(directory) / 'buff_table.json').read_text()))
            self.assertFalse(update_due(24, directory, ['buff_table.json'], source='prts'))
            self.assertTrue(update_due(24, directory, ['buff_table.json'], source='github'))
            def unchanged(request, **kwargs):
                self.assertEqual(request.get_header('If-none-match'), 'example-tag')
                raise urllib.error.HTTPError(request.full_url, 304, 'unchanged', {}, None)
            self.assertEqual(prepare_files(True, ['buff_table.json'], directory=directory, opener=unchanged, source='prts'), [])

    def test_failed_source_switch_preserves_local_data_and_origin(self):
        with tempfile.TemporaryDirectory() as directory:
            prepare_files(True, ['buff_table.json'], directory=directory,
                          opener=lambda *a, **k: Response({'github': {'templateKey': 'empty'}}))
            old_data = (Path(directory) / 'buff_table.json').read_bytes()
            old_metadata = (Path(directory) / '.update.json').read_bytes()
            with self.assertRaises(ValueError):
                prepare_files(True, ['buff_table.json'], directory=directory,
                              opener=lambda *a, **k: Response({'invalid': True}), source='prts')
            self.assertEqual((Path(directory) / 'buff_table.json').read_bytes(), old_data)
            self.assertEqual((Path(directory) / '.update.json').read_bytes(), old_metadata)

    def test_legacy_update_metadata_belongs_to_github(self):
        with tempfile.TemporaryDirectory() as directory:
            metadata = {'files': {'buff_table.json': {'checked_at': time.time(), 'etag': 'old'}}}
            (Path(directory) / '.update.json').write_text(json.dumps(metadata))
            self.assertFalse(update_due(24, directory, ['buff_table.json'], source='github'))
            self.assertTrue(update_due(24, directory, ['buff_table.json'], source='prts'))

    def test_unknown_source_is_rejected_before_download(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                prepare_files(source='unknown', directory=directory)
            with self.assertRaises(ValueError):
                update_due(24, directory, source='unknown')

    def test_failure_does_not_replace_any_local_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'buff_table.json'
            path.write_text('{"old": {"templateKey": "empty"}}')
            def opener(request, **kwargs):
                if request.full_url.endswith('buff_table.json'):
                    return Response({'new': {'templateKey': 'empty'}})
                return Response({'invalid': True})
            with self.assertRaises(ValueError):
                prepare_files(True, ['buff_table.json', 'buff_template_data.json'], directory=directory, opener=opener)
            self.assertIn('old', json.loads(path.read_text()))
            self.assertFalse((Path(directory) / '.update.json').exists())
            self.assertFalse(list(Path(directory).glob('.update-*')))

    def test_304_and_check_interval(self):
        with tempfile.TemporaryDirectory() as directory:
            prepare_files(True, ['buff_table.json'], directory=directory, opener=lambda *a, **k: Response({'b': {'templateKey': 'empty'}}))
            def unchanged(request, **kwargs):
                self.assertEqual(request.get_header('If-none-match'), 'example-tag')
                raise urllib.error.HTTPError(request.full_url, 304, 'unchanged', {}, None)
            self.assertEqual(prepare_files(True, ['buff_table.json'], directory=directory, opener=unchanged), [])
            self.assertFalse(update_due(24, directory, ['buff_table.json']))
            self.assertTrue(update_due(24, directory, ['character_table.json']))

    def test_parse_validator_blocks_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            def reject(paths):
                raise ValueError('incompatible schema')
            with self.assertRaises(ValueError):
                prepare_files(True, ['buff_table.json'], directory=directory,
                              opener=lambda *a, **k: Response({'b': {'templateKey': 'empty'}}), validator=reject)
            self.assertFalse((Path(directory) / 'buff_table.json').exists())

    def test_commit_failure_rolls_back(self):
        import os
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'buff_table.json'
            target.write_text('{"old": {"templateKey": "empty"}}')
            real_replace = os.replace
            def replace(source, dest):
                if Path(source).name == '.update.json':
                    raise OSError('simulated disk failure')
                return real_replace(source, dest)
            with patch('downloader.os.replace', side_effect=replace), self.assertRaises(OSError):
                prepare_files(True, ['buff_table.json'], directory=directory,
                              opener=lambda *a, **k: Response({'new': {'templateKey': 'empty'}}))
            self.assertIn('old', json.loads(target.read_text()))


class SettingsTests(unittest.TestCase):
    def test_missing_settings_use_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.settings.json'
            self.assertEqual(load_settings(path), normalize_settings({}))
            self.assertFalse(path.exists())

    def test_download_source_defaults_validation_and_roundtrip(self):
        for value in (None, 'unknown', [], 1):
            self.assertEqual(normalize_settings({'download_source': value})['download_source'], 'github')
        settings = normalize_settings({'download_source': 'prts', 'auto_update': False})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            save_settings(settings, path)
            self.assertEqual(load_settings(path)['download_source'], 'prts')
            self.assertFalse(load_settings(path)['auto_update'])

    def test_all_rogue_themes_are_enabled_by_default(self):
        seasons = {f'rogue_{index}' for index in range(1, 7)}
        self.assertTrue(seasons <= set(DEFAULT_LOAD))
        self.assertTrue(seasons <= set(normalize_settings({})['tables']))
        self.assertEqual(normalize_settings({'tables': ['rogue_1']})['tables'], ['rogue_1'])

    def test_required_files_add_rogue_and_autochess_tables_as_names(self):
        files = required_files(['rogue_1', 'autochess'])
        self.assertIn('roguelike_topic_table.json', files)
        self.assertIn('activity_table.json', files)
        self.assertTrue(all(isinstance(name, str) and name.endswith('.json') for name in files))

    def test_theme_defaults_and_valid_values(self):
        self.assertEqual(normalize_settings({})['theme'], 'light')
        self.assertEqual(normalize_settings({'theme': 'invalid'})['theme'], 'light')
        self.assertEqual(normalize_settings({'theme': 'dark'})['theme'], 'dark')

    def test_roundtrip_and_validation(self):
        settings = normalize_settings({'tables': ['buff', 'buff', 'bad'], 'auto_update': False, 'font_size': 100})
        self.assertEqual(settings['tables'], ['buff'])
        self.assertEqual(settings['font_size'], 18)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            save_settings(settings, path)
            self.assertEqual(load_settings(path), settings)
        self.assertEqual(normalize_settings({'tables': []})['tables'], [])


if __name__ == '__main__':
    unittest.main()
