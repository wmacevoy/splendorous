"""Shared helpers for the tests. The guide is loaded once; every test gets its own game state."""
import random
from functools import lru_cache
from typing import Dict

from splendorous.cards import CONFIDENCE, KINDS, Card, build_cards
from splendorous.engine import SPIRAL, Game, new_game
from splendorous.guide import default_root, load_guide

CHAPTERS = (("T", "D", "R"), ("H", "O", "A"))


@lru_cache(maxsize=None)
def cards() -> Dict[str, Card]:
    return build_cards(load_guide(default_root()))


def fresh(seed: int = 1, chapters=CHAPTERS) -> Game:
    return new_game(cards(), seed, chapters)


def clear_board(game: Game) -> None:
    """Move every board token into the bag, leaving an empty board for a test to arrange."""
    for cell in SPIRAL:
        if game.board[cell] is not None:
            game.bag.append(game.board[cell])
            game.board[cell] = None


def take_one(game: Game, kind: str) -> None:
    """Remove one token of `kind` from the bag, or failing that from the board, so 25 still holds."""
    if kind in game.bag:
        game.bag.remove(kind)
        return
    for cell in SPIRAL:
        if game.board[cell] == kind:
            game.board[cell] = None
            return
    raise AssertionError(f"no {kind} token is free in the bag or on the board")


def place(game: Game, cell, kind: str) -> None:
    """Put a token of `kind` at `cell`, taking it from the bag or elsewhere on the board."""
    if game.board[cell] is not None:
        game.bag.append(game.board[cell])
    take_one(game, kind)
    game.board[cell] = kind


def give(game: Game, player: int, kind: str, n: int = 1) -> None:
    """Hand a player n tokens of `kind`, from the bag or the board."""
    for _ in range(n):
        take_one(game, kind)
        game.players[player].tokens[kind] += 1


def put_in_hand(game: Game, player: int, card_id: str) -> None:
    """Make sure a card is in a player's hand, pulling it from the deck or discard."""
    p = game.players[player]
    if card_id in p.hand:
        return
    for pile in (p.deck, p.discard):
        if card_id in pile:
            pile.remove(card_id)
            p.hand.append(card_id)
            return
    raise AssertionError(f"{card_id} is not in P{player}'s deck, hand, or discard")


def token_count(game: Game) -> int:
    on_board = sum(1 for v in game.board.values() if v is not None)
    return on_board + len(game.bag) + sum(p.held() for p in game.players)


def card_count(game: Game) -> int:
    in_lanes = sum(len(side) for lane in game.lanes for side in lane)
    return in_lanes + sum(len(p.deck) + len(p.hand) + len(p.discard) for p in game.players)


def rng(seed: int = 0) -> random.Random:
    return random.Random(seed)


__all__ = ["CHAPTERS", "CONFIDENCE", "KINDS", "cards", "fresh", "clear_board", "place", "give", "put_in_hand",
           "token_count", "card_count", "rng"]
