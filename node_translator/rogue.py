#----------------------------------------
# 肉鸽特色Node
#----------------------------------------
from translator import anne_dictionary

# 检查角色是否已秉烛
def node_RoguelikeFilterCharacterInCandleHolder(node):
    target_name = anne_dictionary("target",node["_target"])
    return {
        "main" : f"检查{target_name}（干员）是否已秉烛",
        "true" : "若该干员已秉烛",
        "false" : "若该干员未秉烛，或单位不是干员/非招募所得"
    }