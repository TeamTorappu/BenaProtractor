# AI 翻译讲解：结构、用法与拓展指南

《贝娜的量角器》里的 AI **只做一件事：在翻译阶段补足引擎翻不出来的部分**，
外加一个「对当前条目提简单问题」的小问答口子。它不是聊天机器人，也不参与机制判定。

## 1. 为什么 AI 只接在翻译阶段

- 引擎（`bena.py` / `anne.py` / `node_translator/` / `relic_translator/`）是**确定性**的：
  数值、条件、Buff 关系全部来自游戏数据，这部分交给 AI 只会变差。
- 真正翻不出来的是「标识词」：未覆盖的 Node 名、未收录的 Buff key、纯英文枚举值。
  这些恰好是 LLM 擅长的短词翻译。
- 所以 AI 的定位是**后处理器**：引擎先出译文树，AI 只在用户点「译」时补那几个片段。

## 2. 工作流

```
选中条目
   ↓  引擎翻译（anne，在后台线程里跑，不阻塞界面）
译文树（未译片段带「（未翻译）」等标记）
   ↓  ai/fragments.py 收集候选片段（标记式 + 启发式）
侧栏列出片段 →「翻译」（单条）或「全部翻译」（顺序跑完整条，可中途停止）
   ↓  ai/api.py → Provider → 流式回填侧栏
「应用」（单条）/「全部应用」（一次性写回）
   ↓
ai/decorate.py 把译文旁挂到节点上（ai_text / ai_status / ai_origin），UI 重新渲染
   ↓
.bena_cache/ai/translations.jsonl 缓存（下次同片段直接命中）
```

侧栏还能做两件事：
- **定位**：在译文树里展开祖先并滚到该片段对应的那一行（`FluentProtractor.locate_node`）。
- **导出条目**：把当前条目的完整译文（含已应用的 AI 译文）导出成 Markdown，
  写到 `.bena_cache/ai/export/item_*.md` 并复制到剪贴板；「导出翻译记录」则是导出缓存表格。

关键设计：

- **引擎零改动**：`anne.py` 一行都不用改。AI 字段是旁挂的（`ai_status` / `ai_text` / `ai_origin`），
  引擎自己的 `main` 原文永远保留在 `ai_origin`，所以 `anne.py` 里
  `main.endswith("（未翻译）")` 之类的判断不会被打乱。
- **只改显示，不改数据**：应用 AI 译文只影响 `main` 的显示文本（形如 `充能类Buff（ChargeBuff）`），
  随时可以右键「让 AI 翻译这一行」重来。
- **不自动改字典**：结果只写 `.bena_cache/ai/`，永远不会自动合并进
  `translation/bena_dictionary.json`。觉得译得好，用「导出缓存」导出 Markdown 再人工提 PR。
- **网络只在子线程**：所有请求走 `ui/qt_workers.py` 的 QThread，界面不会卡；
  工作线程只看译文快照（主线程深拷贝），避免和引擎的就地规整抢数据。

## 2.1 片段从哪来

| 来源 | 说明 | 例子 |
| --- | --- | --- |
| 标记式 | 引擎自己标了「（未翻译）」「（翻译失败）」「未找到相应名称的Buff模板」 | `PalsyBuffAdd（未翻译）` |
| 启发式 | 整行一个中文字都没有、又含 ≥3 个连续字母（可在设置里关掉） | `CheckAbnormalResistance`、`PALSY`、`BUFF_OWNER` |
| 手动 | 译文树右键「让 AI 翻译这一行」 | 任意一行 |

启发式可以去设置里关掉；关掉后只处理引擎明确标记过的片段。
`$type`、`true/false`、裸数字这些不会进列表；`ON_X（ON_X）` 这种自注释也会先去重再送出去。

拒绝规则：模型返回空、原样返回、或返回内容里完全没有中文，都不会被写回（避免把 `<palsy[stack]>` 这种标识弄坏）。

## 3. 配置

第一次打开「AI 设置」时会生成 `.bena_ai.json`（已 gitignore，也不会进打包产物）：

```json
{
  "provider": "openai_compatible",
  "base_url": "https://api.deepseek.com/v1",
  "model": "deepseek-chat",
  "api_key": "",
  "temperature": 0.2,
  "max_tokens": 512,
  "reasoning_effort": "low",
  "request_timeout": 60,
  "context_char_budget": 12000,
  "prompt_version": 1,
  "enable_heuristic_fragments": true,
  "auto_translate_on_select": false
}
```

- **任何 OpenAI 兼容接口都能用**：DeepSeek、硅基流动、Moonshot、OpenAI；
  本地模型用 Ollama（`http://127.0.0.1:11434/v1/`）或 LM Studio（`http://127.0.0.1:1234/v1`）时
  `api_key` 可以留空。
- **key 也可以放环境变量**：`BENA_AI_KEY` / `BENA_AI_BASE` / `BENA_AI_MODEL` / `BENA_AI_PROVIDER`，
  优先级高于配置文件（适合不想把 key 写进磁盘的场景）。
- `reasoning_effort` 会随请求下发；如果服务端不认这个字段（返回 400 并提到它），
  客户端会自动去掉它重试一次。设置里选「不下发」即可彻底关掉。
- `enable_heuristic_fragments`：把「一个中文字都没有、又含有字母」的行也列进待译片段。
  关掉后只处理引擎明确标了「（未翻译）」「（翻译失败）」的片段。
- `auto_translate_on_select`：默认关闭（手动逐个点译）。打开后选中条目会自动开始翻译第一个片段。

## 4. 缓存

- 位置：`.bena_cache/ai/translations.jsonl`（一行一条，追加写）。
- key = `sha1(provider + model + prompt_version + 条目 + 位置 + 片段文本)`，
  所以换模型、改提示词版本都会自动失效，不会串味。
- 导出：侧边栏「导出缓存」或设置里的按钮 → `.bena_cache/ai/export/*.md`（表格形式，便于校对与提 PR）。

## 5. 给开发者：怎么加一个 Provider

1. 在 `ai/providers/` 新建模块，实现 `AIProvider`（`ai/providers/base.py`）的接口：

```python
class MyProvider(AIProvider):
    name = "my_provider"
    supports_effort = False

    def chat(self, messages, on_delta=None, cancel=None, **options):
        """messages: [{"role": "system"/"user"/"assistant", "content": "..."}]
        on_delta: 每收到一段增量就调用一次（流式）
        cancel:   threading.Event，置位后尽快抛 ProviderCancelled
        返回完整回复字符串；出错抛 ProviderError（消息要能直接给用户看）
        """
```

2. 在 `ai/registry.py` 的 `PROVIDERS` 里登记，并在 `PROVIDER_CHOICES` 里加上显示名。
3. 配置里把 `provider` 改成新名字即可，UI 与引擎都不用动。

## 6. 给开发者：怎么加一个新的 AI 动作

目前侧边栏有四类动作：片段翻译（单条 / 全部翻译）、整行翻译（右键）、简单问答（底部输入框）、
导出（当前条目 / 缓存）。要加动作（例如「整条机制总览」「整类条目预翻」）：

1. 在 `ai/prompts.py` 加提示词模板；
2. 在 `ai/api.py` 加一个函数（负责拼上下文、挑提示词、调 Provider、写缓存）；
3. 在 `ui/qt_workers.py` 加一个 QThread 包装（不许在 UI 线程里发网络请求）；
   参考 `AITranslateWorker`（单条）与 `ItemTranslateWorker`（引擎翻译，纯计算）；
4. 在 `ui/qt_ai_sidebar.py` 加按钮或右键菜单项；
   如果要「批量顺序执行」，照 `AISidebar.translate_all()` 的写法：
   用 `_batch_running` / `_batch_stop` 两个标志 + `_pump_batch()` 在每次完成回调里推进下一条，
   这样天然不会并发冲击服务端，也随时能停。

## 7. 测试

`python tests/run_tests.py`（139 个用例）覆盖：

- `test_fragments`：片段收集（标记式 / 启发式 / 关闭启发式 / 面包屑 / 分组）
- `test_decorate`：回写与重置，以及「引擎标记字面量必须保留」这条不变量
- `test_provider_contract`：用一个本地 `http.server` 假装服务端，验证
  SSE 流式拼接、鉴权头、非流式模式、`reasoning_effort` 降级重试、HTTP 500 / 非 JSON / 流内错误 / 取消
- `test_cache`：key 随模型与提示词版本失效、落盘重载、坏行容错、导出
- `test_context`：上下文预算截断、占位符保留、提示词约束
- `test_search` / `test_debounce`：片段与目录搜索的匹配、防抖
- `test_anne_dictionary`：字典查表容错（缺 catalogue / 空键不再抛异常）

界面侧的端到端自查（不联网、用本地假 AI 服务）：
`python tools/probe_batch_ai.py` —— 跑通「后台翻译 → 全部翻译 → 全部应用 → 定位 → 导出」。

这些测试**不联网、不消耗任何额度**。
