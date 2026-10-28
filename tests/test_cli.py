"""The terminal interface (REQ1/CLI-1..REQ1/CLI-5, REQ1/GUIDE-2, REQ1/TURN-8), driven with a scripted reader and a
buffer for a writer, so no test touches the real terminal (SE1/T7)."""
import argparse
import io
import unittest

from splendorous.cli import build_parser, card_line, describe, main, parse_chapters, play, render
from splendorous.engine import Demonstrate, Refresh, apply, legal_moves

from support import fresh, give, put_in_hand, rng


class Script:
    """Lines a person would type, then end of input."""

    def __init__(self, *lines):
        self.lines = list(lines)

    def __call__(self):
        return self.lines.pop(0) if self.lines else None


class TestRender(unittest.TestCase):
    def test_cli_1_render_shows_board_tokens_lanes_and_hand(self):
        """REQ1/CLI-1: the board grid, each player's tokens, the three lanes, the viewer's hand."""
        g = fresh()
        give(g, 0, "run")
        text = render(g, 0)
        self.assertIn("Round 1", text)
        self.assertEqual(sum(1 for line in text.splitlines() if line.startswith(" ") and line[1].isdigit()), 5)
        self.assertIn("P0 tokens: R1", text)
        self.assertIn("P1 tokens: none", text)
        for lane in ("Lane 1: P0 T", "Lane 2: P0 D", "Lane 3: P0 R"):
            self.assertIn(lane, text)
        self.assertIn("P0 hand:", text)
        for cid in g.players[0].hand:
            self.assertIn(cid, text.split("P0 hand:")[1])

    def test_cli_1_describe_names_every_kind_of_move(self):
        """REQ1/CLI-1: each move kind has a description a person can choose by."""
        g = fresh()
        kinds = {type(m).__name__ for m in legal_moves(g)}
        self.assertTrue({"Gather", "TakeConfidence", "Refresh"} <= kinds)
        for move in legal_moves(g):
            self.assertTrue(describe(g, move))
        self.assertIn("refresh", describe(g, Refresh()))


class TestPlay(unittest.TestCase):
    def test_cli_1_a_person_chooses_a_listed_move_by_number(self):
        """REQ1/CLI-1: the first listed move is chosen with '1'; then end of input resigns (REQ1/CLI-4)."""
        g = fresh()
        first = legal_moves(g)[0]
        out = io.StringIO()
        final = play(g, [None, None], Script("1"), out.write, rng())
        self.assertIn("  1. " + describe(g, first), out.getvalue())
        self.assertEqual(final.winner, 0)
        self.assertIn("resigned", final.reason)
        self.assertEqual(final.current, 1)

    def test_cli_4_wrong_input_is_refused_and_the_list_shown_again(self):
        """REQ1/CLI-4: a word, a zero, and a number past the end are refused; the next good line works."""
        g = fresh()
        n = len(legal_moves(g))
        out = io.StringIO()
        play(g, [None, None], Script("yes", "0", str(n + 1), "2"), out.write, rng())
        text = out.getvalue()
        for bad in ("'yes'", "'0'", f"'{n + 1}'"):
            self.assertIn(f"{bad} is not a number from 1 to {n}", text)
        self.assertEqual(text.count("P0, choose"), 4)

    def test_guide_2_a_demonstrated_card_prints_its_principle(self):
        """REQ1/GUIDE-2: a face-up play prints SE1/ID, the title, and the Ask."""
        g = fresh()
        put_in_hand(g, 0, "T4")
        give(g, 0, "test")
        number = legal_moves(g).index(Demonstrate("T4")) + 1
        out = io.StringIO()
        play(g, [None, None], Script(str(number)), out.write, rng())
        self.assertIn(card_line(g.cards["T4"]), out.getvalue())
        self.assertIn("SE1/T4", out.getvalue())

    def test_turn_8_the_opponent_sees_a_face_down_card_as_hidden(self):
        """REQ1/TURN-8."""
        g = fresh()
        put_in_hand(g, 0, "T3")
        give(g, 0, "confidence")
        from splendorous.engine import Assert
        g2 = apply(g, Assert("T3"))
        self.assertIn("T3v2", render(g2, 0))
        self.assertIn("??=2", render(g2, 1))

    def test_cli_2_bots_play_each_other_to_the_end(self):
        """REQ1/CLI-2: two bot seats need no input and reach a winner."""
        from splendorous.bots import greedy_bot, random_bot
        out = io.StringIO()
        final = play(fresh(3), [random_bot, greedy_bot], Script(), out.write, rng(3))
        self.assertIn(final.winner, (0, 1))
        self.assertIn(f"P{final.winner} wins", out.getvalue())


class TestArguments(unittest.TestCase):
    def test_cli_2_defaults_are_a_person_against_greedy(self):
        """REQ1/CLI-2."""
        args = build_parser().parse_args([])
        self.assertEqual((args.p0, args.p1), ("human", "greedy"))
        args = build_parser().parse_args(["--p0", "random", "--p1", "human"])
        self.assertEqual((args.p0, args.p1), ("random", "human"))

    def test_cli_3_chapters_are_two_groups_of_three_distinct_letters(self):
        """REQ1/CLI-3: `TDR,HOA` parses; a repeat, an unknown letter, or five letters is refused."""
        self.assertEqual(parse_chapters("tdr,HOA"), (("T", "D", "R"), ("H", "O", "A")))
        for bad in ("TDR,TOA", "TDR,HOZ", "TD,HOA", "TDRHOA"):
            with self.assertRaises(argparse.ArgumentTypeError):
                parse_chapters(bad)

    def test_cli_3_and_set_1_the_same_seed_replays_the_same_game(self):
        """REQ1/CLI-3, REQ1/SET-1: two bot games with one seed print the same transcript."""
        outs = []
        for _ in range(2):
            out = io.StringIO()
            self.assertEqual(main(["--p0", "random", "--p1", "greedy", "--seed", "5", "--chapters", "TDR,HOA"],
                                  read=Script(), write=out.write), 0)
            outs.append(out.getvalue())
        self.assertEqual(outs[0], outs[1])
        self.assertIn("seed 5", outs[0])
        self.assertIn("P0 learns TDR; P1 learns HOA", outs[0])

    def test_cli_5_simulate_prints_the_statistics(self):
        """REQ1/CLI-5: per-seat wins, mean rounds, endings by compile and by limit, mean compiled."""
        out = io.StringIO()
        self.assertEqual(main(["--p0", "random", "--p1", "random", "--seed", "1", "--simulate", "2"],
                              read=Script(), write=out.write), 0)
        text = out.getvalue()
        for key in ("games: 2", "p0_wins:", "p1_wins:", "mean_rounds:", "ended_by_compile:", "ended_by_limit:",
                    "mean_compiled:", "seconds:"):
            self.assertIn(key, text)
        out = io.StringIO()
        self.assertEqual(main(["--simulate", "2"], read=Script(), write=out.write), 2)
        self.assertIn("needs two bots", out.getvalue())

    def test_guide_1_a_missing_guide_stops_the_program(self):
        """REQ1/GUIDE-1: a wrong guide path is an exit code, not a warning."""
        out = io.StringIO()
        self.assertEqual(main(["--guide", "/nonexistent/guide", "--seed", "1"], read=Script(), write=out.write), 2)
        self.assertIn("cannot start", out.getvalue())


if __name__ == "__main__":
    unittest.main()
