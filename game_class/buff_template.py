#----------------------------------------
# Buff模板
#----------------------------------------
from dictionary import anne_dictionary
from game_class.event_to_action import EventToAction

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
        return self.buff_data

    # 翻译
    def translate(self,blackboard : dict = {}):
        print("[安妮]尝试翻译Buff模板 "+self.buff_key)
        translation = {
            "main" : self.buff_key,
            "children" : []
        }
        if self.display_name != self.buff_key:
            translation["main"] = f"{self.display_name}（{self.buff_key}）"
        if self.on_event_priority != "DEFAULT":
            priority = anne_dictionary("event_priority",self.on_event_priority)
            translation["children"].append("事件优先级："+priority)
        if self.effect_key != "":
            translation["children"].append("特效："+self.effect_key)
        # 逐个事件进行翻译
        for event in self.events:
            translation["children"].append(event.translate(blackboard))
        return translation