#----------------------------------------
# 卫戍协议 · 装置棋子
#----------------------------------------
from dictionary import anne_dictionary

DEX = ["[Ⅰ]","[Ⅱ]","[Ⅲ]","[Ⅳ]","[Ⅴ]","[Ⅵ]"]

class AutochessTrapChess:
    def __init__(self, chess_id, trap_data, trap_shop_data, golden_trap_data = None, golden_trap_shop_data = None):
        self.chess_id = chess_id
        self.trap_data = trap_data
        self.trap_shop_data = trap_shop_data
        self.golden_trap_data = golden_trap_data
        self.golden_trap_shop_data = golden_trap_shop_data
        self.display_name = ""
        self.has_golden = golden_trap_data != None
        self.hidden = False

    # 获取显示名
    def get_display_name(self):
        if self.display_name == "":
            self.display_name = DEX[self.chess_level - 1] + self.chess_id
        return self.display_name

    # 获取原文
    def get_raw_data(self):
        return [self.trap_data,self.trap_shop_data,self.golden_trap_data,self.golden_trap_shop_data]

    # 获取翻译
    def translate(self):
        result = {
            "main" : self.get_display_name() + "（" + self.chess_id + "）",
            "children" : []
        }
        return result
