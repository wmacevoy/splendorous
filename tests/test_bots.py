"""The bots (REQ1/BOT-1, REQ1/BOT-2) and the simulation's speed (REQ1/CLI-5)."""
import time
import unittest

from splendorous.bots import BOTS, greedy_bot, random_bot
from splendorous.cli import simulate
from splendorous.engine import apply, legal_moves, new_game

from support import cards, rng


class TestConformance(unittest.TestCase):
    def test_bot_1_every_bot_returns_a_legal_move(self):
        """REQ1/BOT-1: one check for every bot, over the states of a seeded game each."""
        for name, bot in BOTS.items():
            g = new_game(cards(), 11)
            r = rng(11)
            for _ in range(60):
                if g.winner is not None:
                    break
                move = bot(g, r)
                self.assertIn(move, legal_moves(g), name)
                g = apply(g, move)


class TestStrength(unittest.TestCase):
    """One run of 100 games serves REQ1/BOT-2 and REQ1/CLI-5, so the suite pays for it once."""

    @classmethod
    def setUpClass(cls):
        started = time.perf_counter()
        cls.as_p0 = simulate(cards(), 50, greedy_bot, random_bot, seed=0)
        cls.as_p1 = simulate(cards(), 50, random_bot, greedy_bot, seed=50)
        cls.seconds = time.perf_counter() - started

    def test_bot_2_greedy_beats_random_in_more_than_60_percent(self):
        """REQ1/BOT-2: 100 games, 50 from each seat, seeds 0–99."""
        greedy_wins = self.as_p0["p0_wins"] + self.as_p1["p1_wins"]
        self.assertGreater(greedy_wins, 60, (self.as_p0, self.as_p1))

    def test_cli_5_a_hundred_games_finish_in_under_sixty_seconds(self):
        """REQ1/CLI-5: the stats carry the promised keys, add up, and 100 games take under 60 s."""
        for stats in (self.as_p0, self.as_p1):
            self.assertEqual(stats["games"], 50)
            self.assertEqual(stats["p0_wins"] + stats["p1_wins"], 50)
            self.assertEqual(stats["ended_by_compile"] + stats["ended_by_limit"], 50)
            self.assertGreaterEqual(stats["mean_rounds"], 1)
            self.assertGreaterEqual(stats["mean_compiled"], 0)
        self.assertLess(self.seconds, 60)


if __name__ == "__main__":
    unittest.main()
