"""Reference boundaries and conditional output must preserve source meaning."""
import copy
import unittest
from unittest.mock import patch

import anne
import bena
from bena.catalog import Catalog
from game_class import Buff, Node
from document_model import document_rows, reference_parts, default_folds


class ReferenceSafetyTests(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog(['buff'])
        for category in ('buff', 'buff_template', 'global_buff', 'rogue_item'):
            self.catalog.add(category, 'same_id', Buff('same_id', {}))
        self.catalog.add('buff_template', 'damage_resistance', Buff('damage_resistance', {}))
        self.catalog.add('buff', 'only_buff', Buff('only_buff', {}))
        relic = Buff('rogue_6_relic_fight_7', {})
        relic.display_name = '“庇护”'
        self.catalog.add('rogue_item', relic.buff_key, relic)
        self.catalog.install()

    def assertLiteral(self, text):
        parts = reference_parts(text, self.catalog)
        self.assertEqual(''.join(label for label, _ in parts), text)
        self.assertFalse(any(target for _, target in parts))

    def test_comparisons_markup_and_unknown_references_are_literal(self):
        for text in ('1 < 2 and 3 > 0', '<color=#ff0000>重点</color>',
                     '<b>重点</b>', '<@ba.vup>加成</>', '<color=same_id>文字</color>',
                     '说明 <enemy_damage>', '<missing_id>', '<年代之刺>'):
            with self.subTest(text=text):
                self.assertLiteral(text)

    def test_typed_references_use_the_raw_key_and_declared_category(self):
        with patch.object(self.catalog, 'resolve', side_effect=AssertionError('No name lookup')):
            for category in self.catalog.groups:
                with self.subTest(category=category):
                    parts = reference_parts('<' + category + '|same_id>', self.catalog)
                    self.assertEqual([t for _, t in parts if t], [category + '.same_id'])

    def test_invalid_markers_are_literal(self):
        for text in ('<bogus|same_id>', '<|same_id>', '<buff|>', '<buff||same_id>'):
            with self.subTest(text=text):
                self.assertLiteral(text)

    def test_missing_targets_never_fall_back_to_other_categories_or_names(self):
        for text in ('<global_buff|only_buff>', '<rogue_item|buff.same_id>',
                     '<rogue_item|“庇护”>', '<buff_template|庇护>'):
            with self.subTest(text=text):
                self.assertFalse(any(t for _, t in reference_parts(text, self.catalog)))

    def test_relic_raw_key_links_to_relic(self):
        parts = reference_parts('<rogue_item|rogue_6_relic_fight_7>', self.catalog)
        self.assertEqual(parts, [('“庇护”', 'rogue_item.rogue_6_relic_fight_7')])

    def test_plain_text_and_untyped_markers_never_link(self):
        for text in ('庇护', '“庇护”', '收藏品【“庇护”】', '获得庇护效果',
                     '<庇护>', '同_id', '<same_id>', 'same_id / only_buff / [same_id]',
                     'buff.same_id / <damage_resistance>'):
            with self.subTest(text=text):
                self.assertLiteral(text)

    def test_prefab_only_buff_name_translation_does_not_create_a_link(self):
        self.assertEqual(reference_parts('<buff|enemy_damage>', self.catalog),
                         [('敌方_伤害（enemy_damage）', None)])
        with patch('document_model.bena.translate_buff_name', return_value='庇护'):
            self.assertEqual(reference_parts('<buff|prefab_only_id>', self.catalog),
                             [('庇护（prefab_only_id）', None)])

    def test_prts_links_also_require_explicit_markers(self):
        self.assertLiteral('prts.浪里玄条')
        self.assertEqual(reference_parts('<prts|浪里玄条>', self.catalog),
                         [('浪里玄条', 'prts.浪里玄条')])


class PresentationRoleTests(unittest.TestCase):
    def test_children_change_folding_but_not_action_color(self):
        document = {'main': '事件', 'children': [
            {'main': '创建Buff', 'children': [{'main': '黑板数据'}], 'style_closed': True},
            {'main': '创建Buff'}]}
        for collapsed in (frozenset(), default_folds(document)):
            rows = document_rows(document, collapsed)
            actions = [r for r in rows if r.text == '创建Buff']
            self.assertEqual([r.role for r in actions], ['body', 'body'])
            self.assertEqual([r.foldable for r in actions], [True, False])

    def test_event_and_condition_roles_do_not_require_children(self):
        rows = document_rows({'main': '标题', 'children': [
            {'main': '事件', 'role': 'section'},
            {'main': '分支', 'role': 'condition', 'children': [{'main': '动作'}]},
            {'main': '说明所属动作', 'description': '说明'}]})
        self.assertEqual({row.text: row.role for row in rows}, {
            '标题': 'heading', '事件': 'section', '分支': 'condition',
            '动作': 'body', '说明所属动作': 'body', '说明': 'description'})


class ConditionalOutputTests(unittest.TestCase):
    def setUp(self):
        self.translator = anne.AnneNode()
        self.check = {'$type': 'CheckAbnormalCombo', '_targetType': 'TARGET',
                      '_abnormalCombo': 'SLEEPING', '_isUnset': False}
        self.success = {'$type': 'Dummy', '_dummy': '成功效果'}
        self.failure = {'$type': 'Dummy', '_dummy': '失败效果'}

    def rows(self, nodes):
        raw = copy.deepcopy(nodes)
        result = self.translator.translate_all([Node(n) for n in raw], {})
        self.assertEqual(raw, nodes)
        return document_rows(result)

    def test_sequential_check_keeps_original_condition_text(self):
        rows = self.rows([self.check, self.success])
        guards = [r for r in rows if r.text.startswith('若')]
        self.assertEqual([r.text for r in guards], ['若持有沉睡异常组合...'])
        self.assertEqual(guards[0].role, 'condition')

    def test_reversed_checks_have_only_the_reversed_guard(self):
        for nodes in ([dict(self.check, _isUnset=True), self.success],
                      [self.check, {'$type': 'IfNot'}, self.success]):
            with self.subTest(nodes=nodes):
                guards = [r.text for r in self.rows(nodes) if r.text.startswith('若')]
                self.assertEqual(guards, ['若不持有沉睡异常组合或免疫该异常组合...'])

    def test_last_check_has_no_continuation(self):
        self.assertFalse(any(r.text.startswith('若') for r in self.rows([self.check])))

    def test_explicit_branches_keep_their_own_children(self):
        for success, failure in (([self.success], [self.failure]), ([self.success], []),
                                 ([], [self.failure])):
            with self.subTest(success=success, failure=failure):
                rows = self.rows([{'$type': 'IfElse', '_conditionNode': self.check,
                                   '_succeedNodes': success, '_failNodes': failure}])
                guards = [r for r in rows if r.text.startswith('若')]
                self.assertEqual(len(guards), bool(success) + bool(failure))
                self.assertTrue(all(row.role == 'condition' for row in guards))
                for effect in (r for r in rows if r.text in ('成功效果', '失败效果')):
                    parent = next(r for r in guards if effect.path[:-1] == r.path)
                    self.assertEqual(effect.depth, parent.depth + 1)
                    self.assertEqual(parent.text.startswith('若不持有'), effect.text == '失败效果')


if __name__ == '__main__':
    unittest.main()
