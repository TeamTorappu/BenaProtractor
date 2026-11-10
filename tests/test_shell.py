"""Exercise dock visibility through the real View menu and Tk geometry."""
from contextlib import contextmanager
from types import SimpleNamespace
import tkinter as tk
import unittest

from bena.catalog import Catalog
from protractor import Protractor


class ExplorerVisibilityTests(unittest.TestCase):
    @contextmanager
    def opened_app(self, dpi=96):
        root = tk.Tk()
        root.withdraw()
        root.attributes('-alpha', 0.0)
        root.tk.call('tk', 'scaling', dpi / 72)
        app = Protractor(root, {'auto_update': False})
        errors = []
        root.report_callback_exception = lambda *error: errors.append(error)
        try:
            root.deiconify()
            root.update()
            yield app
            self.assertFalse(errors, errors)
        finally:
            app.close()

    def explorer_command(self, app):
        button = next(widget for widget in app.workspace.menus.winfo_children()
                      if widget.cget('text') == '视图(V)')
        dropdown = app.window.nametowidget(button.cget('menu'))
        index = next(i for i in range(dropdown.index('end') + 1)
                     if dropdown.type(i) != 'separator'
                     and dropdown.entrycget(i, 'label') == '数据资源管理器')
        return lambda: dropdown.invoke(index)

    def assert_explorer_visible(self, app):
        workspace = app.workspace
        self.assertTrue(workspace.explorer_visible)
        self.assertIn(str(workspace.explorer), workspace.horizontal.panes())
        self.assertTrue(workspace.explorer.winfo_ismapped())
        self.assertGreater(workspace.explorer.winfo_width(), workspace.px(100))
        self.assertLess(workspace.horizontal.sashpos(0),
                        workspace.horizontal.winfo_width() - workspace.px(100))

    def test_view_menu_restores_explorer_at_each_dpi(self):
        for dpi in (96, 144, 192):
            with self.subTest(dpi=dpi), self.opened_app(dpi) as app:
                invoke = self.explorer_command(app)
                catalog = Catalog([])
                catalog.add('buff', 'sample', SimpleNamespace(display_name='Sample', hidden=False))
                app.translation.show({'main': 'root', 'children': [
                    {'main': '<buff|sample>', 'children': [{'main': 'detail'}]}]}, catalog)
                app.translation.toggle((0,))
                app.source.show({'sample': 1})
                app.search_var.set('sample')
                app.directory.insert('', 'end', iid='sample', text='Sample')
                app.directory.selection_set('sample')
                before = (app.translation.text.get('1.0', 'end-1c'), app.translation.full_text(),
                          dict(app.translation.links), set(app.translation.collapsed),
                          app.source.text.get('1.0', 'end-1c'))
                for cycle in range(3):
                    with self.subTest(cycle=cycle):
                        self.assert_explorer_visible(app)
                        invoke()
                        app.window.update()
                        self.assertFalse(app.workspace.explorer_visible)
                        self.assertFalse(app.workspace.explorer.winfo_ismapped())
                        invoke()
                        app.window.update()
                        self.assert_explorer_visible(app)
                        self.assertEqual(app.search_var.get(), 'sample')
                        self.assertEqual(app.directory.selection(), ('sample',))
                        self.assertEqual(before, (
                            app.translation.text.get('1.0', 'end-1c'), app.translation.full_text(),
                            dict(app.translation.links), set(app.translation.collapsed),
                            app.source.text.get('1.0', 'end-1c')))

    def test_rapid_menu_toggles_and_search_restore_explorer(self):
        with self.opened_app() as app:
            invoke = self.explorer_command(app)
            for _ in range(4):
                invoke()
            app.window.update()
            self.assert_explorer_visible(app)
            invoke()
            app.window.update()
            app.focus_search()
            app.window.update()
            self.assert_explorer_visible(app)


if __name__ == '__main__':
    unittest.main()
