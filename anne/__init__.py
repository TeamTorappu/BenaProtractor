#----------------------------------------
# 安妮 - 翻译组件
# 将读取到的数据翻译转写成对应“人类语”
#----------------------------------------
# 任何翻译器的返回数据结构大概都长这样：
#{
#    "main" : 核心显示文本,
#    "description" : [备注(可选)],
#    "true" : [逻辑真时怎么称呼(可选)],
#    "false" : [逻辑假时怎么称呼(可选)],
#    "children" : [
#        {"main" : ... , "children" : ...},
#        {"main" : ...}
#    ],
#}

from .anne_node import *
from .anne_buff import *
from .anne_global_buff import *
from .anne_relic import *
from .anne_rune import *
from .anne_autochess import *

print("[安妮]嗯。")