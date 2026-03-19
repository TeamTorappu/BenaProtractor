#----------------------------------------
# 逻辑类Node（都需要特别处理，因此均不在这里处理）
#----------------------------------------
from .analyzer import anne_dictionary

# 逻辑 如果+否则
def node_IfElse(node):
    return {"main" : "如果...","true":"如果是...","false":"如果不是..."}

# 否则（但不在这里翻译）
def node_IfNot(node):
    return {"main" : "否则"}

# 始终执行
def node_AlwaysNext(node):
    return {"main" : "不论前一个节点是否成功，始终继续执行"}