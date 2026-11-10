#----------------------------------------
# 藏品最终乘算效果
#----------------------------------------
import math

from bena import ask_bena
from .attribute_rune import char_attribute_mul, layer_char_attribute_mul

# 角色属性最终乘算Buff（偷懒翻译）
def char_attribute_final_scaler(item_type,blackboard):
    result = char_attribute_mul(item_type,blackboard)
    result["main"] = result["main"].replace("藏品符文","藏品符文终乘").replace("+","×")
    return result

# 依照层数提供角色属性最终乘算Buff（偷懒翻译）
def layer_char_attribute_final_scaler(item_type,blackboard):
    result = layer_char_attribute_mul(item_type,blackboard)
    result["main"] = result["main"].replace("藏品符文","藏品符文终乘").replace("+","×")
    return result