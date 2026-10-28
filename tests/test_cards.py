"""The card table and the cost rule (REQ1/CARD-1, REQ1/CARD-2, REQ1/SET-4)."""
import unittest

from splendorous.cards import ABILITIES, BAG, CHAPTER_KINDS, CHAPTERS, SLACK, TABLE, base_cost, discounted_cost

from support import cards


class TestCostRule(unittest.TestCase):
    def test_card_1_cost_follows_value_and_chapter(self):
        """REQ1/CARD-1: 0 free; 1 = one primary; 2 = 1+1; 3 = 2+1; 4 = 2+2; 5 = 2+2+Slack."""
        self.assertEqual(CHAPTER_KINDS["T"], ("test", "run"))
        self.assertEqual(base_cost(0, "T"), {})
        self.assertEqual(base_cost(1, "T"), {"test": 1})
        self.assertEqual(base_cost(2, "T"), {"test": 1, "run": 1})
        self.assertEqual(base_cost(3, "T"), {"test": 2, "run": 1})
        self.assertEqual(base_cost(4, "T"), {"test": 2, "run": 2})
        self.assertEqual(base_cost(5, "T"), {"test": 2, "run": 2, SLACK: 1})
        self.assertEqual(base_cost(3, "H"), {"ask": 2, "review": 1})

    def test_card_2_each_compiled_chapter_discounts_its_primary_kind(self):
        """REQ1/CARD-2: one less primary per compiled chapter, never below zero, Slack untouched."""
        t3 = cards()["T3"]  # value 5, chapter T: test 2, run 2, slack 1
        self.assertEqual(discounted_cost(t3, []), {"test": 2, "run": 2, SLACK: 1})
        self.assertEqual(discounted_cost(t3, ["T"]), {"test": 1, "run": 2, SLACK: 1})
        self.assertEqual(discounted_cost(t3, ["T", "F"]), {"run": 2, SLACK: 1})
        self.assertEqual(discounted_cost(t3, ["T", "F", "O"]), {"run": 1, SLACK: 1})  # O's primary is run
        self.assertEqual(discounted_cost(t3, ["H"]), {"test": 2, "run": 2, SLACK: 1})  # ask is not in the cost
        p3 = cards()["P3"]  # value 1: ask 1
        self.assertEqual(discounted_cost(p3, ["P", "R"]), {})

    def test_table_values_and_abilities_are_in_range(self):
        """REQ1/CARD-1, REQ1/CARD-3: every value is 0–5 and every ability is a known one."""
        for cid, (value, ability) in TABLE.items():
            self.assertIn(value, range(6), cid)
            self.assertIn(ability, ABILITIES, cid)
        self.assertEqual(set(CHAPTER_KINDS), set(CHAPTERS))

    def test_set_4_bag_holds_25_tokens(self):
        """REQ1/SET-4: four of each evidence kind, two Slack, three Confidence."""
        self.assertEqual(sum(BAG.values()), 25)
        self.assertEqual(BAG, {"run": 4, "test": 4, "ask": 4, "note": 4, "review": 4, "slack": 2, "confidence": 3})


if __name__ == "__main__":
    unittest.main()
