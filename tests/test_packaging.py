"""Release archives must be complete and leave prior releases intact on failure."""
import datetime
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import packer
from app_settings import load_settings, normalize_settings


class PackagingTests(unittest.TestCase):
    def prepare_files(self, source):
        files = {'dist/main.exe': b'MZ-test-executable'}
        files.update({name: name.encode('utf-8') for name in packer.RESOURCES})
        for name, content in files.items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return files

    def test_archive_contains_executable_and_all_resources_from_another_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'source with spaces'
            other = Path(temporary) / 'other'
            other.mkdir()
            files = self.prepare_files(source)
            previous = Path.cwd()
            try:
                os.chdir(other)
                with patch('packer.SOURCE_DIR', source):
                    archive = packer.create_archive(date=datetime.date(2026, 10, 2))
            finally:
                os.chdir(previous)
            self.assertEqual(archive.parent, source / 'output')
            with zipfile.ZipFile(archive) as package:
                self.assertIsNone(package.testzip())
                self.assertEqual(set(package.namelist()), {'贝娜的量角器.exe', '.settings.json', *packer.RESOURCES})
                self.assertEqual(package.read('贝娜的量角器.exe'), files['dist/main.exe'])
                for name in packer.RESOURCES:
                    self.assertEqual(package.read(name), files[name])

    def test_archive_generates_loadable_defaults_without_source_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'source'
            self.prepare_files(source)
            archive = packer.create_archive(source)
            released = Path(temporary) / 'released'
            with zipfile.ZipFile(archive) as package:
                self.assertIn('.settings.json', package.namelist())
                package.extractall(released)
            other = Path(temporary) / 'other'
            other.mkdir()
            previous = Path.cwd()
            try:
                os.chdir(other)
                with patch('app_paths.BASE_DIR', released):
                    self.assertEqual(load_settings(), normalize_settings({}))
            finally:
                os.chdir(previous)
            self.assertFalse((source / '.settings.json').exists())

    def test_archive_does_not_copy_or_change_personal_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            self.prepare_files(source)
            local = source / '.settings.json'
            personal = b'{"theme":"dark","download_source":"prts","tables":["buff"],"font_size":18}'
            local.write_bytes(personal)
            archive = packer.create_archive(source)
            with zipfile.ZipFile(archive) as package:
                self.assertEqual(json.loads(package.read('.settings.json')), normalize_settings({}))
            self.assertEqual(local.read_bytes(), personal)

    def test_missing_executable_or_resource_does_not_create_an_empty_archive(self):
        for missing in ('dist/main.exe', 'translation/enum_dictionary.json'):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temporary:
                source = Path(temporary)
                self.prepare_files(source)
                (source / missing).unlink()
                with self.assertRaises(FileNotFoundError):
                    packer.create_archive(source)
                self.assertFalse((source / 'output').exists())

    def test_write_failure_preserves_previous_release_and_removes_partial_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            self.prepare_files(source)
            archive = packer.create_archive(source)
            previous = archive.read_bytes()
            with patch('packer.zipfile.ZipFile.write', side_effect=OSError('simulated disk failure')):
                with self.assertRaises(OSError):
                    packer.create_archive(source)
            self.assertEqual(archive.read_bytes(), previous)
            self.assertEqual(list(archive.parent.iterdir()), [archive])


if __name__ == '__main__':
    unittest.main()
