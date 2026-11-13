"""IDE document surfaces with margin folding and selectable, read-only text."""
import json
import re
import tkinter as tk
from tkinter import ttk, font
from document_model import reference_parts, json_spans, document_rows, default_folds
from vs_theme import COLORS, menu
from dpi import DpiScale

COLOR_TAG_PATTERN = re.compile(r'<@([A-Za-z0-9_.-]+)>(.*?)</>')
COLOR_TAGS = {
    "mission.levelname": "#FFDE00",
    "mission.number": "#FFDE00",
    "tu.kw": "#0098DC",
    "tu.imp": "#FF0000",
    "cc.vup": "#0098DC",
    "cc.vdown": "#FF6237",
    "cc.rem": "#F49800",
    "cc.kw": "#00B0FF",
    "cc.pn": "#000000",
    "cc.talpu": "#000000",
    "ba.vup": "#0098DC",
    "ba.vdown": "#FF6237",
    "ba.rem": "#F49800",
    "ba.kw": "#00B0FF",
    "ba.pn": "#000000",
    "ba.talpu": "#0098DC",
    "ba.xa": "#FF0000",
    "ba.xb": "#FF7D00",
    "ba.xc": "#FFFF00",
    "ba.xd": "#00FF00",
    "ba.xe": "#00FFFF",
    "ba.xf": "#0291FF",
    "ba.xg": "#FF00FF",
    "ba.gild": "#2FAC78",
    "ba.enemy": "#D83C3C",
    "ba.drop": "#36ACFF",
    "ba.acrem": "#727272",
    "ba.velc": "#21ffc3",
    "ba.delc": "#ff9000",
    "ba.dgrey": "#9a9a9a",
    "eb.key": "#00FFFF",
    "eb.danger": "#FF0000",
    "ro.get": "#0098DC",
    "ro.lose": "#C82A36",
    "rolv.rem": "#FF4C22",
    "lv.description": "#d8d769",
    "lv.extrades": "#d8d769",
    "lv.sand2desc": "#a0a001",
    "lv.item": "#FFFFFF",
    "lv.rem": "#FFFFFF",
    "lv.fs": "#FF0000",
    "lv.sp": "#fd4600",
    "lv.ez": "#0098dc",
    "recalrune.nag": "#c9001c",
    "recalrune.pos": "#0098dc",
    "crisisv2.nag": "#ea9818",
    "crisisv2.pos": "#16acaa",
    "crisisv2.cra": "#d7181c",
    "ro1.get": "#E5B684",
    "ro2.lose": "#FF6E6E",
    "ro2.get": "#59DDDC",
    "ro2.virtue": "#0098dc",
    "ro2.mutation": "#9266b2",
    "ro2.desc": "#6d6d6d",
    "ro3.lose": "#FF6E6E",
    "ro3.get": "#9ed9fd",
    "ro3.redt": "#ff4532",
    "ro3.greent": "#4ffaa5",
    "ro3.bluet": "#0085ff",
    "ro3.bosst": "#ffffff",
    "ro4.lose": "#FF6E6E",
    "ro4.get": "#28bfe5",
    "ro5.lose": "#FF6E6E",
    "ro5.get": "#28bfe5",
    "ro6.get": "#38d0d4",
    "ro6.lose": "#d13464",
    "rc.title": "#FFFFFF",
    "rc.subtitle": "#FFC90E",
    "rc.em": "#FF7F27",
    "rc.eml": "#32CD32",
    "ga.title": "#FFFFFF",
    "ga.subtitle": "#FFC90E",
    "ga.up": "#FF7F27",
    "ga.adgacha": "#00C8FF",
    "ga.nbgacha": "#00DDBB",
    "ga.limadgacha": "#FF7E1F",
    "ga.percent": "#FFD800",
    "ga.attention": "#FF3126",
    "ga.classicgacha": "#00A8FF",
    "attainga.desc": "#FF0000",
    "attainga.desc2": "#FFD800",
    "attainga.attention": "#E1322C",
    "linkagega.charname": "#FFF6A9",
    "linkagega.title": "#FF8A00",
    "ga.spgacha": "#FF8A00",
    "ga.spgacha.return": "#FFCB00",
    "limtedga.title": "#FFFFFF",
    "limtedga.subtitle": "#FFC90E",
    "limtedga.up": "#FF7F27",
    "limtedga.21": "#D7BCFF",
    "limtedga.percent": "#FFD800",
    "limtedga.attention": "#E1322C",
    "limtedga.lattention": "#FF9E58",
    "vc.newyear10": "#FF3823",
    "vc.adgacha": "#0098DC",
    "vc.attention": "#FFD800",
    "act.missiontips": "#d9bd6a",
    "lv.hdbg": "#7ba61f",
    "autochess.gray": "#777777",
    "autochess.dgreen": "#40B196",
    "vecbreakv2.highlight": "#d8741a",
    "dp.level.dis": "#909090",
    "dp.level.rich": "#4970ff",
    "dp.level.raid": "#ff1f1f",
    "duel.ping.low": "#7fa826",
    "duel.ping.medium": "#ec7a00",
    "duel.ping.high": "#ff3d3d",
    "duel.milestone": "#D4133C",
    "duel.dm.award": "#36BBCC",
    "duel.dm.condition": "#C9C9C9",
    "tu.ht": "#ff8d00",
    "multiv3.teambuff": "#d0294c",
    "multiv3.matchdesc": "#2ea0af",
    "multiv3.unlocktoast": "#ff3a64",
    "multiv3.photodesc": "#31acbc",
    "acdm.award": "#04d3a3",
    "acdm.milestone": "#2da186",
    "acdm.hudtip": "#04d3a3",
    "acdm.buff": "#2da186",
    "acdm.tracker": "#2da186",
    "trap.number": "#018FCE",
    "trap.debuff": "#d83c3c",
    "trap.monster": "#d83c3c",
    "trap.combine": "#018FCE",
    "trap.drop": "#018FCE",
    "strategy.number": "#018FCE",
    "strategy.text": "#018FCE",
    "strategy.text2": "#767676",
    "gacha.text": "#f3e468",
    "buff.number": "#ede160",
    "level.highlight": "#ede161",
    "lv.act20side": "#F7BC44",
    "lv.act20sre": "#F7BC44",
    "lv.mhitem": "#A57F5B",
    "lv.mhtx": "#1B1B1B",
    "lv.mhfs": "#A57F5B",
    "cc.miu": "#8F7156",
    "ping.low": "#7fa826",
    "ping.medium": "#ec7a00",
    "ping.high": "#ff3d3d",
    "match.success": "#36BBCC",
    "map.normal": "#36BBCC",
    "map.football": "#36BBCC",
    "map.defence": "#36BBCC",
    "milestone": "#D4133C",
    "dm.award": "#36BBCC",
    "dm.condition": "#C9C9C9",
    "tutor": "#36BBCC",
    "lv.muitem": "#D4133C",
    "token.highlight": "#d8741a",
    "ba.grt": "#FFAB27",
    "ba.exl": "#14F0AF",
    "ba.hrd": "#DA2536",
    "firework.npc": "#810d17",
    "act.spreward": "#FF5001",
    "char.oblv": "#7799cc",
    "char.mort": "#779977",
    "char.dolr": "#bb9955",
    "char.amor": "#aa4477",
    "char.tmor": "#335566",
    "act.timelimit": "#ffe300",
    "lv.pycitem": "#D14631",
    "lv.pyctx": "#1B1B1B",
    "lv.pycfs": "#D14631",
    "arkodcact53side.lv": "#2FA29B",
    "vc.text": "#898989",
    "vc.endtime": "#ff0327"
}


class TextPane(ttk.Frame):
    def __init__(self, master, size=11, code=False):
        super().__init__(master, style='Editor.TFrame')
        self.size, self.code = size, code
        px = self.px = DpiScale(self)
        self.folds = {}
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        families = font.families(self)
        self.code_family = 'Cascadia Mono' if 'Cascadia Mono' in families else 'Consolas'
        self.family = self.code_family if code else 'Microsoft YaHei UI'
        self.reading_font = font.Font(self, family=self.family, size=size)
        self.number_font = font.Font(self, family=self.code_family, size=size)
        self.gutter = tk.Canvas(self, width=px(54), highlightthickness=0, borderwidth=0)
        self.gutter.grid(row=0, column=0, sticky='ns')
        self.text = tk.Text(self, width=1, height=1, wrap='none' if code else 'char',
                            font=self.reading_font, relief='flat', borderwidth=0, highlightthickness=0,
                            padx=px(10), pady=px(10), spacing1=px(1 if code else 2), spacing3=px(1 if code else 2),
                            state='disabled', cursor='xterm', undo=False)
        self.text.grid(row=0, column=1, sticky='nsew')
        self.vertical = ttk.Scrollbar(self, orient='vertical', command=self.text.yview)
        self.horizontal = ttk.Scrollbar(self, orient='horizontal', command=self.text.xview)
        self.vertical.grid(row=0, column=2, sticky='ns')
        self.horizontal.grid(row=1, column=0, columnspan=2, sticky='ew')
        self.text.configure(yscrollcommand=self.scrolled, xscrollcommand=self.horizontal.set)
        self.text.bind('<Configure>', lambda event: self.draw_margin())
        self.text.bind('<Expose>', lambda event: self.draw_margin())
        self.text.bind('<Control-a>', self.select_all)
        self.text.bind('<Button-3>', self.context_menu)
        self.apply_palette()

    def apply_palette(self):
        self.gutter.configure(bg=COLORS['editor'])
        self.text.configure(bg=COLORS['editor'], fg=COLORS['text'], insertbackground=COLORS['text'],
                            selectbackground=COLORS['selection'], selectforeground=COLORS['selected_text'])
        self.draw_margin()

    def scrolled(self, first, last):
        self.vertical.set(first, last)
        self.draw_margin()

    def draw_margin(self):
        if not hasattr(self, 'text'):
            return
        px = self.px
        self.gutter.delete('all')
        digits = max(3, len(self.text.index('end-1c').split('.')[0]))
        margin = self.number_font.measure('0' * digits) + px(30)
        if int(self.gutter.cget('width')) != margin:
            self.gutter.configure(width=margin)
        number_x, fold_x = margin - px(23), margin - px(12)
        index = self.text.index('@0,0')
        while True:
            geometry = self.text.dlineinfo(index)
            if geometry is None:
                break
            line = int(index.split('.')[0])
            y = geometry[1] + geometry[3] / 2
            self.gutter.create_text(number_x, y, text=str(line), anchor='e', fill=COLORS['muted'], font=self.number_font)
            if line in self.folds:
                path, collapsed = self.folds[line]
                tag = 'fold_' + str(line)
                self.gutter.create_rectangle(fold_x - px(5), y - px(5), fold_x + px(5), y + px(5), fill=COLORS['editor'], outline=COLORS['muted'], width=px(1), tags=(tag,))
                self.gutter.create_line(fold_x - px(3), y, fold_x + px(3), y, fill=COLORS['muted'], width=px(1), tags=(tag,))
                if collapsed:
                    self.gutter.create_line(fold_x, y - px(3), fold_x, y + px(3), fill=COLORS['muted'], width=px(1), tags=(tag,))
                self.gutter.tag_bind(tag, '<Button-1>', lambda event, p=path: self.toggle(p))
            index = self.text.index(f'{line + 1}.0')

    def set_size(self, size):
        self.size = size
        self.reading_font.configure(size=size)
        self.number_font.configure(size=size)
        for tag in self.text.tag_names():
            if tag.startswith('indent_'):
                depth = int(tag.split('_')[1])
                self.text.tag_configure(tag, lmargin2=self.reading_font.measure('    ' * depth))
        self.draw_margin()

    def set_text(self, text):
        self.folds.clear()
        self.text.configure(state='normal')
        self.text.delete('1.0', 'end')
        self.text.insert('1.0', text)
        self.text.configure(state='disabled')
        self.draw_margin()

    def select_all(self, event=None):
        self.text.tag_add('sel', '1.0', 'end-1c')
        return 'break'

    def copy_all(self):
        self.clipboard_clear()
        self.clipboard_append(self.text.get('1.0', 'end-1c'))

    def context_menu(self, event):
        popup = menu(self)
        popup.add_command(label='复制', command=lambda: self.text.event_generate('<<Copy>>'),
                          state='normal' if self.text.tag_ranges('sel') else 'disabled')
        popup.add_command(label='复制全文', command=self.copy_all)
        popup.add_separator()
        popup.add_command(label='全选', command=self.select_all, accelerator='Ctrl+A')
        try:
            popup.tk_popup(event.x_root, event.y_root)
        finally:
            popup.grab_release()

# 原始伪代码界面
class SourceView(TextPane):
    def __init__(self, master, size=11):
        super().__init__(master, size=size, code=True)

    def apply_palette(self):
        super().apply_palette()
        for kind in ('key', 'string', 'number', 'keyword', 'type', 'bracket0', 'bracket1', 'bracket2'):
            self.text.tag_configure(kind, foreground=COLORS[kind])

    def show(self, data):
        content = json.dumps(data, ensure_ascii=False, indent=4)
        self.set_text(content)
        for start, end, kind in json_spans(content):
            self.text.tag_add(kind, f'1.0+{start}c', f'1.0+{end}c')
        self.text.yview_moveto(0)
        self.text.xview_moveto(0)

# 伪代码中文翻译界面
class TranslationView(TextPane):
    def __init__(self, master, navigate, size=11):
        self.navigate = navigate
        self.document = None
        self.catalog = None
        self.collapsed = set()
        self.links = {}
        self.color_tags = {}
        super().__init__(master, size=size)
        self.text.bind('<Motion>', self.hover_link)
        self.text.bind('<ButtonRelease-1>', self.activate_link)

    @staticmethod
    def color_for(name):
        return COLOR_TAGS.get(name, COLORS['text'])

    @classmethod
    def split_markup(cls, value):
        parts, offset = [], 0
        for match in COLOR_TAG_PATTERN.finditer(value):
            if match.start() > offset:
                parts.append((value[offset:match.start()], None))
            parts.append((match.group(2), cls.color_for(match.group(1))))
            offset = match.end()
        if offset < len(value):
            parts.append((value[offset:], None))
        return parts

    def apply_palette(self):
        super().apply_palette()
        for role, color in {'heading': COLORS['text'], 'section': COLORS['type'], 'condition': COLORS['purple'],
                            'description': COLORS['muted'], 'body': COLORS['text']}.items():
            self.text.tag_configure(role, foreground=color)
        for tag in self.links:
            self.text.tag_configure(tag, foreground=COLORS['blue'], underline=True)
        for tag, color in self.color_tags.items():
            self.text.tag_configure(tag, foreground=color)

    def show(self, document, catalog):
        self.document, self.catalog = document, catalog
        self.collapsed = default_folds(document)
        self.render()
        self.text.yview_moveto(0)

    def render(self):
        if self.document is None or self.catalog is None:
            return
        for tag in self.links:
            self.text.tag_delete(tag)
        for tag in self.color_tags:
            self.text.tag_delete(tag)
        self.links.clear()
        self.color_tags.clear()
        self.set_text('')
        self.text.configure(state='normal')
        for row in document_rows(self.document, self.collapsed):
            line = int(self.text.index('end-1c').split('.')[0])
            if row.foldable:
                self.folds[line] = (row.path, row.path in self.collapsed)
            indent = f'indent_{row.depth}'
            self.text.tag_configure(indent, lmargin2=self.reading_font.measure('    ' * row.depth))
            self.text.insert('end', '    ' * row.depth, (indent,))
            for text, color in self.split_markup(row.text):
                for label, target in reference_parts(text, self.catalog):
                    tags = (row.role, indent)
                    if color:
                        tag = f'color_{len(self.color_tags)}'
                        self.color_tags[tag] = color
                        self.text.tag_configure(tag, foreground=color)
                        tags += (tag,)
                    if target:
                        tag = f'reference_{len(self.links)}'
                        self.links[tag] = target
                        self.text.tag_configure(tag, foreground=COLORS['blue'], underline=True)
                        tags += (tag,)
                    self.text.insert('end', label, tags)
            self.text.insert('end', '\n')
        self.text.configure(state='disabled')
        self.draw_margin()

    def target_at(self, event):
        index = self.text.index(f'@{event.x},{event.y}')
        return next((self.links[tag] for tag in self.text.tag_names(index) if tag in self.links), None)

    def hover_link(self, event):
        self.text.configure(cursor='hand2' if self.target_at(event) else 'xterm')

    def activate_link(self, event):
        target = self.target_at(event)
        if target and not self.text.tag_ranges('sel'):
            self.follow(target)
            return 'break'

    def follow(self, target):
        self.navigate(target)
        return 'break'

    def toggle(self, path):
        self.collapsed.symmetric_difference_update({path})
        position = self.text.yview()[0]
        self.render()
        self.text.yview_moveto(position)

    def expand_all(self, collapse=False):
        self.collapsed = {row.path for row in document_rows(self.document) if row.foldable and row.path} if collapse else set()
        self.render()

    def full_text(self):
        if self.document is None:
            return self.text.get('1.0', 'end-1c')
        return '\n'.join('    ' * row.depth + ''.join(text for text, _ in reference_parts(COLOR_TAG_PATTERN.sub(r'\2', row.text), self.catalog))
                         for row in document_rows(self.document))

    def copy_all(self):
        self.clipboard_clear()
        self.clipboard_append(self.full_text())
