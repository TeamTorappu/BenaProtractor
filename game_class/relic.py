#----------------------------------------
# 藏品符文
#----------------------------------------
import json
from analyzer import analyze_blackboard

class Relic:
    def __init__(self, relic_data, item_type):
        self.relic_data = relic_data
        self.key = relic_data["key"]
        self.type = item_type # 父级的类型，用于传参
        self.blackboard = analyze_blackboard(relic_data["blackboard"])
        self.translation = None

    # 获取原文
    def get_raw_data(self):
        return json.dump(self.relic_data,indent=4,ensure_ascii=False)