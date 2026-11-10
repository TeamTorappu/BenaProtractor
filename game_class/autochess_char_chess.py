#----------------------------------------
# 卫戍协议 · 干员棋子
#----------------------------------------
from bena import ask_bena_character
from dictionary import anne_dictionary
from game_class.autochess_garrison import AutochessGarrison

DEX = ["[Ⅰ]","[Ⅱ]","[Ⅲ]","[Ⅳ]","[Ⅴ]","[Ⅵ]"]

class AutochessCharChess:
    def __init__(self, chess_id, chess_data, char_data,garrison_datas):
        self.chess_id = chess_id
        self.chess_data = chess_data
        self.char_data = char_data
        self.garrison_datas = garrison_datas
        self.garrisons = [AutochessGarrison(_id,_datas) for _id,_datas in garrison_datas.items()]
        self.char_id = char_data["charId"]
        self.backup_char_id = char_data["backupCharId"]
        self.chess_level = char_data["chessLevel"]
        self.display_name = ""
        self.identifier = chess_data["identifier"]
        self.is_golden = chess_data["isGolden"]
        self.hidden = False

    # 获取显示名
    def get_display_name(self):
        if self.display_name == "":
            self.display_name = DEX[self.chess_level - 1]
            if self.char_id == None:
                self.display_name += f"自选（{self.chess_id[13:-2]}）"
            else:
                self.display_name += ask_bena_character(self.char_id)
            if self.is_golden:
                self.display_name += " · 精锐"
        return self.display_name

    # 获取原文
    def get_raw_data(self):
        return [self.chess_data,self.char_data]
    
    # 获取翻译
    def translate(self):
        result = {
            "main" : self.get_display_name(),
            "description" : "【无盟约】",
            "children" : []
        }
        bonds = [anne_dictionary("bond_id",bond_id) for bond_id in self.chess_data["bondIds"]]
        if len(bonds) > 0:
            result["description"] = " ".join(bonds)
        result["children"].append(self.chess_data["desc"])
        if self.char_id != None:
            base_char = ask_bena_character(self.char_id)
            result["children"].append({"main" : "盟约干员："+base_char})
            if self.backup_char_id != base_char and self.backup_char_id != None:
                backup_char = ask_bena_character(self.backup_char_id)
                result["children"].append({"main" : "原型干员："+backup_char})

        # 特质
        garrison_label = {"main" : "特质：","children" : []}
        for garrison in self.garrisons:
            garrison_label["children"].append(garrison.translate())
        result["children"].append(garrison_label)
        return result
