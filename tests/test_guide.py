"""The cards come from the vendored guide (REQ1/GUIDE-1, REQ1/GUIDE-2, REQ1/GUIDE-3)."""
import shutil
import tempfile
import unittest
from pathlib import Path

from splendorous.cards import TABLE, GuideMismatch, build_cards
from splendorous.cli import card_line
from splendorous.guide import Guide, GuideError, Principle, default_root, load_guide, parse_asks, parse_index

from support import cards

INDEX_SAMPLE = """
- [**SE1/P1**](guide/01-purpose.md#p1) Engineers make reliable things
- [**SE1/T3**](guide/06-testing.md#t3) A test that cannot fail proves nothing
not an index line
"""

CHAPTER_SAMPLE = '''# 6. Testing

### <a id="t3"></a>T3. A test that cannot fail proves nothing

*Since v1.1 (2026-10-20).*

Body text.

> **Ask:** "Have I seen this test fail — and this
> instrument fire?"

### <a id="t4"></a>T4. A loop you do not trust is worse than none

No ask here.

### <a id="w8"></a>W8. Don't fall down the waterfall

> **Ask:** "What will I know when this spike stops?" — and — "What has the client objected to so far?"
'''


class TestGuideParsing(unittest.TestCase):
    def test_guide_1_index_lines_are_parsed_in_order(self):
        """REQ1/GUIDE-1: the index gives id, path, anchor, and title, and skips other lines."""
        entries = parse_index(INDEX_SAMPLE)
        self.assertEqual([e["id"] for e in entries], ["P1", "T3"])
        self.assertEqual(entries[1], {"id": "T3", "path": "guide/06-testing.md", "anchor": "t3",
                                      "title": "A test that cannot fail proves nothing"})

    def test_guide_2_ask_lines_wrap_and_may_be_absent(self):
        """REQ1/GUIDE-2: a wrapped Ask is one line; a principle without one gives None."""
        asks = parse_asks(CHAPTER_SAMPLE)
        self.assertEqual(asks["T3"], "Have I seen this test fail — and this instrument fire?")
        self.assertIsNone(asks["T4"])
        self.assertEqual(asks["W8"], 'What will I know when this spike stops?" — and — "What has the client objected to so far?')

    def test_guide_1_vendored_guide_has_one_card_per_principle(self):
        """REQ1/GUIDE-1: 100 principles at v1.3.1, each with a card, and no card without one."""
        guide = load_guide(default_root())
        ids = [p.id for p in guide.principles]
        self.assertEqual(len(ids), 100)
        self.assertEqual(len(set(ids)), 100)
        self.assertEqual(set(ids), set(TABLE))
        self.assertEqual(set(cards()), set(ids))

    def test_guide_1_mismatch_refuses_and_names_the_ids(self):
        """REQ1/GUIDE-1: a principle the table lacks, or a table entry the guide lacks, is refused by name."""
        real = load_guide(default_root())
        extra = Principle("Z9", "Z", "A principle the table does not know", None, "guide/x.md", "z9")
        with self.assertRaises(GuideMismatch) as caught:
            build_cards(Guide(real.principles + [extra], real.chapter_names))
        self.assertIn("Z9", str(caught.exception))
        with self.assertRaises(GuideMismatch) as caught:
            build_cards(Guide([p for p in real.principles if p.id != "T3"], real.chapter_names))
        self.assertIn("T3", str(caught.exception))

    def test_guide_1_missing_guide_is_refused_by_path(self):
        """REQ1/GUIDE-1 (input absent): no guide at the path is an error naming the path."""
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(GuideError) as caught:
                load_guide(Path(tmp) / "nowhere")
            self.assertIn("nowhere", str(caught.exception))

    def test_guide_2_card_shows_citation_title_and_ask(self):
        """REQ1/GUIDE-2: the card line carries SE1/ID, the title, and the Ask where there is one."""
        t3 = cards()["T3"]
        line = card_line(t3)
        self.assertIn("SE1/T3", line)
        self.assertIn(t3.title, line)
        self.assertIn("Ask:", line)
        self.assertIn(t3.ask, line)
        no_ask = next(c for c in cards().values() if c.ask is None)
        self.assertNotIn("Ask:", card_line(no_ask))
        self.assertIn(no_ask.title, card_line(no_ask))

    def test_guide_3_editing_the_vendored_text_changes_the_card(self):
        """REQ1/GUIDE-3: a changed title and Ask in a copy of the guide reach the card with no code change."""
        root = default_root()
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "guide-copy"
            copy.mkdir()
            shutil.copytree(root / "guide", copy / "guide")
            readme = (root / "README.md").read_text(encoding="utf8")
            (copy / "README.md").write_text(readme.replace("A test that cannot fail proves nothing",
                                                           "A test never seen red proves nothing"), encoding="utf8")
            chapter = copy / "guide" / "06-testing.md"
            chapter.write_text(chapter.read_text(encoding="utf8").replace(
                '> **Ask:** "Have I seen this test fail', '> **Ask:** "Did I watch it fail'), encoding="utf8")
            edited = build_cards(load_guide(copy))
        self.assertEqual(edited["T3"].title, "A test never seen red proves nothing")
        self.assertTrue(edited["T3"].ask.startswith("Did I watch it fail"))
        self.assertEqual(cards()["T3"].title, "A test that cannot fail proves nothing")


if __name__ == "__main__":
    unittest.main()
