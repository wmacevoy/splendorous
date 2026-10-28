"""The rules (REQ1/SET-*, TURN-*, REQ1/CARD-3, REQ1/CARD-4, LANE-*, END-*), as pure functions on a state."""
import unittest

from splendorous.bots import greedy_bot, random_bot
from splendorous.cards import CONFIDENCE, SLACK, cards_of_chapter
from splendorous.cli import render
from splendorous.engine import (LANES, ROUND_LIMIT, SIZE, SPIRAL, TOKEN_LIMIT, WHITESPACE_TOTAL, Assert,
                                Demonstrate, Gather, IllegalMove, Refresh, Replenish, TakeConfidence,
                                Whitespace, ability_targets, apply, lane_of, lane_value, legal_moves, new_game)

from support import (CHAPTERS, card_count, cards, clear_board, fresh, give, place, put_in_hand, rng,
                     token_count)


def moves_of(game, kind):
    return [m for m in legal_moves(game) if isinstance(m, kind)]


class TestSetup(unittest.TestCase):
    def test_set_1_same_seed_and_moves_give_the_same_game(self):
        """REQ1/SET-1: two games from one seed stay identical move for move; another seed differs."""
        a, b = fresh(7), fresh(7)
        r = rng(7)
        for _ in range(40):
            move = greedy_bot(a, r)
            a, b = apply(a, move), apply(b, move)
        self.assertEqual(render(a, 0), render(b, 0))
        self.assertEqual(a.log, b.log)
        self.assertNotEqual(fresh(7).players[0].hand, fresh(8).players[0].hand)

    def test_set_2_chapters_are_six_distinct_given_or_dealt(self):
        """REQ1/SET-2: given chapters are used; dealt ones are six distinct; bad sets are refused."""
        self.assertEqual(fresh().players[0].chapters, ("T", "D", "R"))
        dealt = new_game(cards(), 3)
        six = dealt.players[0].chapters + dealt.players[1].chapters
        self.assertEqual(len(set(six)), 6)
        for bad in [(("T", "D", "R"), ("T", "O", "A")), (("T", "D", "Z"), ("H", "O", "A")), (("T", "D"), ("H", "O", "A"))]:
            with self.assertRaises(ValueError):
                new_game(cards(), 1, bad)

    def test_set_3_deck_is_the_chapters_cards_and_the_hand_is_five(self):
        """REQ1/SET-3: deck plus hand is every card of the three chapters; five are in hand."""
        for p, chs in zip(fresh().players, CHAPTERS):
            expected = {cid for ch in chs for cid in cards_of_chapter(cards(), ch)}
            self.assertEqual(set(p.deck) | set(p.hand), expected)
            self.assertEqual(len(p.hand), 5)
            self.assertEqual(len(p.deck) + 5, len(expected))
        self.assertNotEqual(fresh(1).players[0].deck, fresh(2).players[0].deck)

    def test_set_4_board_is_filled_from_the_bag_in_a_spiral(self):
        """REQ1/SET-4: 25 cells full, bag empty; the spiral starts at the center and steps to a neighbor."""
        g = fresh()
        self.assertEqual(sum(1 for v in g.board.values() if v is not None), 25)
        self.assertEqual(g.bag, [])
        self.assertEqual(SPIRAL[0], (SIZE // 2, SIZE // 2))
        self.assertEqual(set(SPIRAL), {(r, c) for r in range(SIZE) for c in range(SIZE)})
        for (r1, c1), (r2, c2) in zip(SPIRAL, SPIRAL[1:]):
            self.assertLessEqual(max(abs(r1 - r2), abs(c1 - c2)), 1)
        self.assertEqual(token_count(g), 25)

    def test_set_5_whitespace_starts_one_with_player_1_two_in_the_middle(self):
        """REQ1/SET-5."""
        g = fresh()
        self.assertEqual((g.players[0].whitespace, g.players[1].whitespace, g.middle_whitespace), (0, 1, 2))
        self.assertEqual(WHITESPACE_TOTAL, 3)

    def test_set_6_lane_i_holds_each_players_ith_chapter(self):
        """REQ1/SET-6."""
        g = fresh()
        self.assertEqual(lane_of(g, 0, "D"), 1)
        self.assertEqual(lane_of(g, 1, "O"), 1)
        self.assertEqual(lane_of(g, 1, "A"), 2)


class TestTurn(unittest.TestCase):
    def test_turn_1_a_main_action_ends_the_turn_and_an_optional_one_does_not(self):
        """REQ1/TURN-1: player 0 first; Refresh switches the player; a Whitespace spend does not."""
        g = fresh()
        self.assertEqual(g.current, 0)
        g.middle_whitespace -= 1
        g.players[0].whitespace += 1
        g2 = apply(g, moves_of(g, Whitespace)[0])
        self.assertEqual(g2.current, 0)
        g3 = apply(g2, Refresh())
        self.assertEqual(g3.current, 1)
        self.assertEqual(g3.round, 1)
        self.assertEqual(apply(g3, Refresh()).round, 2)

    def test_turn_2_whitespace_takes_one_non_confidence_token(self):
        """REQ1/TURN-2: needs a scroll; any non-Confidence token; the scroll goes back to the middle."""
        g = fresh()
        self.assertEqual(moves_of(g, Whitespace), [])
        g.middle_whitespace -= 1
        g.players[0].whitespace += 1
        options = moves_of(g, Whitespace)
        self.assertEqual({m.cell for m in options},
                         {c for c in SPIRAL if g.board[c] is not None and g.board[c] != CONFIDENCE})
        cell = options[0].cell
        kind = g.board[cell]
        g2 = apply(g, Whitespace(cell))
        self.assertIsNone(g2.board[cell])
        self.assertEqual(g2.players[0].tokens[kind], 1)
        self.assertEqual((g2.players[0].whitespace, g2.middle_whitespace), (0, 2))

    def test_turn_3_replenish_fills_gaps_in_spiral_order_once_per_turn(self):
        """REQ1/TURN-3: only with a bag and a gap; fills in spiral order; opponent gains a Whitespace. "At
        most once" needs no flag: afterwards the board is full or the bag is empty (FINDINGS 2026-10-28)."""
        g = fresh()
        self.assertEqual(moves_of(g, Replenish), [])
        for cell in (SPIRAL[3], SPIRAL[10], SPIRAL[24]):
            g.bag.append(g.board[cell])
            g.board[cell] = None
        g.bag = g.bag[:2]  # two tokens for three gaps
        lost = g.bag[-1], g.bag[-2]
        g2 = apply(g, Replenish())
        self.assertEqual((g2.board[SPIRAL[3]], g2.board[SPIRAL[10]]), lost)
        self.assertIsNone(g2.board[SPIRAL[24]])
        self.assertEqual(g2.bag, [])
        self.assertEqual((g2.players[1].whitespace, g2.middle_whitespace), (2, 1))
        self.assertEqual(g2.current, 0)
        self.assertEqual(moves_of(g2, Replenish), [])
        g3 = apply(apply(g2, Refresh()), Refresh())  # a round later, with a gap and a bag again
        g3.bag.append("run")
        self.assertTrue(moves_of(g3, Replenish))

    def test_turn_4_gather_is_one_to_three_adjacent_tokens_in_a_line(self):
        """REQ1/TURN-4: straight, adjacent, no gap, no Confidence, at most three."""
        g = fresh()
        clear_board(g)
        for cell, kind in {(0, 0): "run", (0, 1): "test", (0, 2): "ask", (0, 4): "note", (1, 0): CONFIDENCE,
                           (1, 1): "review", (2, 2): "review"}.items():
            place(g, cell, kind)
        gathers = {m.cells for m in moves_of(g, Gather)}
        self.assertIn(((0, 0), (0, 1), (0, 2)), gathers)          # a row
        self.assertIn(((0, 0), (1, 1), (2, 2)), gathers)          # a diagonal
        self.assertIn(((0, 4),), gathers)                          # a single token
        self.assertNotIn(((0, 2), (0, 3), (0, 4)), gathers)       # a gap
        self.assertFalse(any((1, 0) in cells for cells in gathers))  # never Confidence
        self.assertTrue(all(len(cells) <= 3 for cells in gathers))
        self.assertFalse(any(len(cells) == 4 for cells in gathers))
        g2 = apply(g, Gather(((0, 0), (0, 1), (0, 2))))
        self.assertEqual([g2.board[c] for c in ((0, 0), (0, 1), (0, 2))], [None] * 3)
        self.assertEqual((g2.players[0].tokens["run"], g2.players[0].tokens["test"], g2.players[0].tokens["ask"]), (1, 1, 1))
        self.assertEqual(g2.current, 1)

    def test_turn_5_three_of_a_kind_or_two_slack_give_the_opponent_a_whitespace(self):
        """REQ1/TURN-5: three alike, or two Slack, hands P1 a scroll; a mixed three does not."""
        g = fresh()
        clear_board(g)
        for cell, kind in {(0, 0): "test", (0, 1): "test", (0, 2): "test", (2, 0): SLACK, (2, 1): SLACK,
                           (4, 0): "run", (4, 1): "ask", (4, 2): "note"}.items():
            place(g, cell, kind)
        self.assertEqual(apply(g, Gather(((0, 0), (0, 1), (0, 2)))).players[1].whitespace, 2)
        self.assertEqual(apply(g, Gather(((2, 0), (2, 1)))).players[1].whitespace, 2)
        self.assertEqual(apply(g, Gather(((4, 0), (4, 1), (4, 2)))).players[1].whitespace, 1)
        self.assertEqual(apply(g, Gather(((0, 0), (0, 1)))).players[1].whitespace, 1)

    def test_turn_6_take_confidence(self):
        """REQ1/TURN-6: one Confidence token from the board is a whole main action."""
        g = fresh()
        options = moves_of(g, TakeConfidence)
        self.assertEqual({m.cell for m in options}, {c for c in SPIRAL if g.board[c] == CONFIDENCE})
        g2 = apply(g, options[0])
        self.assertEqual(g2.players[0].tokens[CONFIDENCE], 1)
        self.assertIsNone(g2.board[options[0].cell])
        self.assertEqual(g2.current, 1)

    def test_turn_7_demonstrate_pays_the_cost_and_plays_face_up(self):
        """REQ1/TURN-7: the cost leaves the player for the bag; the card lands face-up in its lane."""
        g = fresh()
        put_in_hand(g, 0, "T4")  # value 1, cost one test, no ability
        self.assertNotIn(Demonstrate("T4"), legal_moves(g))
        give(g, 0, "test")
        self.assertIn(Demonstrate("T4"), legal_moves(g))
        bag_before = len(g.bag)
        g2 = apply(g, Demonstrate("T4"))
        self.assertEqual(g2.lanes[0][0], [("T4", True)])
        self.assertNotIn("T4", g2.players[0].hand)
        self.assertEqual(g2.players[0].tokens["test"], 0)
        self.assertEqual(len(g2.bag), bag_before + 1)
        self.assertEqual(lane_value(g2, 0, 0), 1)
        self.assertEqual(g2.current, 1)

    def test_turn_8_assert_costs_one_confidence_and_is_worth_two(self):
        """REQ1/TURN-8: any card, face-down, for a Confidence; worth 2; hidden from the opponent."""
        g = fresh()
        put_in_hand(g, 0, "T3")
        self.assertEqual(moves_of(g, Assert), [])
        give(g, 0, CONFIDENCE)
        self.assertIn(Assert("T3"), legal_moves(g))
        g2 = apply(g, Assert("T3"))
        self.assertEqual(g2.lanes[0][0], [("T3", False)])
        self.assertEqual(lane_value(g2, 0, 0), 2)
        self.assertEqual(g2.players[0].tokens[CONFIDENCE], 0)
        self.assertIn("T3", render(g2, 0))
        self.assertNotIn("T3", render(g2, 1).split("P1 hand:")[0])

    def test_turn_9_refresh_discards_the_hand_and_draws_five(self):
        """REQ1/TURN-9."""
        g = fresh()
        hand, deck = list(g.players[0].hand), len(g.players[0].deck)
        g2 = apply(g, Refresh())
        p = g2.players[0]
        self.assertEqual(p.discard, hand)
        self.assertEqual(len(p.hand), 5)
        self.assertEqual(len(p.deck), deck - 5)
        self.assertTrue(set(p.hand).isdisjoint(hand))

    def test_turn_10_ten_tokens_is_the_limit_and_spent_tokens_return_to_the_bag(self):
        """REQ1/TURN-10: at ten nothing more can be taken; at nine only one; payment refills the bag."""
        g = fresh()
        g.middle_whitespace -= 1
        g.players[0].whitespace += 1
        for kind in ("run", "test", "ask", "note", "review"):
            give(g, 0, kind, 2)
        self.assertEqual(g.players[0].held(), TOKEN_LIMIT)
        self.assertEqual(moves_of(g, Gather), [])
        self.assertEqual(moves_of(g, TakeConfidence), [])
        self.assertEqual(moves_of(g, Whitespace), [])
        g.bag.append("ask")
        g.players[0].tokens["ask"] -= 1
        self.assertTrue(all(len(m.cells) == 1 for m in moves_of(g, Gather)))
        self.assertTrue(moves_of(g, TakeConfidence))
        put_in_hand(g, 0, "T8")  # value 4: test 2, run 2
        bag_before = len(g.bag)
        self.assertEqual(len(apply(g, Demonstrate("T8")).bag), bag_before + 4)

    def test_turn_11_a_whitespace_comes_from_the_middle_then_the_opponent_then_nowhere(self):
        """REQ1/TURN-11, driven by Replenish, which hands the opponent a scroll."""
        g = fresh()
        g.bag.append(g.board[SPIRAL[0]])
        g.board[SPIRAL[0]] = None
        g2 = apply(g, Replenish())
        self.assertEqual((g2.middle_whitespace, g2.players[0].whitespace, g2.players[1].whitespace), (1, 0, 2))
        g.middle_whitespace, g.players[0].whitespace, g.players[1].whitespace = 0, 3, 0
        g3 = apply(g, Replenish())
        self.assertEqual((g3.middle_whitespace, g3.players[0].whitespace, g3.players[1].whitespace), (0, 2, 1))
        g.middle_whitespace, g.players[0].whitespace, g.players[1].whitespace = 0, 0, 3
        g4 = apply(g, Replenish())
        self.assertEqual((g4.middle_whitespace, g4.players[0].whitespace, g4.players[1].whitespace), (0, 0, 3))

    def test_turn_12_an_empty_deck_reshuffles_the_discard_or_draws_nothing(self):
        """REQ1/TURN-12."""
        g = fresh()
        p = g.players[0]
        p.discard, p.deck = p.deck, []
        g2 = apply(g, Refresh())
        self.assertEqual(len(g2.players[0].hand), 5)
        self.assertEqual(len(g2.players[0].discard), 0)
        g = fresh()
        p = g.players[0]
        p.deck, p.discard, p.hand = [], [], []
        g3 = apply(g, Refresh())
        self.assertEqual(g3.players[0].hand, [])


class TestAbilities(unittest.TestCase):
    def test_card_3_draw(self):
        """REQ1/CARD-3 draw: two more cards in hand."""
        g = fresh()
        put_in_hand(g, 0, "T1")  # value 2, draw: test 1, run 1
        give(g, 0, "test")
        give(g, 0, "run")
        g2 = apply(g, Demonstrate("T1"))
        self.assertEqual(len(g2.players[0].hand), len(g.players[0].hand) - 1 + 2)

    def test_card_3_take(self):
        """REQ1/CARD-3 take: any non-Confidence board token, chosen by the player."""
        g = fresh()
        put_in_hand(g, 0, "D5")  # value 2, take: note 1, review 1
        give(g, 0, "note")
        give(g, 0, "review")
        options = [m for m in moves_of(g, Demonstrate) if m.card == "D5"]
        self.assertEqual({m.target for m in options},
                         {c for c in SPIRAL if g.board[c] is not None and g.board[c] != CONFIDENCE})
        cell = options[0].target
        kind = g.board[cell]
        g2 = apply(g, options[0])
        self.assertIsNone(g2.board[cell])
        self.assertEqual(g2.players[0].tokens[kind], 1)

    def test_card_3_whitespace(self):
        """REQ1/CARD-3 whitespace: a scroll from the middle."""
        g = fresh()
        put_in_hand(g, 0, "D12")  # value 0, whitespace, free
        self.assertIn(Demonstrate("D12"), legal_moves(g))
        g2 = apply(g, Demonstrate("D12"))
        self.assertEqual((g2.players[0].whitespace, g2.middle_whitespace), (1, 1))
        self.assertEqual(g2.lanes[1][0], [("D12", True)])

    def test_card_3_flip_removes_one_opposing_face_down_card_in_the_lane(self):
        """REQ1/CARD-3 flip: the chosen face-down card goes to its owner's discard; face-up ones are safe."""
        g = fresh()
        put_in_hand(g, 0, "D13")  # value 2, flip: note 1, review 1
        give(g, 0, "note")
        give(g, 0, "review")
        self.assertIn(Demonstrate("D13"), legal_moves(g))  # no target: fires with nothing to do
        p1 = g.players[1]
        for cid in ("O1", "O2", "O3"):
            put_in_hand(g, 1, cid)
            p1.hand.remove(cid)
        g.lanes[1][1] = [("O1", True), ("O2", False), ("O3", False)]
        options = [m for m in moves_of(g, Demonstrate) if m.card == "D13"]
        self.assertEqual({m.target for m in options}, {1, 2})
        g2 = apply(g, Demonstrate("D13", 2))
        self.assertEqual(g2.lanes[1][1], [("O1", True), ("O2", False)])
        self.assertIn("O3", g2.players[1].discard)
        self.assertEqual(card_count(g2), card_count(g))

    def test_card_3_steal(self):
        """REQ1/CARD-3 steal: one non-Confidence token of the opponent's, chosen by the player."""
        g = apply(fresh(), Refresh())  # P1 to move: O8 is P1's
        put_in_hand(g, 1, "O8")  # value 5, steal: run 2, test 2, slack 1
        give(g, 1, "run", 2)
        give(g, 1, "test", 2)
        give(g, 1, SLACK)
        self.assertIn(Demonstrate("O8"), legal_moves(g))  # P0 holds nothing: no target
        give(g, 0, "note")
        give(g, 0, CONFIDENCE)
        options = [m for m in moves_of(g, Demonstrate) if m.card == "O8"]
        self.assertEqual({m.target for m in options}, {"note"})
        g2 = apply(g, Demonstrate("O8", "note"))
        self.assertEqual((g2.players[0].tokens["note"], g2.players[1].tokens["note"]), (0, 1))
        self.assertEqual(token_count(g2), 25)

    def test_card_3_none(self):
        """REQ1/CARD-3: a card with no ability is one move and changes only its lane and the tokens."""
        g = fresh()
        put_in_hand(g, 0, "T4")
        give(g, 0, "test")
        self.assertEqual([m for m in moves_of(g, Demonstrate) if m.card == "T4"], [Demonstrate("T4")])
        g2 = apply(g, Demonstrate("T4"))
        self.assertEqual(len(g2.players[0].hand), len(g.players[0].hand) - 1)
        self.assertEqual(g2.players[0].whitespace, 0)

    def test_card_4_take_and_steal_have_no_target_without_room(self):
        """REQ1/CARD-4: with no room under the limit, take and steal offer nothing. Under the v1
        numbers this cannot arise in play (paying the card's cost always frees a slot), so the guard
        is tested directly; FINDINGS records that."""
        g = fresh()
        give(g, 1, "note")
        self.assertEqual(ability_targets(g, 0, cards()["D5"], room=0), [])
        self.assertTrue(ability_targets(g, 0, cards()["D5"], room=1))
        self.assertEqual(ability_targets(g, 0, cards()["O8"], room=0), [])
        self.assertEqual(ability_targets(g, 0, cards()["O8"], room=1), ["note"])


class TestLanesAndEnd(unittest.TestCase):
    def stage(self, lanes0, lanes1):
        """A game at the start of P0's turn with lane 0 holding the given cards (as (id, face_up))."""
        g = apply(fresh(), Refresh())  # P1 to move
        for side, entries in ((0, lanes0), (1, lanes1)):
            for cid, _ in entries:
                put_in_hand(g, side, cid)
                g.players[side].hand.remove(cid)
            g.lanes[0][side] = list(entries)
        return g

    def test_lane_1_value_is_face_up_values_plus_two_per_face_down(self):
        """REQ1/LANE-1."""
        g = self.stage([("T3", True), ("T4", False), ("T2", True)], [])
        self.assertEqual(lane_value(g, 0, 0), 5 + 2 + 4)
        self.assertEqual(lane_value(g, 0, 1), 0)

    def test_lane_2_compile_needs_ten_and_more_than_the_opponent_at_turn_start(self):
        """REQ1/LANE-2: 10 to 5 compiles and clears both sides; 10 to 10 does not; 9 does not."""
        g = self.stage([("T3", True), ("T10", True)], [("H6", True)])
        g2 = apply(g, Refresh())  # P1 passes; P0's turn begins
        self.assertEqual(g2.players[0].compiled, ["T"])
        self.assertEqual(g2.lanes[0], [[], []])
        self.assertIn("T3", g2.players[0].discard)
        self.assertIn("H6", g2.players[1].discard)
        self.assertEqual(card_count(g2), card_count(g))
        tie = self.stage([("T3", True), ("T10", True)], [("H6", True), ("H7", True)])
        self.assertEqual(apply(tie, Refresh()).players[0].compiled, [])
        short = self.stage([("T3", True), ("T8", True)], [])
        self.assertEqual(apply(short, Refresh()).players[0].compiled, [])

    def test_lane_3_a_compiled_chapter_stays_compiled_and_its_lane_stays_open(self):
        """REQ1/LANE-3: no second compile; cards may still be played there and count for blocking."""
        g = self.stage([("T3", True), ("T10", True)], [])
        g.players[0].compiled = ["T"]
        g2 = apply(g, Refresh())
        self.assertEqual(g2.players[0].compiled, ["T"])
        self.assertEqual(g2.lanes[0][0], [("T3", True), ("T10", True)])
        put_in_hand(g2, 0, "T4")
        give(g2, 0, "test")
        self.assertIn(Demonstrate("T4"), legal_moves(g2))

    def test_end_1_the_third_compile_wins_at_once(self):
        """REQ1/END-1."""
        g = self.stage([("T3", True), ("T10", True)], [])
        g.players[0].compiled = ["D", "R"]
        g2 = apply(g, Refresh())
        self.assertEqual(g2.winner, 0)
        self.assertEqual(g2.reason, "all three chapters compiled")

    def test_end_2_the_round_limit_ends_the_game_with_three_tie_breaks(self):
        """REQ1/END-2: more compiled; else higher lane total; else player 1."""
        def finish(g):
            g.round = ROUND_LIMIT
            return apply(apply(g, Refresh()), Refresh())
        g = finish(fresh())
        self.assertEqual((g.winner, g.round), (1, ROUND_LIMIT + 1))
        self.assertIn("tie", g.reason)
        g = fresh()
        g.players[0].compiled = ["T"]
        self.assertEqual(finish(g).winner, 0)
        g = fresh()
        g.players[0].compiled, g.players[1].compiled = ["T"], ["H"]
        put_in_hand(g, 0, "T4")
        g.players[0].hand.remove("T4")
        g.lanes[0][0] = [("T4", True)]
        self.assertEqual(finish(g).winner, 0)

    def test_end_3_an_ended_game_offers_no_move(self):
        """REQ1/END-3."""
        g = fresh()
        g.round = ROUND_LIMIT
        g = apply(apply(g, Refresh()), Refresh())
        self.assertIsNotNone(g.winner)
        self.assertEqual(legal_moves(g), [])
        with self.assertRaises(IllegalMove):
            apply(g, Refresh())


class TestInvariants(unittest.TestCase):
    def test_random_games_keep_every_token_card_and_scroll(self):
        """REQ1/SET-4, REQ1/SET-5, REQ1/TURN-10, REQ1/END-2: over 20 seeded random games, 25 tokens, every card,
        and three scrolls are always accounted for; a move is always offered; the game ends in time."""
        for seed in range(20):
            g = new_game(cards(), seed)
            r = rng(seed)
            total_cards = card_count(g)
            steps = 0
            while g.winner is None:
                self.assertEqual(token_count(g), 25, seed)
                self.assertEqual(card_count(g), total_cards, seed)
                self.assertEqual(g.middle_whitespace + sum(p.whitespace for p in g.players), WHITESPACE_TOTAL, seed)
                self.assertTrue(all(p.held() <= TOKEN_LIMIT for p in g.players), seed)
                moves = legal_moves(g)
                self.assertTrue(moves, seed)
                g = apply(g, random_bot(g, r))
                steps += 1
            self.assertLessEqual(g.round, ROUND_LIMIT + 1)
            self.assertIn(g.winner, (0, 1))
            self.assertEqual(legal_moves(g), [])


if __name__ == "__main__":
    unittest.main()
