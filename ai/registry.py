'''
Provider 注册表
新增一个后端只需要：写一个 AIProvider 子类 → 在这里登记 → 配置里改 provider 名
'''
from ai.providers.base import AIProvider, ProviderError  # noqa: F401
from ai.providers.openai_compatible import OpenAICompatibleProvider

PROVIDERS = {
    OpenAICompatibleProvider.name : OpenAICompatibleProvider,
}

# 给设置界面用的下拉项：(值, 显示名)
PROVIDER_CHOICES = [
    ("openai_compatible","OpenAI 兼容（DeepSeek / 硅基流动 / Ollama / LM Studio…）"),
]

_CACHE = {}


def list_providers():
    return list(PROVIDERS.keys())


def get_provider(config=None,force_new=False):
    '''按配置实例化 Provider（同一个配置复用实例）'''
    if config is None:
        from ai import config as config_module
        config = config_module.load()
    name = str(config.get("provider","openai_compatible")).strip()
    if name not in PROVIDERS:
        available = "、".join(PROVIDERS.keys())
        raise ProviderError(f"不认识的 provider：{name!r}（可选：{available}）")
    key = (name,id(config)) if force_new else name
    if key not in _CACHE or force_new:
        _CACHE[key] = PROVIDERS[name](config)
    provider = _CACHE[key]
    provider.config = config
    return provider


def reset():
    _CACHE.clear()
