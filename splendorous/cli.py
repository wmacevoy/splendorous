"""The terminal interface: the only module that reads input or prints.

Rendering and move descriptions are functions from state to text, so they are tested as
functions (SE1/T7); `play` takes its reader and writer as arguments, so a test can drive it with
a list of lines and a buffer. `main` is the thin edge that parses arguments and binds the real
terminal.
"""
import argparse
import random
import sys
import time
from typing import Callable, Dict, List, Optional

from . import engine
from .bots import BOTS
from .cards import CONFIDENCE, KINDS, LETTER, Card, build_cards
from .engine import (Assert, Demonstrate, Game, Gather, Refresh, Replenish, TakeConfidence, Whitespace,
                     apply, cost_for, lane_value, legal_moves, new_game, resign)
from .guide import GuideError, default_root, load_guide

Reader = Callable[[], Optional[str]]   # returns None at end of input
Writer = Callable[[str], None]


def card_line(card: Card) -> str:
    """REQ1/GUIDE-2: the versioned ID, the title, and the Ask where there is one."""
    line = f"{card.citation} {card.title}"
    if card.ask:
        line += f'\n    Ask: "{card.ask}"'
    return line


def cost_text(cost: Dict[str, int]) -> str:
    return " ".join(f"{LETTER[k]}{n}" for k, n in cost.items()) or "free"


def tokens_text(tokens: Dict[str, int]) -> str:
    parts = [f"{LETTER[k]}{tokens[k]}" for k in KINDS if tokens.get(k)]
    return " ".join(parts) or "none"


def render(game: Game, viewer: int) -> str:
    """The board, both players' tokens, the lanes, and the viewer's hand. The opponent's face-down
    cards are shown as `??` (REQ1/TURN-8)."""
    out = [f"Round {game.round} · P{game.current} to move · bag {len(game.bag)} · "
           f"Whitespace: middle {game.middle_whitespace}, P0 {game.players[0].whitespace}, P1 {game.players[1].whitespace}"]
    out.append("   " + " ".join(str(c) for c in range(engine.SIZE)))
    for r in range(engine.SIZE):
        row = [LETTER[game.board[(r, c)]] if game.board[(r, c)] else "." for c in range(engine.SIZE)]
        out.append(f" {r} " + " ".join(row))
    out.append("   R run  T test  A ask  N note  V review  S slack  C confidence")
    for p in (0, 1):
        pl = game.players[p]
        out.append(f"P{p} tokens: {tokens_text(pl.tokens)} ({pl.held()}/{engine.TOKEN_LIMIT}) · "
                   f"compiled: {''.join(pl.compiled) or '-'} · hand {len(pl.hand)} · deck {len(pl.deck)}")
    for lane in range(engine.LANES):
        sides = []
        for p in (0, 1):
            chapter = game.players[p].chapters[lane]
            done = "*" if chapter in game.players[p].compiled else ""
            cards = []
            for cid, face_up in game.lanes[lane][p]:
                if face_up:
                    cards.append(f"{cid}={game.cards[cid].value}")
                else:
                    cards.append(f"{cid}v2" if p == viewer else "??=2")
            sides.append(f"P{p} {chapter}{done} [{' '.join(cards)}] = {lane_value(game, lane, p)}")
        out.append(f"Lane {lane + 1}: " + "  |  ".join(sides))
    me = game.players[viewer]
    out.append(f"P{viewer} hand:")
    for cid in me.hand:
        card = game.cards[cid]
        out.append(f"  {cid:<4} value {card.value}  cost {cost_text(cost_for(game, viewer, card)):<10} "
                   f"{card.ability:<10} {card.title}")
    return "\n".join(out)


def describe(game: Game, move: object) -> str:
    if isinstance(move, Whitespace):
        return f"spend a Whitespace: take {game.board[move.cell]} at {move.cell}"
    if isinstance(move, Replenish):
        return "replenish the board from the bag (opponent gains a Whitespace)"
    if isinstance(move, Gather):
        kinds = ", ".join(f"{game.board[c]} at {c}" for c in move.cells)
        return f"gather {kinds}"
    if isinstance(move, TakeConfidence):
        return f"take a Confidence token at {move.cell}"
    if isinstance(move, Demonstrate):
        card = game.cards[move.card]
        text = f"demonstrate {card.citation} (value {card.value}, cost {cost_text(cost_for(game, game.current, card))})"
        if card.ability != "none":
            text += f" — {card.ability}"
            if move.target is not None:
                if card.ability == "take":
                    text += f" {game.board[move.target]} at {move.target}"
                elif card.ability == "steal":
                    text += f" a {move.target}"
                elif card.ability == "flip":
                    text += f" their face-down card #{move.target + 1}"
        return text
    if isinstance(move, Assert):
        return f"assert {move.card} face-down (value 2, costs one Confidence)"
    if isinstance(move, Refresh):
        return "refresh: discard the hand and draw five"
    return str(move)


def choose(game: Game, moves: List[object], read: Reader, write: Writer) -> Optional[object]:
    """REQ1/CLI-1, REQ1/CLI-4: list the moves; accept a listed number; refuse anything else and list
    again; return None at end of input."""
    while True:
        for i, m in enumerate(moves, 1):
            write(f"  {i:>3}. {describe(game, m)}\n")
        write(f"P{game.current}, choose 1-{len(moves)}: ")
        line = read()
        if line is None:
            return None
        line = line.strip()
        if line.isdigit() and 1 <= int(line) <= len(moves):
            return moves[int(line) - 1]
        write(f"'{line}' is not a number from 1 to {len(moves)}.\n")


def play(game: Game, seats: List[Optional[Callable]], read: Reader, write: Writer, bot_rng: random.Random) -> Game:
    """Play `game` out. A seat is None for a person or a bot function."""
    shown = len(game.log)
    while game.winner is None:
        bot = seats[game.current]
        moves = legal_moves(game)
        if bot is None:
            write(render(game, game.current) + "\n")
            move = choose(game, moves, read, write)
            if move is None:
                write(f"\nEnd of input: P{game.current} resigns.\n")
                game = resign(game, game.current)
                break
        else:
            move = bot(game, bot_rng)
            if move not in moves:
                raise engine.IllegalMove(f"bot at seat {game.current} returned an illegal move: {move}")
        if isinstance(move, Demonstrate):
            write(f"\nP{game.current} plays {card_line(game.cards[move.card])}\n")
        game = apply(game, move)
        for line in game.log[shown:]:
            write(f"> {line}\n")
        shown = len(game.log)
    write(f"\nP{game.winner} wins: {game.reason}\n")
    return game


def simulate(cards, n: int, bot0, bot1, seed: int, chapters=None) -> Dict[str, float]:
    """REQ1/CLI-5: n bot games with seeds seed..seed+n-1."""
    wins = [0, 0]
    rounds = 0
    by_compile = 0
    compiled = 0
    for i in range(n):
        game = new_game(cards, seed + i, chapters)
        bot_rng = random.Random(seed + i)
        while game.winner is None:
            game = apply(game, (bot0 if game.current == 0 else bot1)(game, bot_rng))
        wins[game.winner] += 1
        rounds += game.round
        by_compile += 1 if game.reason == "all three chapters compiled" else 0
        compiled += sum(len(p.compiled) for p in game.players)
    return {"games": n, "p0_wins": wins[0], "p1_wins": wins[1], "mean_rounds": rounds / n,
            "ended_by_compile": by_compile, "ended_by_limit": n - by_compile, "mean_compiled": compiled / n}


def parse_chapters(text: str):
    """REQ1/CLI-3: `TDR,HOA` -> (("T","D","R"),("H","O","A")); refuses anything else."""
    parts = text.upper().split(",")
    six = [ch for part in parts for ch in part]
    if len(parts) != 2 or len(six) != 6 or len(set(six)) != 6 or any(ch not in engine.CHAPTERS for ch in six):
        raise argparse.ArgumentTypeError(
            f"--chapters takes two groups of three distinct letters from {engine.CHAPTERS}, like TDR,HOA")
    return tuple(six[:3]), tuple(six[3:])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="splendorous", description="Learn the software-engineering guide by playing it.")
    seats = ["human"] + list(BOTS)
    ap.add_argument("--p0", choices=seats, default="human", help="seat 0, moves first (default: human)")
    ap.add_argument("--p1", choices=seats, default="greedy", help="seat 1 (default: greedy)")
    ap.add_argument("--seed", type=int, default=None, help="fixes the deal and the shuffles; printed when drawn")
    ap.add_argument("--chapters", type=parse_chapters, default=None, help="six chapter letters, like TDR,HOA")
    ap.add_argument("--simulate", type=int, metavar="N", default=None, help="play N bot games and print statistics")
    ap.add_argument("--guide", default=None, help="path of the vendored guide (default: vendor/software-engineering)")
    return ap


def main(argv: Optional[List[str]] = None, read: Optional[Reader] = None, write: Optional[Writer] = None) -> int:
    args = build_parser().parse_args(argv)
    write = write or sys.stdout.write
    read = read or (lambda: (lambda s: s if s != "" else None)(sys.stdin.readline()))
    try:
        cards = build_cards(load_guide(args.guide or default_root()))
    except (GuideError, Exception) as e:  # REQ1/GUIDE-1: a power-on self test, not a warning
        write(f"splendorous: cannot start: {e}\n")
        return 2
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1 << 30)
    write(f"seed {seed}\n")
    if args.simulate is not None:
        if args.p0 == "human" or args.p1 == "human":
            write("--simulate needs two bots: --p0 and --p1 among " + ", ".join(BOTS) + "\n")
            return 2
        started = time.perf_counter()
        stats = simulate(cards, args.simulate, BOTS[args.p0], BOTS[args.p1], seed, args.chapters)
        stats["seconds"] = round(time.perf_counter() - started, 2)
        for k, v in stats.items():
            write(f"{k}: {v}\n")
        return 0
    seats = [None if args.p0 == "human" else BOTS[args.p0], None if args.p1 == "human" else BOTS[args.p1]]
    game = new_game(cards, seed, args.chapters)
    write(f"P0 learns {''.join(game.players[0].chapters)}; P1 learns {''.join(game.players[1].chapters)}\n")
    play(game, seats, read, write, random.Random(seed))
    return 0
