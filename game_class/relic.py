#----------------------------------------
# 藏品符文
#----------------------------------------
from analyzer.blackboard import analyze_blackboard

class Relic:
    def __init__(self, relic_data, item_type):
        self.relic_data = relic_data
        self.key = relic_data["key"]
        self.type = item_type # 父级的类型，用于传参
        self.blackboard = analyze_blackboard(relic_data["blackboard"])
        self.display_name == ""
        self.hidden = False

    # 获取显示名
    def get_display_name(self):
        if self.display_name == "":
            return self.key
        return self.display_name

    # 获取原文
    def get_raw_data(self):
        return self.relic_data