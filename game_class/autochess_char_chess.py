#----------------------------------------
# 卫戍协议 · 干员棋子
#----------------------------------------
from bena import ask_bena_character
from dictionary import anne_dictionary
from game_class.autochess_garrison import AutochessGarrison

DEX = ["[Ⅰ]","[Ⅱ]","[Ⅲ]","[Ⅳ]","[Ⅴ]","[Ⅵ]"]

BOND_REFERENCE = {}

class AutochessCharChess:
    def __init__(self, chess_id, char_data, chess_data, garrison_datas, golden_chess_data = None, golden_garrison_datas = None):
        self.chess_id = chess_id
        self.char_data = char_data
        self.chess_data = chess_data
        self.golden_garrison_datas = golden_garrison_datas
        self.garrisons = [AutochessGarrison(_id,_datas) for _id,_datas in garrison_datas.items()]
        self.char_id = char_data["charId"]
        self.backup_char_id = char_data["backupCharId"]
        self.chess_level = char_data["chessLevel"]
        self.bonds = chess_data["bondIds"] # 金的应该和普通的一样，这里不校验了
        self.display_name = ""
        self.has_golden = golden_chess_data != None
        self.golden_chess_data = golden_chess_data
        self.garrison_datas = garrison_datas
        self.hidden = False
        # 加入索引
        for bond_id in self.bonds:
            if bond_id not in BOND_REFERENCE:
                BOND_REFERENCE[bond_id] = []
            BOND_REFERENCE[bond_id].append(self)

    # 获取显示名
    def get_display_name(self):
        if self.display_name == "":
            self.display_name = DEX[self.chess_level - 1]
            if self.char_id == None:
                self.display_name += f"自选（{self.chess_id[13:-2]}）"
            else:
                self.display_name += ask_bena_character(self.char_id)
        return self.display_name

    # 获取原文
    def get_raw_data(self):
        return [self.char_data,self.chess_data,self.garrison_datas,self.golden_chess_data,self.golden_garrison_datas]
    
    # 获取翻译
    def translate(self):
        result = {
            "main" : self.get_display_name() + "（" + self.chess_id + "）",
            "description" : "【无盟约】",
            "children" : []
        }
        bonds = [anne_dictionary("bond_id",bond_id) for bond_id in self.bonds]
        if len(bonds) > 0:
            result["description"] = " ".join(bonds)
        if self.char_id != None and self.backup_char_id != self.char_id and self.backup_char_id != None:
            backup_char = ask_bena_character(self.backup_char_id)
            result["description"] += " | " + "原型干员："+backup_char

        # 普通版
        normal_label = {"main" : "普通状态：","role" : "condition","children" : []}
        normal_label["children"].append({"main" : self.chess_data["desc"]})
        garrison_label = {"main" : "特质：","children" : []}
        for garrison in self.garrisons:
            garrison_label["children"].append(garrison.translate())
        normal_label["children"].append(garrison_label)
        result["children"].append(normal_label)

        # 精锐版
        if self.has_golden:
            golden_label = {"main" : "精锐状态：","role" : "condition","children" : []}
            golden_label["children"].append({"main" : self.golden_chess_data["desc"]})
            golden_garrison_label = {"main" : "特质：","children" : []}
            for garrison_id, garrison_data in self.golden_garrison_datas.items():
                golden_garrison_label["children"].append(AutochessGarrison(garrison_id,garrison_data).translate())
            golden_label["children"].append(golden_garrison_label)
            result["children"].append(golden_label)
        
        # 相关干员
        related_chars = []
        for bond_id in self.bonds:
            if bond_id in BOND_REFERENCE and len(BOND_REFERENCE[bond_id]) > 0:
                bond_info = {
                    "main" : anne_dictionary("bond_id",bond_id) + "："
                }
                for char in BOND_REFERENCE[bond_id]:
                    bond_info["main"] += "<autochess_3|" + char.chess_id + "> "
                bond_info["main"] = bond_info["main"].strip()
                related_chars.append(bond_info)
        if len(related_chars) > 0:
            result["children"].append({
                "main" : "相关干员：",
                "role" : "condition",
                "children" : related_chars
            })
        return result
