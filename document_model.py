"""Text presentation data, independent of any GUI toolkit."""
from dataclasses import dataclass
import json
import re
import bena

REFERENCE_PATTERN = re.compile(r'<([a-z][a-z0-9_]*)\|([^<>|\r\n]+)>')


def reference_parts(value, catalog):
    """Link only explicit <category|raw key> references, before translation."""
    parts, offset = [], 0
    value = str(value)
    for match in REFERENCE_PATTERN.finditer(value):
        if match.start() > offset:
            parts.append((value[offset:match.start()], None))
        category, key = match.groups()
        target = f'{category}.{key}'
        entry = catalog.entries.get(target)
        if entry is not None:
            parts.append((entry.name, entry.target))
        elif category == 'prts':
            parts.append((key, target))
        elif category in ('buff', 'buff_template', 'global_buff', 'cardbuff'):
            # Prefab-only Buff names still use the original translation fallback.
            # Its result is display text only, never another lookup key.
            label = bena.translate_buff_name(key)
            parts.append((f'{label}（{key}）' if label != key else key, None))
        elif category == 'rogue_item':
            parts.append((key, None))
        elif category == 'autochess_3':
            parts.append((key, None))
        else:
            parts.append((match.group(), None))
        offset = match.end()
    if offset < len(value):
        parts.append((value[offset:], None))
    return parts


TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\b(?:true|false|null)\b|[{}\[\]]')
COLON = re.compile(r'\s*:')


def json_spans(source):
    nesting = 0
    for match in TOKEN.finditer(source):
        token = match.group()
        if token.startswith('"'):
            kind = 'key' if COLON.match(source, match.end()) else 'type' if token.startswith('"Torappu.') else 'string'
        elif token in ('true', 'false', 'null'):
            kind = 'keyword'
        elif token in '{}[]':
            nesting = max(0, nesting - int(token in '}]'))
            kind = f'bracket{nesting % 3}'
            nesting += int(token in '{[')
        else:
            kind = 'number'
        yield match.start(), match.end(), kind


@dataclass
class DocumentRow:
    path: tuple
    depth: int
    text: str
    role: str = 'body'
    foldable: bool = False

# 文档嵌套解析
def document_rows(document, collapsed=frozenset()):
    def visit(part, path=(), depth=0):
        if isinstance(part, list):
            for i, child in enumerate(part):
                yield from visit(child, path + (i,), depth)
        elif not isinstance(part, dict):
            yield DocumentRow(path, depth, str(part))
        else:
            # 正文
            children = part.get('children') or []
            foldable = bool(children or part.get('description'))
            # Children control folding, never the semantic color of an action.
            role = part.get('role')
            if role not in ('heading', 'section', 'condition', 'description', 'body'):
                role = 'heading' if depth == 0 else 'body'
            if part.get('main'):
                yield DocumentRow(path, depth, str(part['main']), role, foldable=foldable)
            if not part.get("last_one"):
                if part.get('true') :
                    yield DocumentRow(path, depth, "若"+str(part['true'])+"...", 'condition', foldable=foldable)
                elif part.get('false'):
                    yield DocumentRow(path, depth, "若"+str(part['false'])+"，则直接跳出", 'condition', foldable=foldable)

            # 子部分
            if path not in collapsed:
                if part.get('description'):
                    yield DocumentRow(path + ('description',), depth + 1, str(part['description']), 'description')
                for i, child in enumerate(children):
                    yield from visit(child, path + (i,), depth + 1)
    return list(visit(document))


def default_folds(document):
    paths = set()
    def visit(part, path=()):
        if isinstance(part, dict):
            if part.get('style_closed'):
                paths.add(path)
            for i, child in enumerate(part.get('children') or []):
                visit(child, path + (i,))
        elif isinstance(part, list):
            for i, child in enumerate(part):
                visit(child, path + (i,))
    visit(document)
    return paths
