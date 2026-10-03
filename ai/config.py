'''
AI 配置
存在仓库根目录的 .bena_ai.json（已 gitignore，不进打包产物）。
key 也可以用环境变量覆盖，避免明文落盘：
    BENA_AI_KEY / BENA_AI_BASE / BENA_AI_MODEL / BENA_AI_PROVIDER
'''
import copy
import json
import os
import sys
import traceback


def runtime_root():
    '''源码运行时=仓库根目录；打包后=exe 所在目录'''
    if getattr(sys,"frozen",False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CONFIG_PATH = os.path.join(runtime_root(),".bena_ai.json")

DEFAULT_CONFIG = {
    "_comment" : [
        "AI 翻译配置。provider 目前只有 openai_compatible（DeepSeek / 硅基流动 / Ollama / LM Studio 等都能用）。",
        "本地模型（如 Ollama）base_url 填 http://127.0.0.1:11434/v1/ ，api_key 可以留空。",
        "reasoning_effort 会随请求下发（low 可以让回答更短更快）；不需要就留空字符串。",
        "api_key 也可以放在环境变量 BENA_AI_KEY 里，本文件留空。"
    ],
    "provider" : "openai_compatible",
    "base_url" : "https://api.deepseek.com/v1",
    "model" : "deepseek-chat",
    "api_key" : "",
    "temperature" : 0.2,
    "max_tokens" : 512,
    "reasoning_effort" : "low",
    "request_timeout" : 60,
    "context_char_budget" : 12000,
    "prompt_version" : 1,
    "enable_heuristic_fragments" : True,
    "auto_translate_on_select" : False,
    "system_prompt" : "",
    "max_context_breadcrumb" : 6,
}

_CONFIG = None


def load(force=False):
    global _CONFIG
    if _CONFIG is not None and not force:
        return _CONFIG
    config = copy.deepcopy(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            # utf-8-sig：容错带 BOM 的文件
            with open(CONFIG_PATH,"r",encoding="utf-8-sig") as file:
                loaded = json.load(file)
            if isinstance(loaded,dict):
                config.update(loaded)
        except Exception:
            print("[AI]配置文件读取失败，改用默认配置：")
            traceback.print_exc()
    # 环境变量覆盖
    env_map = {
        "BENA_AI_KEY" : "api_key",
        "BENA_AI_BASE" : "base_url",
        "BENA_AI_MODEL" : "model",
        "BENA_AI_PROVIDER" : "provider",
    }
    for env_name,key in env_map.items():
        value = os.environ.get(env_name)
        if value:
            config[key] = value
    _CONFIG = config
    return _CONFIG


def save(config=None):
    global _CONFIG
    if config is not None:
        _CONFIG = config
    if _CONFIG is None:
        return
    try:
        with open(CONFIG_PATH,"w",encoding="UTF-8") as file:
            file.write(json.dumps(_CONFIG,indent=4,ensure_ascii=False))
    except Exception:
        print("[AI]配置文件写入失败：")
        traceback.print_exc()


def get(key,default=None):
    return load().get(key,default)


def set_value(key,value,save_now=True):
    config = load()
    config[key] = value
    if save_now:
        save(config)
    return config


def is_configured(config=None):
    '''能不能发请求：地址和模型必须有；key 允许为空（本地模型）'''
    config = config or load()
    base_url = str(config.get("base_url","")).strip()
    model = str(config.get("model","")).strip()
    return bool(base_url) and bool(model)


def missing_fields(config=None):
    config = config or load()
    missing = []
    if not str(config.get("base_url","")).strip():
        missing.append("base_url")
    if not str(config.get("model","")).strip():
        missing.append("model")
    return missing


def masked_key(config=None):
    config = config or load()
    key = str(config.get("api_key",""))
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def describe(config=None):
    config = config or load()
    return f"{config.get('provider')} / {config.get('base_url')} / {config.get('model')}"
