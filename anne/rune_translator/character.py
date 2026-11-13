#----------------------------------------
# 角色类符文
#----------------------------------------
from analyzer import is_attribute_key,to_percent,analyze_selector
from dictionary import anne_dictionary

# 角色属性乘法符文
def char_attribute_mul(selector,blackboard):
    modifiers = []
    for key,value in blackboard.items():
        if is_attribute_key(key):
            name = anne_dictionary("attribute",key.upper())
            power = to_percent(value) # ×X%
            modifiers.append(f"{name}×{power}")
    # 选择器目标处理
    selector = analyze_selector(blackboard,"我方")
    hint = "（均为乘法符文）" if len(modifiers) > 1 else "（乘法符文）"
    return {"main" : f"所有{selector}{'、'.join(modifiers)}{hint}"}