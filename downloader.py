'''
下载明日方舟游戏数据
分发版第一次启动时由用户自己下载，所以这里要考虑：
- 文件不小（character_table 约 15MB、roguelike_topic_table 约 18MB、enemy_database 约 40MB+）
- 网络可能断，支持断点续传（.part 临时文件 + HTTP Range）
- 界面要能显示进度，所以提供 progress_cb 回调
'''
import os
import sys
import time
import urllib.error
import urllib.request

# Github仓库的根文件夹
WEB = "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/refs/heads/master/zh_CN/gamedata/"
#WEB = "https://torappu.prts.wiki/gamedata/latest/"
#WEB = "https://raw.githubusercontent.com/ArknightsAssets/ArknightsGamedata/refs/heads/master/cn/gamedata/"

# 需要下载的文件
# 以简体中文版数据为准（通常会是最新的）
FILES = {
    "buff_table.json" : "buff_table.json",
    "character_table.json" : "excel/character_table.json",
    "roguelike_topic_table.json" : "excel/roguelike_topic_table.json",
    "buff_template_data.json" : "battle/buff_template_data.json",
    "enemy_database.json" : "levels/enemydata/enemy_database.json"
}

TABLE_DIR = "./tables"
CHUNK_SIZE = 256 * 1024
MAX_RETRY = 3
RETRY_WAIT = 3


class DownloadError(IOError):
    '''下载失败（供界面辨认并给出「重试」）'''


def human_size(size):
    size = float(size)
    for unit in ("B","KB","MB","GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"


def missing_files():
    missing = []
    for name in FILES:
        path = os.path.join(TABLE_DIR,name)
        if not (os.path.exists(path) and os.path.getsize(path) > 0):
            missing.append(name)
    return missing


def total_bytes():
    '''当前 tables 目录里已就位的数据总量'''
    total = 0
    for name in FILES:
        path = os.path.join(TABLE_DIR,name)
        if os.path.exists(path):
            total += os.path.getsize(path)
    return total


def _report(progress_cb,name,current,total,stage=None):
    if progress_cb is None:
        return
    try:
        progress_cb(name,current,total,stage)
    except TypeError:
        # 兼容只接受 (name, current, total) 的回调
        try:
            progress_cb(name,current,total)
        except Exception:
            pass
    except Exception:
        # 界面回调出错不该拖垮下载
        pass


def _console_progress(name,current,total,stage=None):
    if total:
        percent = min(current / total,1.0) * 100
        sys.stdout.write(f"\r[贝娜]下载 {name} {percent:6.2f}%  "
                         f"{human_size(current)}/{human_size(total)}")
    else:
        sys.stdout.write(f"\r[贝娜]下载 {name} {human_size(current)}")
    sys.stdout.flush()


def _download_one(name,relative,progress_cb=None):
    '''下载单个文件，支持断点续传；返回 (新增字节, 失败原因或 None)'''
    target = os.path.join(TABLE_DIR,name)
    part = target + ".part"
    url = WEB + relative
    added = 0

    resume_at = os.path.getsize(part) if os.path.exists(part) else 0
    headers = {"User-Agent" : "BenaProtractor/downloader"}
    if resume_at > 0:
        headers["Range"] = f"bytes={resume_at}-"
    request = urllib.request.Request(url,headers=headers)
    try:
        response = urllib.request.urlopen(request,timeout=30)
    except urllib.error.HTTPError as error:
        if error.code == 416 and resume_at > 0:
            # 本地那份其实已经下完了
            os.replace(part,target)
            return added,None
        return added,f"HTTP {error.code}"
    except Exception as error:
        return added,f"{type(error).__name__}: {error}"

    with response:
        content_length = int(response.headers.get("Content-Length") or 0)
        total = content_length + resume_at if content_length else 0
        mode = "ab" if (resume_at > 0 and response.status == 206) else "wb"
        if mode == "wb":
            resume_at = 0
            added = 0
        current = resume_at
        _report(progress_cb,name,current,total,"start")
        with open(part,mode) as file:
            while True:
                try:
                    chunk = response.read(CHUNK_SIZE)
                except Exception as error:
                    return added,f"读取中断：{type(error).__name__}: {error}"
                if not chunk:
                    break
                file.write(chunk)
                current += len(chunk)
                added += len(chunk)
                _report(progress_cb,name,current,total,"running")
        if total and current < total:
            return added,f"连接提前结束（{human_size(current)}/{human_size(total)}）"
    os.replace(part,target)
    return added,None


def download_file(name,relative=None,progress_cb=None):
    '''带重试的下载；失败抛 DownloadError'''
    relative = relative or FILES.get(name)
    if relative is None:
        raise DownloadError(f"没有 {name} 对应的下载地址")
    last_error = ""
    for attempt in range(1,MAX_RETRY + 1):
        added,error = _download_one(name,relative,progress_cb)
        if error is None:
            return added
        last_error = error
        print(f"\n[贝娜]{name} 第 {attempt} 次下载失败：{error}")
        if attempt < MAX_RETRY:
            _report(progress_cb,name,0,0,f"retry {attempt}")
            time.sleep(RETRY_WAIT)
    raise DownloadError(f"{name} 下载失败：{last_error}")


# 下载所需文件
def prepare_files(progress_cb=None):
    '''progress_cb(name, current, total, stage)

    stage: start / running / retry n / done / all_done
    没有传 progress_cb 时退化为控制台进度输出。
    '''
    callback = progress_cb if progress_cb is not None else _console_progress
    if not os.path.exists(TABLE_DIR):
        os.makedirs(TABLE_DIR,exist_ok=True)

    todo = missing_files()
    if todo:
        print("[贝娜]缺少所需文件，即将开始下载明日方舟游戏数据")
        print("[贝娜]数据总量约 70MB+；如果发现下载较慢/失败，建议启用网络代理（俗称梯子）后重试")
        print("[贝娜]下载支持断点续传，中断后重跑会接着下")

    for name in todo:
        print(f"[贝娜]尝试下载 {name}")
        try:
            download_file(name,FILES[name],callback)
        except DownloadError as error:
            print(f"\n[贝娜]{error}")
            # 失败的半成品留在原地，下次可以续传
            raise IOError("[贝娜]缺少文件，无法处理") from error
        _report(callback,name,0,0,"done")
        if progress_cb is None:
            print("")
        print(f"[贝娜]{name} 下载完成！")

    if not todo:
        print("[贝娜]游戏数据齐全，跳过下载")
    else:
        _report(callback,"","","","all_done")
    return missing_files()
