import unittest
from unittest.mock import patch

from anne.autochess_char_chess import AutochessCharChess


class AutochessCharChessTests(unittest.TestCase):
    def make_chess(self, level, char_id=None, tmpl_id=None, is_golden=False):
        chess_id = f"chess_char_{level}_diy1_a"
        chess_data = {
            "identifier": 1,
            "isGolden": is_golden,
            "bondIds": [],
            "desc": "测试棋子",
        }
        char_data = {
            "charId": char_id,
            "tmplId": tmpl_id,
            "chessLevel": level,
        }
        return AutochessCharChess(chess_id, chess_data, char_data, {})

    def test_missing_character_ids_have_a_display_fallback(self):
        chess = self.make_chess(6)
        with patch("anne.autochess_char_chess.ask_bena_character", return_value=None):
            self.assertEqual(chess.get_display_name(), "[Ⅵ]自定义棋子（chess_char_6_diy1_a）")
            translation = chess.translate()
        self.assertIn({"main": "盟约干员：未指定"}, translation["children"])
        self.assertIn({"main": "原型干员：未指定"}, translation["children"])

    def test_chess_levels_map_to_one_based_rank_symbols(self):
        chess = self.make_chess(1, char_id="char_1")
        with patch("anne.autochess_char_chess.ask_bena_character", return_value="测试干员"):
            self.assertEqual(chess.get_display_name(), "[Ⅰ]测试干员")


if __name__ == "__main__":
    unittest.main()
