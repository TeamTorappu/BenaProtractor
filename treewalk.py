'''
译文结构规范化与遍历
实现放在 ai/treewalk.py（ui 与 ai 共用），这里只是根目录的转发入口，
方便 `import treewalk` 这种写法。
'''
from ai.treewalk import (  # noqa: F401
    AI_KEYS,
    OPTIONAL_KEYS,
    children_of,
    normalize,
    text_lines,
    to_text,
    walk,
    walk_text,
)

__all__ = [
    "AI_KEYS","OPTIONAL_KEYS","children_of","normalize",
    "text_lines","to_text","walk","walk_text",
]
