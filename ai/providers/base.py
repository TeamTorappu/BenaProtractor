'''
Provider 抽象层
想接新模型/新协议时：
    1. 在本目录新增一个模块，写一个类实现 AIProvider 的接口；
    2. 在 ai/registry.py 的 PROVIDERS 里登记名字；
    3. 配置里把 provider 改成这个名字即可，UI 与引擎都不用动。
'''
import threading


class ProviderError(Exception):
    '''AI 调用出问题时统一抛这个（消息面向用户，可直接显示）'''


class ProviderCancelled(ProviderError):
    '''用户主动取消'''


class AIProvider:
    '''所有 Provider 的共同接口'''

    name = "base"
    # 这个 Provider 是否支持 reasoning_effort 之类的推理强度参数
    supports_effort = True

    def __init__(self,config=None):
        self.config = config or {}
        self.last_used_fallback = False # 上一次请求是否因为参数不被支持而降级重试过

    # ---------------- 必须实现 ----------------
    def chat(self,messages,on_delta=None,cancel=None,**options):
        '''发一轮对话，返回完整回复文本。

        messages: [{"role": "system"/"user"/"assistant", "content": "..."}]
        on_delta: 可选回调，收到流式增量时调用 on_delta(text)
        cancel:   可选 threading.Event，置位后尽快抛 ProviderCancelled
        options:  覆盖 temperature / max_tokens / reasoning_effort
        '''
        raise NotImplementedError

    # ---------------- 便捷封装 ----------------
    def translate(self,text,messages,on_delta=None,cancel=None):
        '''翻译一个片段（走 chat，便于统一重试/统计）'''
        return self.chat(messages,on_delta=on_delta,cancel=cancel)

    def ask(self,messages,on_delta=None,cancel=None):
        '''简单问答'''
        return self.chat(messages,on_delta=on_delta,cancel=cancel)

    # ---------------- 工具 ----------------
    @staticmethod
    def make_cancel_event():
        return threading.Event()

    def describe(self):
        return f"{self.name}({self.config.get('model','?')})"
