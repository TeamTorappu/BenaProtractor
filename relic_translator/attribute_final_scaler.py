#----------------------------------------
# 藏品最终乘算效果
#----------------------------------------
import math

from bena import ask_bena
from .attribute_rune import rogue_char_attribute_mul, rogue_layer_char_attribute_mul

# 角色属性最终乘算Buff（偷懒翻译）
def rogue_char_attribute_final_scaler(item_type,blackboard):
    result = rogue_char_attribute_mul(item_type,blackboard)
    result["main"] = result["main"].replace("藏品符文","藏品最终乘算")
    return result

# 依照层数提供角色属性最终乘算Buff（偷懒翻译）
def rogue_layer_char_attribute_final_scaler(item_type,blackboard):
    result = rogue_layer_char_attribute_mul(item_type,blackboard)
    result["main"] = result["main"].replace("藏品符文","藏品最终乘算")
    return result