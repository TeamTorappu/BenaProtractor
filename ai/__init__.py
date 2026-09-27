'''
ai - AI 翻译 / 讲解
设计原则：
1. 引擎（bena / anne）完全不感知 AI，AI 只作为「译文的后处理器」存在；
2. 所有网络访问都收敛在 ai/providers/ 里，换模型/换协议只需要新增一个 Provider；
3. 结果只写 .bena_cache/ai/，永远不自动改 translation/*.json。
'''
