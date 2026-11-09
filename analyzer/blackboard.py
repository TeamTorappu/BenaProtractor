#----------------------------------------
# 解析黑板
#----------------------------------------

# 解析黑板，将黑板转化为更易于处理的格式
# 返回数据正常一对一的结构体
def analyze_blackboard(raw_bb_data):
    if raw_bb_data == None:
        return {}
    bb_data = {}
    for bb in raw_bb_data:
        if "key" in bb:
            bb_key = bb["key"]
            if "valueStr" in bb and bb["valueStr"] != None and bb["value"] != "":
                bb_data[bb_key] = bb["valueStr"]
            elif "value" in bb:
                bb_data[bb_key] = bb["value"]
    return bb_data