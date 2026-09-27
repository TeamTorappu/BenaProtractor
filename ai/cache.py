'''
AI 结果缓存（单独一个目录，绝不碰仓库里的 translation/*.json）
布局：
    .bena_cache/ai/translations.jsonl   一行一条，追加写
    .bena_cache/ai/export/*.md          手动导出（方便日后提 PR 补字典）
key = sha1(provider + model + prompt_version + 条目上下文 + 待译片段)
换模型/改提示词版本 → key 变化 → 自动失效，不会串味。
'''
import hashlib
import json
import os
import threading
import time

CACHE_DIR = "./.bena_cache/ai"
CACHE_FILE = os.path.join(CACHE_DIR,"translations.jsonl")
EXPORT_DIR = os.path.join(CACHE_DIR,"export")

_LOCK = threading.Lock()
_INDEX = None      # key -> entry
_DIRTY = False


def _hash(text):
    return hashlib.sha1(text.encode("UTF-8")).hexdigest()


def make_key(candidate,item_key="",provider="",model="",prompt_version=1,extra=""):
    material = "|".join([
        str(provider),str(model),str(prompt_version),
        str(item_key),str(extra),str(candidate),
    ])
    return _hash(material)


def ensure_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR,exist_ok=True)
    return CACHE_DIR


def _load_index():
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    _INDEX = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE,"r",encoding="UTF-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    entry_key = entry.get("key")
                    if entry_key:
                        _INDEX[entry_key] = entry
        except OSError:
            pass
    return _INDEX


# 一个进程里只查内存，写的时候才落盘
def get(candidate,item_key="",provider="",model="",prompt_version=1,extra=""):
    key = make_key(candidate,item_key,provider,model,prompt_version,extra)
    entry = _load_index().get(key)
    if entry is None:
        return None
    return entry.get("translation")


def put(candidate,translation,item_key="",provider="",model="",prompt_version=1,
        extra="",context=""):
    if not translation:
        return None
    key = make_key(candidate,item_key,provider,model,prompt_version,extra)
    entry = {
        "key" : key,
        "text" : candidate,
        "translation" : translation,
        "item_key" : item_key,
        "provider" : provider,
        "model" : model,
        "prompt_version" : prompt_version,
        "context" : context,
        "created_at" : time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with _LOCK:
        _load_index()[key] = entry
        _append(entry)
    return key


def _append(entry):
    ensure_dir()
    try:
        with open(CACHE_FILE,"a",encoding="UTF-8") as file:
            file.write(json.dumps(entry,ensure_ascii=False) + "\n")
    except OSError as error:
        print("[AI]缓存写入失败："+str(error))


def all_entries():
    return list(_load_index().values())


def stats():
    entries = _load_index()
    return {
        "count" : len(entries),
        "file" : CACHE_FILE,
        "size" : os.path.getsize(CACHE_FILE) if os.path.exists(CACHE_FILE) else 0,
    }


def export_markdown(path=None,only_missing_keys=None):
    '''导出缓存内容为 Markdown，方便人工校对/提 PR'''
    ensure_dir()
    if path is None:
        os.makedirs(EXPORT_DIR,exist_ok=True)
        path = os.path.join(EXPORT_DIR,
                            "ai_translations_" + time.strftime("%Y%m%d_%H%M%S") + ".md")
    entries = sorted(_load_index().values(),key=lambda entry:(entry.get("item_key",""),
                                                             entry.get("text","")))
    lines = ["# AI 翻译缓存导出","",
             f"- 共 {len(entries)} 条",
             f"- 导出时间：{time.strftime('%Y-%m-%d %H:%M:%S')}","",
             "| 条目 | 原文片段 | AI 译文 | 模型 | 时间 |",
             "| --- | --- | --- | --- | --- |"]
    for entry in entries:
        lines.append("| {item} | {text} | {translation} | {model} | {time} |".format(
            item=(entry.get("item_key") or "").replace("|","\\|"),
            text=(entry.get("text") or "").replace("|","\\|"),
            translation=(entry.get("translation") or "").replace("|","\\|"),
            model=entry.get("model",""),
            time=entry.get("created_at","")))
    with open(path,"w",encoding="UTF-8") as file:
        file.write("\n".join(lines) + "\n")
    return path


def clear_memory():
    global _INDEX
    with _LOCK:
        _INDEX = None


def set_cache_dir(path):
    '''换缓存目录（测试用，顺带清掉内存索引）'''
    global CACHE_DIR, CACHE_FILE, EXPORT_DIR
    CACHE_DIR = path
    CACHE_FILE = os.path.join(path,"translations.jsonl")
    EXPORT_DIR = os.path.join(path,"export")
    clear_memory()
    return CACHE_DIR
