'''
OpenAI 兼容 /chat/completions（含 SSE 流式）
覆盖：DeepSeek、硅基流动、Moonshot、OpenAI、Ollama(/v1)、LM Studio、vLLM 等
只用标准库，不引入 requests / openai。
'''
import json
import socket
import urllib.error
import urllib.request

from ai.providers.base import AIProvider, ProviderCancelled, ProviderError

SSE_DONE = "[DONE]"


class OpenAICompatibleProvider(AIProvider):
    name = "openai_compatible"
    supports_effort = True

    # ----------------------------------------
    # 组装请求
    # ----------------------------------------
    def _endpoint(self):
        base_url = str(self.config.get("base_url","")).strip().rstrip("/")
        if base_url == "":
            raise ProviderError("还没配置 base_url（AI 设置里填一个 OpenAI 兼容地址）")
        if base_url.endswith("/chat/completions"):
            return base_url
        return base_url + "/chat/completions"

    def _headers(self):
        headers = {
            "Content-Type" : "application/json",
            "Accept" : "text/event-stream, application/json",
            "User-Agent" : "BenaProtractor/ai",
        }
        api_key = str(self.config.get("api_key","")).strip()
        if api_key:
            headers["Authorization"] = "Bearer " + api_key
        return headers

    def _payload(self,messages,stream,options):
        # 先校验地址再校验模型，这样报错能指到真正缺的那个
        self._endpoint()
        model = str(self.config.get("model","")).strip()
        if model == "":
            raise ProviderError("还没配置 model（AI 设置里填模型名，例如 deepseek-chat）")
        payload = {
            "model" : model,
            "messages" : messages,
            "stream" : bool(stream),
            "temperature" : options.get("temperature",self.config.get("temperature",0.2)),
            "max_tokens" : options.get("max_tokens",self.config.get("max_tokens",512)),
        }
        effort = options.get("reasoning_effort",self.config.get("reasoning_effort",""))
        if effort:
            payload["reasoning_effort"] = effort
        return payload

    # ----------------------------------------
    # 主流程
    # ----------------------------------------
    def chat(self,messages,on_delta=None,cancel=None,**options):
        want_stream = bool(on_delta is not None and options.get("stream",True))
        try:
            if want_stream:
                return self._chat_stream(messages,on_delta,cancel,options)
            return self._chat_once(messages,cancel,options)
        except ProviderError as error:
            # reasoning_effort 不被支持时降级重试一次
            if getattr(error,"status",None) == 400 and "reasoning_effort" in str(error):
                self.last_used_fallback = True
                self.config = dict(self.config)
                self.config["reasoning_effort"] = ""
                if want_stream:
                    return self._chat_stream(messages,on_delta,cancel,options)
                return self._chat_once(messages,cancel,options)
            raise

    def _open(self,payload):
        request = urllib.request.Request(
            self._endpoint(),
            data=json.dumps(payload,ensure_ascii=False).encode("UTF-8"),
            headers=self._headers(),
            method="POST")
        timeout = float(self.config.get("request_timeout",60))
        try:
            return urllib.request.urlopen(request,timeout=timeout)
        except urllib.error.HTTPError as error:
            detail = ""
            try:
                detail = error.read().decode("UTF-8","replace")[:600]
            except Exception:
                pass
            message = f"服务返回 HTTP {error.code}"
            if detail:
                message += f"：{detail}"
            wrapped = ProviderError(message)
            wrapped.status = error.code
            raise wrapped from error
        except urllib.error.URLError as error:
            raise ProviderError(f"连不上 AI 服务（{error.reason}）。检查网络、base_url 或代理设置。") from error
        except socket.timeout as error:
            raise ProviderError("请求超时，可以在 AI 设置里把超时时间调大。") from error

    # ----------------------------------------
    # 非流式
    # ----------------------------------------
    def _chat_once(self,messages,cancel,options):
        if cancel is not None and cancel.is_set():
            raise ProviderCancelled("已取消")
        payload = self._payload(messages,False,options)
        with self._open(payload) as response:
            raw = response.read().decode("UTF-8","replace")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ProviderError("服务返回的不是合法 JSON：" + raw[:200]) from error
        return self._extract_content(data)

    @staticmethod
    def _extract_content(data):
        if isinstance(data,dict) and "error" in data and data["error"]:
            error = data["error"]
            message = error.get("message") if isinstance(error,dict) else str(error)
            raise ProviderError("AI 服务报错：" + str(message))
        try:
            choices = data["choices"]
            message = choices[0]["message"]
            content = message.get("content")
        except (KeyError,IndexError,TypeError) as error:
            raise ProviderError("看不懂服务返回的结构：" + json.dumps(data,ensure_ascii=False)[:200]) from error
        if content is None:
            content = ""
        return str(content)

    # ----------------------------------------
    # 流式（SSE）
    # ----------------------------------------
    def _chat_stream(self,messages,on_delta,cancel,options):
        payload = self._payload(messages,True,options)
        chunks = []
        with self._open(payload) as response:
            for line in response:
                if cancel is not None and cancel.is_set():
                    raise ProviderCancelled("已取消")
                if not line:
                    continue
                text = line.decode("UTF-8","replace").strip()
                if text == "" or text.startswith(":"):
                    continue
                if not text.startswith("data:"):
                    continue
                data_text = text[5:].strip()
                if data_text == SSE_DONE:
                    break
                try:
                    data = json.loads(data_text)
                except json.JSONDecodeError:
                    continue
                delta = self._extract_delta(data)
                if delta:
                    chunks.append(delta)
                    try:
                        on_delta(delta)
                    except Exception:
                        # 界面回调出错不该中断请求
                        pass
        return "".join(chunks)

    @staticmethod
    def _extract_delta(data):
        if isinstance(data,dict) and data.get("error"):
            error = data["error"]
            message = error.get("message") if isinstance(error,dict) else str(error)
            raise ProviderError("AI 服务报错：" + str(message))
        try:
            choice = data["choices"][0]
        except (KeyError,IndexError,TypeError):
            return ""
        delta = choice.get("delta") or {}
        content = delta.get("content")
        if content:
            return str(content)
        # 有的服务把内容直接放在 text 字段里
        text = choice.get("text")
        return str(text) if text else ""
