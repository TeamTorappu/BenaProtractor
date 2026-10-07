#----------------------------------------
# 地图符文
#----------------------------------------

# 地块黑板乘算（选择器无效果）
def map_tile_blackb_mul(selector,blackboard):
    return {}

# 地块黑板加算（选择器无效果）
def map_tile_blackb_add(selector,blackboard):
    return {}

# 地块黑板重设（选择器无效果）
def map_tile_blackb_assign(selector,blackboard):
    if blackboard.get("tile","") != "":
        target_tiles = blackboard["tile"].split("|") #需翻译
        result = {
            "main" : "覆写关卡中所有 "+"、".join(target_tiles)+" 地块的黑板值：",
            "children" : []
        }
        for key, value in blackboard.items():
            if key != "tile":
                result["children"].append({"main" : str(key) + " : " + str(value)})
        return result
    return {"main" : "无效符文"}