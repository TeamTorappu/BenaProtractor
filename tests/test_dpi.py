"""DPI layout checks on real Tk widgets without downloading game data."""
from contextlib import contextmanager
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import font
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import dpi
from bena.catalog import Catalog
from preferences_view import Preferences
from protractor import Protractor


class DpiLayoutTests(unittest.TestCase):
    @contextmanager
    def make_app(self, dpi):
        root = tk.Tk()
        root.withdraw()
        root.tk.call('tk', 'scaling', dpi / 72)
        # Test logical window sizes independently of the test machine's screen.
        with patch.object(root, 'winfo_screenwidth', return_value=7680), \
                patch.object(root, 'winfo_screenheight', return_value=4320):
            app = Protractor(root, {'auto_update': False})
        try:
            yield app
        finally:
            app.close()

    def test_pixel_dimensions_follow_system_dpi(self):
        for dpi in (96, 120, 144, 168, 192):
            with self.subTest(dpi=dpi), self.make_app(dpi) as app:
                root = app.window
                dialog = Preferences(app)
                dialog.withdraw()
                expected = lambda value: round(value * dpi / 96)
                self.assertEqual(root.minsize(), (expected(960), expected(600)))
                self.assertEqual(root.winfo_pixels(app.translation.text.cget('padx')), expected(10))
                self.assertEqual(root.winfo_pixels(app.source.text.cget('spacing1')), expected(1))
                self.assertEqual(app.directory.column('#0', 'minwidth'), expected(140))
                self.assertEqual(app.properties.column('#0', 'width'), expected(68))
                self.assertEqual(dialog.navigation.column('#0', 'width'), expected(140))
                self.assertEqual(int(str(dialog.content.cget('padding')[0])), expected(15))
                self.assertEqual(root.winfo_pixels(dialog.error.cget('wraplength')), expected(400))
                gutter_extra = (int(app.translation.gutter.cget('width'))
                                - app.translation.number_font.measure('000'))
                self.assertEqual(gutter_extra, expected(30))
                self.assertEqual(int(app.style.lookup('Treeview', 'indent')), expected(16))
                self.assertEqual(int(app.style.lookup('TPanedwindow', 'sashwidth')), expected(4))
                self.assertEqual(int(app.style.lookup('Vertical.TScrollbar', 'arrowsize')), expected(11))
                self.assertEqual(int(app.progress.cget('length')), expected(90))
                # Point fonts and dimensions already measured from fonts scale once.
                self.assertEqual(app.translation.reading_font.cget('size'), 11)
                self.assertEqual(app.workspace.explorer_width,
                                 round(320 * font.nametofont('TkDefaultFont').metrics('linespace') / 19))
                dialog.destroy()

    def test_dpi_and_theme_do_not_change_document_links_or_folds(self):
        catalog = Catalog([])
        catalog.add('buff', 'sample', SimpleNamespace(display_name='Sample', hidden=False))
        document = {'main': 'root', 'children': [
            {'main': 'action <buff|sample>', 'children': [{'main': 'detail'}]}]}
        snapshots = []
        for dpi in (96, 144, 192):
            with self.subTest(dpi=dpi), self.make_app(dpi) as app:
                view = app.translation
                view.show(document, catalog)
                app.source.show({'sample': [1, True, 'text']})
                full_text = view.full_text()
                source = app.source.text.get('1.0', 'end-1c')
                view.toggle((0,))
                folded = view.text.get('1.0', 'end-1c')
                links = dict(view.links)
                with patch('protractor.save_settings'):
                    for theme in ('dark', 'light'):
                        app.change_theme(theme)
                        self.assertEqual(view.collapsed, {(0,)})
                        self.assertEqual(view.text.get('1.0', 'end-1c'), folded)
                        self.assertEqual(view.links, links)
                        self.assertEqual(view.full_text(), full_text)
                        self.assertEqual(app.source.text.get('1.0', 'end-1c'), source)
                view.toggle((0,))
                self.assertIn('detail', view.text.get('1.0', 'end-1c'))
                snapshots.append((full_text, source, folded, links))
        self.assertTrue(all(snapshot == snapshots[0] for snapshot in snapshots))


class DpiSetupTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == 'win32', 'Windows API check')
    def test_native_awareness_is_enabled_before_tk_creation(self):
        script = """
import ctypes
import tkinter as tk
from unittest.mock import patch
from protractor import Protractor

class HiddenTk(tk.Tk):
    def __init__(self):
        value = ctypes.c_int(-1)
        result = ctypes.windll.shcore.GetProcessDpiAwareness(None, ctypes.byref(value))
        assert result == 0 and value.value == 1, (result, value.value)
        super().__init__()
        self.withdraw()

with patch('protractor.tk.Tk', HiddenTk):
    app = Protractor(settings={'auto_update': False})
    try:
        system_dpi = ctypes.windll.user32.GetDpiForSystem()
        assert abs(app.window.winfo_fpixels('1i') - system_dpi) < 1
    finally:
        app.close()
"""
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', script],
                                cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_existing_process_awareness_is_not_overridden(self):
        libraries = Mock()
        libraries.shcore.SetProcessDpiAwareness.return_value = -2147024891  # E_ACCESSDENIED
        with patch('dpi.sys.platform', 'win32'), patch('dpi.ctypes.windll', libraries, create=True):
            dpi.enable_dpi_awareness()
        libraries.shcore.SetProcessDpiAwareness.assert_called_once_with(1)
        libraries.user32.SetProcessDPIAware.assert_not_called()

    def test_legacy_windows_falls_back_to_user32(self):
        libraries = SimpleNamespace(shcore=SimpleNamespace(), user32=Mock())
        with patch('dpi.sys.platform', 'win32'), patch('dpi.ctypes.windll', libraries, create=True):
            dpi.enable_dpi_awareness()
        libraries.user32.SetProcessDPIAware.assert_called_once_with()

    def test_non_windows_does_not_call_windows_apis(self):
        libraries = Mock()
        with patch('dpi.sys.platform', 'linux'), patch('dpi.ctypes.windll', libraries, create=True):
            dpi.enable_dpi_awareness()
        self.assertEqual(libraries.mock_calls, [])


if __name__ == '__main__':
    unittest.main()
