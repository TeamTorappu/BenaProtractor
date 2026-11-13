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

# 加载顺序从小到大
from .node import Node
from .action import Action
from .event_to_action import EventToAction
from .buff_template import BuffTemplate
from .rune import Rune
from .relic import Relic
from .buff import Buff
from .global_buff import GlobalBuff
from .rogue_item import RogueItem
from .autochess_garrison import AutochessGarrison
from .autochess_char_chess import AutochessCharChess
from .autochess_band import AutochessBand

print("[安妮]嗯。")