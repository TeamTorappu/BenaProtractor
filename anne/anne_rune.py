#----------------------------------------
# 安妮的符文翻译器
#----------------------------------------
import anne.rune_translator as rune_translator
    
# 翻译重定向器，本质switch case
# 翻译返回的结果始终是一层一层的结构体
def anne_rune_translate(rune_info):
    rune_key = rune_info.key
    print(f"[安妮]尝试翻译符文 {rune_key}")
    method = getattr(rune_translator, rune_key, "")
    if method != "" :
        translation = method(rune_info.selector,rune_info.blackboard)

# 全部翻译
def anne_rune_translate_all(rune_info_list):
    children = []
    for rune_info in rune_info_list:
        translation = anne_rune_translate(rune_info)
        children.append(translation)
    return {"main" : "","children" : children}