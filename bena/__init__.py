#----------------------------------------
# 贝娜 - 分析组件
# 将yj的json解读为可以查询的数据
#----------------------------------------

CATALOG = None

from .catalog import Catalog
from .translate_buff_name import translate_buff_name

# 询问贝娜一个ID有没有对应的数据，若没有将原路返回
def ask_bena(_type,input_id):
    return CATALOG.groups.get(_type, {}).get(input_id)

# 询问贝娜一个角色ID有没有对应的名字，若没有将原路返回
def ask_bena_character(character_id: str):
    # 对照表里同时存了短名与全名，理论上可以兼容搜索
    if character_id in CATALOG.character_display_names:
        return CATALOG.character_display_names[character_id]
    return character_id # 找不到，原路返回

# 询问贝娜一个敌人ID有没有对应的名字，若没有将原路返回
def ask_bena_enemy(enemy_id: str):
    # 对照表里同时存了短名与全名，理论上可以兼容搜索
    if enemy_id in CATALOG.enemy_display_names:
        return CATALOG.enemy_display_names[enemy_id]
    return enemy_id # 找不到，原路返回

print("[贝娜]我叫贝娜，来找一个出门就忘了回家的笨蛋。听说她还有些活要干，没办法，我也在这陪她一会好了。")