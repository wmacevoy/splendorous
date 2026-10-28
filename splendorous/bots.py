"""Two sparring partners. Every bot has one shape: `bot(game, rng) -> move`, returning one of
`legal_moves(game)` (REQ1/BOT-1), so one conformance test holds for both (SE1/T6).

`random_bot` picks uniformly. `greedy_bot` looks one move ahead: it applies each legal move and
scores the result for the mover, keeping the first best. It is a one-ply heuristic on purpose
(REQUIREMENTS_v1, Non-goals): good enough to punish a player who never gathers evidence.
"""
import random
from typing import Callable, Dict, List

from .cards import CONFIDENCE
from .engine import LANES, TARGET, Game, apply, can_pay, cost_for, lane_value, legal_moves

Bot = Callable[[Game, random.Random], object]


def random_bot(game: Game, rng: random.Random) -> object:
    return rng.choice(legal_moves(game))


def score(game: Game, player: int) -> float:
    """How good `game` looks to `player`. Compiles dominate; lane progress, playable cards, and
    tokens break ties; the opponent's progress counts against."""
    me, other = game.players[player], game.players[1 - player]
    if game.winner == player:
        return 1e9
    if game.winner is not None:
        return -1e9
    s = 1000.0 * len(me.compiled) - 1000.0 * len(other.compiled)
    for lane in range(LANES):
        mine, theirs = lane_value(game, lane, player), lane_value(game, lane, 1 - player)
        chapter = me.chapters[lane]
        if chapter not in me.compiled:
            s += 12.0 * min(mine, TARGET)
            if mine >= TARGET and mine > theirs:
                s += 60.0  # will compile at the start of my next turn, unless they pass me
        if other.chapters[lane] not in other.compiled:
            s -= 8.0 * min(theirs, TARGET)
            if theirs >= TARGET and theirs > mine:
                s -= 40.0
    for cid in me.hand:
        card = game.cards[cid]
        cost = cost_for(game, player, card)
        deficit = sum(max(0, n - me.tokens.get(k, 0)) for k, n in cost.items())
        s += 3.0 * card.value / (1 + deficit) + (2.0 if can_pay(me, cost) else 0.0)
    s += 1.0 * (me.held() - me.tokens[CONFIDENCE]) + 0.5 * me.tokens[CONFIDENCE]
    s += 2.0 * me.whitespace + 0.5 * len(me.hand)
    return s


def greedy_bot(game: Game, rng: random.Random) -> object:
    best, best_score = None, None
    for move in legal_moves(game):
        value = score(apply(game, move, check=False), game.current)
        if best_score is None or value > best_score:
            best, best_score = move, value
    return best


BOTS: Dict[str, Bot] = {"random": random_bot, "greedy": greedy_bot}


def names() -> List[str]:
    return list(BOTS)
