#----------------------------------------
# Buff模板
#----------------------------------------
import json
from gameclasses.event_to_action import EventToAction

class BuffTemplate:
    def __init__(self, buff_key, buff_data):
        self.buff_key = buff_key
        self.display_name = buff_key
        self.buff_data = buff_data
        self.template_key = buff_data["templateKey"] if "templateKey" in buff_data else buff_key # 虽然不知道有啥区别，总之留着吧
        self.effect_key = buff_data["effectKey"]
        self.hidden = False
        self.on_event_priority = buff_data["onEventPriority"]
        self.events = []
        for event_name in buff_data["eventToActions"].keys():
            self.events.append(EventToAction(event_name,buff_data["eventToActions"][event_name]))
    
    # 获取显示名
    def get_display_name(self):
        if self.display_name == "":
            return self.buff_key
        return self.display_name

    # 获取原文
    def get_raw_data(self):
        return json.dumps(self.buff_data,indent=4,ensure_ascii=False)