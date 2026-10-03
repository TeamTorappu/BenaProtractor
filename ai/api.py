'''
AI 调用门面
UI 只需要用这里的函数，不用关心 Provider 怎么选、缓存怎么算、提示词怎么拼。
'''
from ai import cache, config as config_module, prompts
from ai.decorate import apply_fragment, find_node
from ai.fragments import already_translated, collect_fragments, pending_fragments
from ai.providers.base import ProviderCancelled, ProviderError
from ai.registry import get_provider
from ai.treewalk import to_text

__all__ = [
    "ProviderError","ProviderCancelled",
    "describe_provider","is_ready","missing_fields",
    "item_description","collect_fragments","pending_fragments",
    "translate_fragment","translate_text","explain","explain_node","apply_fragment",
    "find_node","export_cache","cache_stats",
]


# ----------------------------------------
# 配置相关的小工具
# ----------------------------------------
def describe_provider(config=None):
    config = config or config_module.load()
    return f"{config.get('provider')} · {config.get('model')} @ {config.get('base_url')}"


def is_ready(config=None):
    return config_module.is_configured(config)


def missing_fields(config=None):
    return config_module.missing_fields(config)


def item_description(data_type=None,data_key=None,display_name=None):
    '''给提示词用的条目说明'''
    pieces = []
    if display_name:
        pieces.append(str(display_name))
    if data_key:
        pieces.append(f"（{data_key}）")
    if data_type:
        pieces.append(f"[类型 {data_type}]")
    return " ".join(pieces) if pieces else "（未知条目）"


# ----------------------------------------
# 上下文
# ----------------------------------------
def _breadcrumb_text(fragment):
    if not fragment.breadcrumb:
        return ""
    crumbs = [crumb for crumb in fragment.breadcrumb if crumb]
    limit = int(config_module.get("max_context_breadcrumb",6) or 6)
    if len(crumbs) > limit:
        crumbs = crumbs[-limit:]
    return " > ".join(crumbs)


def translation_snapshot(translation,max_depth=None):
    '''交给模型的译文纯文本（会按 context_char_budget 截断）'''
    if translation is None:
        return ""
    budget = int(config_module.get("context_char_budget",12000) or 12000)
    text = to_text(translation,max_depth=-1 if max_depth is None else max_depth)
    if len(text) > budget:
        text = text[:budget] + "\n…（已截断）"
    return text


def branch_snapshot(translation,node_path,depth=1):
    '''取某一行的父级分支，用于「解释这一行」'''
    node = find_node(translation,node_path)
    if node is None:
        return ""
    parent_path = node_path.rsplit(".",1)[0] if "." in node_path else None
    if parent_path is None:
        return to_text(node)
    parent = find_node(translation,parent_path)
    if parent is None:
        return to_text(node)
    return to_text(parent,max_depth=depth)


# ----------------------------------------
# 翻译
# ----------------------------------------
def translate_text(text,item_desc="",breadcrumb="",on_delta=None,cancel=None,
                   use_cache=True,item_key="",extra=""):
    '''翻译一段文本；返回译文（失败抛 ProviderError）'''
    config = config_module.load()
    provider_name = str(config.get("provider",""))
    model = str(config.get("model",""))
    prompt_version = int(config.get("prompt_version",prompts.PROMPT_VERSION) or 1)
    if use_cache:
        cached = cache.get(text,item_key,provider_name,model,prompt_version,extra)
        if cached:
            if on_delta is not None:
                on_delta(cached)
            return cached
    provider = get_provider(config)
    messages = prompts.translate_messages(text,item_desc,breadcrumb)
    result = provider.chat(messages,on_delta=on_delta,cancel=cancel)
    result = (result or "").strip().strip('"').strip()
    if result:
        cache.put(text,result,item_key,provider_name,model,prompt_version,extra,
                  context=breadcrumb)
    return result


def translate_fragment(fragment,translation,item_desc="",item_key="",
                       on_delta=None,cancel=None,use_cache=True,apply=True):
    '''翻译一个片段；apply=True 时顺手写回译文结构'''
    result = translate_text(fragment.candidate,item_desc,_breadcrumb_text(fragment),
                            on_delta=on_delta,cancel=cancel,use_cache=use_cache,
                            item_key=item_key,extra=fragment.node_path)
    if apply and translation is not None and already_translated(fragment,result):
        apply_fragment(translation,fragment,result)
    return result


# ----------------------------------------
# 讲解 / 简单问答
# ----------------------------------------
def explain(question,item_desc="",translation=None,on_delta=None,cancel=None):
    config = config_module.load()
    provider = get_provider(config)
    messages = prompts.explain_messages(question,item_desc,translation_snapshot(translation))
    return provider.chat(messages,on_delta=on_delta,cancel=cancel,
                         max_tokens=config.get("max_tokens",512))


def explain_node(question,item_desc="",translation=None,node_path="",line="",
                 on_delta=None,cancel=None):
    config = config_module.load()
    provider = get_provider(config)
    messages = prompts.explain_messages(
        question,item_desc,translation_snapshot(translation),
        branch=branch_snapshot(translation,node_path),path=node_path,line=line)
    return provider.chat(messages,on_delta=on_delta,cancel=cancel,
                         max_tokens=config.get("max_tokens",512))


# ----------------------------------------
# 缓存相关
# ----------------------------------------
def export_cache(path=None):
    return cache.export_markdown(path)


def cache_stats():
    return cache.stats()
