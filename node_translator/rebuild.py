#----------------------------------------
# 再部署类Node
#----------------------------------------
from .analyzer import analyze_buff
from translator import anne_dictionary

# 在特定范围内再部署此干员
def node_RebuildCharacterOnTileInRange(node):
    # 未解析参数：_owner
    target_name = anne_dictionary("target",node["_target"])
    range_id = node["_rangeId"]
    direction = "相同方向"
    # 修改朝向
    if node["_rotateBuildDirection"]:
        if node["_randomDirection"]:
            direction = "随机方向"
        else:
            direction = "+ [value] 的方向"
    result = {
        "main" : f"撤退（不返还费用）并在{range_id}范围内随机位置上以{direction}再部署{target_name}"
    }
    # 再部署后的Buff
    if node["_createBuff"] and node["_buff"] != None:
        result["children"] = []
        buff = analyze_buff(node['_buff'])
        buff["main"] = "...并在再部署后为新单位创建Buff：" + buff["main"]
        result["children"].append(buff)
        result["children"].append({"main" : "（该Buff会继承本Buff的黑板数据，如记录在黑板上的生命值、技能状态、技力等）"})
    return result


