'''
后台工作者（QThread）
界面线程只负责显示；所有网络请求都在这里跑，通过 signal 把增量送回主线程。

约定：工作线程只读传入的译文快照——快照在主线程用 copy_translation() 深拷贝好，
避免子线程里的 normalize 就地规整与界面读取打架。
'''
import json
import threading

from PySide6.QtCore import QThread, Signal

from ai import api
from ai.providers.base import ProviderCancelled, ProviderError


def copy_translation(translation):
    '''给工作线程用的深拷贝（译文结构只有 dict/list/str/数字，json 往返即可）'''
    if translation is None:
        return None
    try:
        return json.loads(json.dumps(translation,ensure_ascii=False))
    except (TypeError,ValueError):
        return None


def translate_item(data_type,obj):
    '''把某个条目翻译成可显示的结构（纯函数，供 ItemTranslateWorker 在后台跑）

    与 qt_ui.show_selected 原先的 if-elif 完全等价，只是搬到了工作线程：
    译文模板动辄上千个节点，在主线程里翻会让「切换条目」明显卡顿。
    返回 (译文结构, 原文)；译文结构为 None 表示这条只能看原文（兜底展示）。
    '''
    import anne
    if data_type == "buff":
        return anne.translate_whole_buff(obj),f'"{obj.buff_key}" :' + obj.get_raw_data()
    if data_type == "global_buff":
        return (anne.translate_whole_global_buff(obj),
                f'"{obj.buff_key}" :' + obj.get_raw_data())
    if data_type == "buff_template":
        return (anne.translate_whole_buff_template(obj),
                f'"{obj.buff_key}" :' + obj.get_raw_data())
    if data_type == "rogue_item":
        raw = [obj.item_info,obj.item_data] if obj.has_effect else obj.item_info
        return anne.translate_whole_rogue_item(obj),raw
    if isinstance(obj,(dict,list)):
        return None,obj
    return None,obj


class ItemTranslateWorker(QThread):
    '''在后台翻译一个条目（切换条目不再阻塞界面）

    线程契约（HANDOVER §7.1）：
      - 调用方必须留强引用，且只在 finished 里清空；
      - 结果通过信号送回主线程，工作线程里只做纯计算，不碰任何控件。
    '''
    finished_ok = Signal(str,object,object)   # item_key, translation, raw
    failed = Signal(str,str)                  # item_key, message

    def __init__(self,item_key,data_type,obj,parent=None):
        super().__init__(parent)
        self.item_key = item_key
        self.data_type = data_type
        self.obj = obj

    def run(self):
        try:
            translation,raw = translate_item(self.data_type,self.obj)
            self.finished_ok.emit(self.item_key,translation,raw)
        except Exception as error:            # 引擎侧任何异常都要变成可读提示，不能带走进程
            self.failed.emit(self.item_key,f"{type(error).__name__}: {error}")


class AITranslateWorker(QThread):
    '''翻译一个片段（可能对应多个出现位置）'''
    delta = Signal(str)
    finished_ok = Signal(str)     # 完整译文
    failed = Signal(str)

    def __init__(self,group,item_desc,item_key,parent=None):
        super().__init__(parent)
        self.group = group            # [Fragment, ...]
        self.item_desc = item_desc
        self.item_key = item_key
        # 事件在构造时就建好：万一 run() 还没开始就有人调 cancel()，取消也不会丢
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        self.cancel_event.clear()
        fragment = self.group[0]
        try:
            def _delta(text):
                if self.cancel_event.is_set():
                    raise ProviderCancelled("已取消")
                self.delta.emit(text)
            result = api.translate_text(
                fragment.candidate,
                self.item_desc,
                fragment.breadcrumb_text,
                on_delta=_delta,
                cancel=self.cancel_event,
                item_key=self.item_key,
                extra=fragment.node_path,
            )
            if self.cancel_event.is_set():
                self.failed.emit("已取消")
                return
            self.finished_ok.emit(result or "")
        except ProviderCancelled:
            self.failed.emit("已取消")
        except ProviderError as error:
            self.failed.emit(str(error))
        except Exception as error:  # 兜底，界面不该因为未知异常崩掉
            self.failed.emit(f"{type(error).__name__}: {error}")


class AIAskWorker(QThread):
    '''自由追问 / 解释某一行'''
    # 注意：QThread 自带 started 信号（线程启动时发），别覆盖它；
    # 这里用 request_started 表示「真的要发请求了」，界面据此打 [AI] 标记。
    request_started = Signal()
    delta = Signal(str)
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self,question,item_desc,translation,node_path=None,line=None,parent=None):
        super().__init__(parent)
        self.question = question
        self.item_desc = item_desc
        self.translation = copy_translation(translation)
        self.node_path = node_path
        self.line = line
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        self.cancel_event.clear()
        self.request_started.emit()
        try:
            def _delta(text):
                if self.cancel_event.is_set():
                    raise ProviderCancelled("已取消")
                self.delta.emit(text)
            if self.node_path:
                result = api.explain_node(self.question,self.item_desc,self.translation,
                                          node_path=self.node_path,line=self.line or "",
                                          on_delta=_delta,cancel=self.cancel_event)
            else:
                result = api.explain(self.question,self.item_desc,self.translation,
                                     on_delta=_delta,cancel=self.cancel_event)
            if self.cancel_event.is_set():
                self.failed.emit("已取消")
                return
            self.finished_ok.emit(result or "")
        except ProviderCancelled:
            self.failed.emit("已取消")
        except ProviderError as error:
            self.failed.emit(str(error))
        except Exception as error:
            self.failed.emit(f"{type(error).__name__}: {error}")
