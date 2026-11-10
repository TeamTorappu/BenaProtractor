#----------------------------------------
# 安妮的藏品翻译器
#----------------------------------------
from analyzer import analyze_relic_timing

from bena import ask_bena
import anne.relic_translator as relic_translator
    
# 翻译重定向器，本质switch case
# 翻译返回的结果始终是一层一层的结构体
def anne_relic_translate(rogue_effect):
    effect_key = rogue_effect.key
    print(f"[安妮]尝试翻译藏品 {effect_key}")
    method = getattr(relic_translator, effect_key, "")
    if method != "" :
        translation = method(rogue_effect.type,rogue_effect.blackboard)
        if "global_buff" in translation: # 翻译全局Buff
            # 尝试寻找全局Buff
            gbuff = ask_bena("global_buff",translation["global_buff"])
            if gbuff == None:
                gbuff = ask_bena("global_buff",translation["global_buff"].lower()) #试试小写，Assetbundle的问题
            if gbuff != None:
                gbuff_translation = gbuff.translate(rogue_effect.blackboard)
                gbuff_translation["main"] = "战斗中："
                if len(translation["children"]) > 0:
                    translation["children"][0]["style_closed"] = True
                    translation["children"] = gbuff_translation["children"] + translation["children"]
                else:
                    translation["children"] += gbuff_translation["children"]
        return translation
    else: # 无法翻译，把所有数据搓成可阅读的格式
        prefix = analyze_relic_timing(rogue_effect.type,rogue_effect.blackboard)
        translation = {
            "main" : prefix+effect_key+"（未翻译）",
            "style_closed" : True,
            "children" : []
        }
        for key,bb in rogue_effect.blackboard.items():
            translation["children"].append({"main": str(key) + " : "+str(bb)})
    # 返回译文
    return translation

# 全部翻译
def anne_relic_translate_all(rogue_effect_list):
    children = []
    for rogue_effect in rogue_effect_list:
        translation = anne_relic_translate(rogue_effect)
        children.append(translation)
    return {"main" : "","children" : children}