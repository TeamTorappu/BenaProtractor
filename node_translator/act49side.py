#----------------------------------------
# 辞岁行相关Node
#----------------------------------------
from translator import anne_dictionary
from .analyzer import to_percent

# 修改颜色
def node_Act49SideSetEntityAnimatorColor(node):
    target_name = anne_dictionary("target",node["_targetType"])
    color = (node["color"]["r"] , node["color"]["g"] , node["color"]["b"])
    alpha = to_percent(node["color"]["a"])
    color_name = ""
    if node["color"]["a"] == 0:
        color_name = "透明（0%）"
    elif color[0] == 1 and color[1] == 1 and color[2] == 1:
        color_name = f"白色（{alpha}）"
    elif color[0] == 0 and color[1] == 0 and color[2] == 0:
        color_name = f"黑色（{alpha}）"
    elif color[0] == 1 and color[1] == 0 and color[2] == 0:
        color_name = f"红色（{alpha}）"
    elif color[0] == 0 and color[1] == 1 and color[2] == 0:
        color_name = f"绿色（{alpha}）"
    elif color[0] == 0 and color[1] == 0 and color[2] == 1:
        color_name = f"蓝色（{alpha}）"
    elif color[0] == 1 and color[1] == 1 and color[2] == 0:
        color_name = f"黄色（{alpha}）"
    elif color[0] == 0 and color[1] == 1 and color[2] == 1:
        color_name = f"青色（{alpha}）"
    elif color[0] == 1 and color[1] == 0 and color[2] == 1:
        color_name = f"品红色（{alpha}）"
    else:
        color_hex = '#{:02X}{:02X}{:02X}'.format(color)
        color_name = f"#{color_hex}（{alpha}）"
    return {
        "main" : f"将{target_name}的渲染颜色改为 {color_name}",
        "description" : f"r{node['color']['r']}  g{node['color']['g']}  b{node['color']['b']}  a{node['color']['a']})"
    }

# 浪里玄条字形态寻路
def node_Act49SideEnemyTjglyTryFindNextTile(node):
    target_name = anne_dictionary("target",node["_targetType"])
    return {
        "main" : f"若{target_name}处于字形态下，尝试寻找并移动到下一个地块上",
        "description" : "具体逻辑请见PRTS的 浪里玄条 页面",
        "link" : "prts.浪里玄条"
    }

# 浪里玄条绑定字
def node_Act49SideEnemyTjglyLockSelfWithTile(node):
    target_name = anne_dictionary("target",node["_targetType"])
    return {
        "main" : f"尝试将{target_name}与当前所在字格地块的\"鱼\"字相绑定",
        "description" : "具体逻辑请见PRTS的 浪里玄条 页面",
        "link" : "prts.浪里玄条"
    }

# 检查所在字格地块是否可部署
def node_Act49SideCheckWordTileBuildable(node):
    target_name = anne_dictionary("target",node["_targetType"])
    return {
        "main" : f"检查{target_name}所在的字格地块是否可部署",
        "true" : "若该地块为可部署的字格地块",
        "false" : "若该地块不为字格或是不可部署"
    }

# 检查所在字格地块是否为某字
def node_Act49SideCheckCharacterTileType(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_checkAnyTile"]:
        return {
            "main" : f"检查{target_name}所在的地块",
            "true" : "若该地块是字格地块",
            "false" : "若该地块不是字格地块"
        }
    if node["_tileType"] == "None":
        return {
            "main" : f"检查{target_name}所在的地块",
            "true" : "若该地块不是字格地块",
            "false" : "若该地块是字格地块"
        }
    tile = anne_dictionary("act49side_char",node["_tileType"])
    return {
        "main" : f"检查{target_name}所在的字格地块上的字",
        "true" : f"若该地块上的字为\"{tile}\"字",
        "false" : f"若该地块不为字格或是字不为\"{tile}\"字"
    }

# 将所在字格地块改写为某字
def node_Act49SideWriteCharacter(node):
    target_name = anne_dictionary("target",node["_targetType"])
    if node["_tileType"] == "None":
        return {
            "main" : f"尝试将{target_name}所在字格地块改写为\"不是字格\"",
            "true" : "若改写成功",
            "false" : "若该地块已不为字格或是改写失败"
        }
    tile = anne_dictionary("act49side_char",node["_tileType"])
    return {
        "main" : f"尝试将{target_name}所在字格地块上的字改写为\"{tile}\"字",
        "true" : "若改写成功",
        "false" : "若该地块不为字格或是改写失败"
    }