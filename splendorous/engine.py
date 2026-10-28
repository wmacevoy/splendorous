"""The rules of Splendorous, as pure functions over a game state.

`new_game` builds a state from a seed; `legal_moves` lists what the current player may do;
`apply` returns the state after a move. Nothing here reads a clock, the terminal, or a file:
randomness is a `random.Random` carried in the state and seeded once (REQ1/SET-1), so a game is
replayable and a test is repeatable (SE1/D7, SE1/T5). The rules cite REQUIREMENTS_v1 by ID.
"""
import copy
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .cards import BAG, CHAPTERS, CONFIDENCE, KINDS, SLACK, Card, cards_of_chapter, discounted_cost

SIZE = 5
LANES = 3
HAND = 5
TARGET = 10         # REQ1/LANE-2 (invented)
TOKEN_LIMIT = 10    # REQ1/TURN-10 (invented)
ROUND_LIMIT = 100   # REQ1/END-2 (invented)
WHITESPACE_TOTAL = 3  # REQ1/SET-5 (invented)
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))  # a row, a column, the two diagonals

Cell = Tuple[int, int]


def spiral_order() -> List[Cell]:
    """The 25 cells from the center outward (REQ1/SET-4): right, down, left, up, widening."""
    r, c = SIZE // 2, SIZE // 2
    order = [(r, c)]
    steps = 1
    while len(order) < SIZE * SIZE:
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            for _ in range(steps):
                r, c = r + dr, c + dc
                if 0 <= r < SIZE and 0 <= c < SIZE and len(order) < SIZE * SIZE:
                    order.append((r, c))
            if dr == 1 or dr == -1:
                steps += 1
    return order


SPIRAL = spiral_order()


# ---------------------------------------------------------------- moves

@dataclass(frozen=True)
class Whitespace:          # REQ1/TURN-2, optional
    cell: Cell


@dataclass(frozen=True)
class Replenish:           # REQ1/TURN-3, optional
    pass


@dataclass(frozen=True)
class Gather:              # REQ1/TURN-4
    cells: Tuple[Cell, ...]


@dataclass(frozen=True)
class TakeConfidence:      # REQ1/TURN-6
    cell: Cell


@dataclass(frozen=True)
class Demonstrate:         # REQ1/TURN-7; target is the ability's choice, or None
    card: str
    target: object = None


@dataclass(frozen=True)
class Assert:              # REQ1/TURN-8
    card: str


@dataclass(frozen=True)
class Refresh:             # REQ1/TURN-9
    pass


OPTIONAL = (Whitespace, Replenish)


class IllegalMove(Exception):
    pass


# ---------------------------------------------------------------- state

@dataclass
class Player:
    chapters: Tuple[str, str, str]
    deck: List[str]
    hand: List[str]
    discard: List[str] = field(default_factory=list)
    tokens: Dict[str, int] = field(default_factory=lambda: {k: 0 for k in KINDS})
    whitespace: int = 0
    compiled: List[str] = field(default_factory=list)

    def held(self) -> int:
        return sum(self.tokens.values())


@dataclass
class Game:
    seed: int
    cards: Dict[str, Card]
    rng: random.Random
    players: List[Player]
    board: Dict[Cell, Optional[str]]
    bag: List[str]
    middle_whitespace: int
    lanes: List[List[List[Tuple[str, bool]]]]  # lanes[i][player] = [(card id, face up), ...]
    current: int = 0
    round: int = 1
    winner: Optional[int] = None
    reason: Optional[str] = None
    log: List[str] = field(default_factory=list)

    def clone(self) -> "Game":
        """A copy that shares the (immutable) cards and nothing else."""
        g = copy.copy(self)
        g.rng = random.Random()
        g.rng.setstate(self.rng.getstate())  # deepcopy of a Random costs 90% of a bot's lookahead
        g.players = [Player(p.chapters, list(p.deck), list(p.hand), list(p.discard), dict(p.tokens),
                            p.whitespace, list(p.compiled)) for p in self.players]
        g.board = dict(self.board)
        g.bag = list(self.bag)
        g.lanes = [[list(side) for side in lane] for lane in self.lanes]
        g.log = list(self.log)
        return g

    def other(self, p: Optional[int] = None) -> int:
        return 1 - (self.current if p is None else p)


def deal_chapters(rng: random.Random) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    six = rng.sample(CHAPTERS, 6)
    return tuple(six[:3]), tuple(six[3:])


def new_game(cards: Dict[str, Card], seed: int, chapters=None) -> Game:
    """REQ1/SET-1..REQ1/SET-6. `chapters` is ((p0 three), (p1 three)) or None to deal by the seed."""
    rng = random.Random(seed)
    if chapters is None:
        chapters = deal_chapters(rng)
    p0, p1 = tuple(chapters[0]), tuple(chapters[1])
    six = p0 + p1
    if len(six) != 6 or len(set(six)) != 6 or any(ch not in CHAPTERS for ch in six):
        raise ValueError(f"six distinct chapters from {CHAPTERS} are needed, not {six}")
    players = []
    for chs in (p0, p1):
        deck = [cid for ch in chs for cid in cards_of_chapter(cards, ch)]
        rng.shuffle(deck)
        hand = [deck.pop() for _ in range(HAND)]
        players.append(Player(chapters=chs, deck=deck, hand=hand))
    bag = [kind for kind, n in BAG.items() for _ in range(n)]
    rng.shuffle(bag)
    board: Dict[Cell, Optional[str]] = {cell: None for cell in SPIRAL}
    for cell in SPIRAL:
        board[cell] = bag.pop()
    players[1].whitespace = 1
    game = Game(seed=seed, cards=cards, rng=rng, players=players, board=board, bag=bag,
                middle_whitespace=WHITESPACE_TOTAL - 1,
                lanes=[[[], []] for _ in range(LANES)])
    _begin_turn(game)
    return game


# ---------------------------------------------------------------- reading the state

def lane_value(game: Game, lane: int, player: int) -> int:
    """REQ1/LANE-1."""
    total = 0
    for cid, face_up in game.lanes[lane][player]:
        total += game.cards[cid].value if face_up else 2
    return total


def lane_of(game: Game, player: int, chapter: str) -> int:
    return game.players[player].chapters.index(chapter)


def cost_for(game: Game, player: int, card: Card) -> Dict[str, int]:
    return discounted_cost(card, game.players[player].compiled)


def can_pay(player: Player, cost: Dict[str, int]) -> bool:
    return all(player.tokens.get(k, 0) >= n for k, n in cost.items())


def _line_segments() -> List[Tuple[Cell, ...]]:
    seen = set()
    out = []
    for r in range(SIZE):
        for c in range(SIZE):
            for dr, dc in DIRECTIONS:
                cells = []
                for i in range(3):
                    rr, cc = r + dr * i, c + dc * i
                    if not (0 <= rr < SIZE and 0 <= cc < SIZE):
                        break
                    cells.append((rr, cc))
                    key = tuple(sorted(cells))
                    if key not in seen:
                        seen.add(key)
                        out.append(key)
    return out


SEGMENTS = _line_segments()


def gather_moves(game: Game) -> List[Gather]:
    """REQ1/TURN-4 and REQ1/TURN-10: 1–3 adjacent, non-empty, non-Confidence cells in a line."""
    me = game.players[game.current]
    room = TOKEN_LIMIT - me.held()
    out = []
    for cells in SEGMENTS:
        if len(cells) > room:
            continue
        if all(game.board[c] is not None and game.board[c] != CONFIDENCE for c in cells):
            out.append(Gather(cells))
    return out


def ability_targets(game: Game, player: int, card: Card, room: int) -> List[object]:
    """The legal choices for a card's ability after its cost is paid; [] when it has none."""
    other = game.players[game.other(player)]
    if card.ability == "take":
        if room < 1:
            return []
        return [cell for cell in SPIRAL if game.board[cell] is not None and game.board[cell] != CONFIDENCE]
    if card.ability == "steal":
        if room < 1:
            return []
        return [k for k in KINDS if k != CONFIDENCE and other.tokens.get(k, 0) > 0]
    if card.ability == "flip":
        lane = lane_of(game, player, card.chapter)
        return [i for i, (_, face_up) in enumerate(game.lanes[lane][game.other(player)]) if not face_up]
    return []


def legal_moves(game: Game) -> List[object]:
    """Everything the current player may do now (REQ1/END-3: nothing, once the game has ended)."""
    if game.winner is not None:
        return []
    me = game.players[game.current]
    moves: List[object] = []
    if me.whitespace > 0 and me.held() < TOKEN_LIMIT:
        for cell in SPIRAL:
            if game.board[cell] is not None and game.board[cell] != CONFIDENCE:
                moves.append(Whitespace(cell))
    if game.bag and any(v is None for v in game.board.values()):
        moves.append(Replenish())  # once a turn follows: afterwards the board is full or the bag is empty
    moves.extend(gather_moves(game))
    if me.held() < TOKEN_LIMIT:
        for cell in SPIRAL:
            if game.board[cell] == CONFIDENCE:
                moves.append(TakeConfidence(cell))
    for cid in sorted(set(me.hand), key=me.hand.index):
        card = game.cards[cid]
        cost = cost_for(game, game.current, card)
        if can_pay(me, cost):
            room = TOKEN_LIMIT - (me.held() - sum(cost.values()))
            targets = ability_targets(game, game.current, card, room)
            if targets:
                moves.extend(Demonstrate(cid, t) for t in targets)
            else:
                moves.append(Demonstrate(cid))
        if me.tokens[CONFIDENCE] > 0:
            moves.append(Assert(cid))
    moves.append(Refresh())
    return moves


# ---------------------------------------------------------------- changing the state

def _draw(game: Game, player: int, n: int) -> int:
    """REQ1/TURN-12. Returns how many were drawn."""
    p = game.players[player]
    drawn = 0
    for _ in range(n):
        if not p.deck and p.discard:
            p.deck = list(p.discard)
            p.discard = []
            game.rng.shuffle(p.deck)
        if not p.deck:
            break
        p.hand.append(p.deck.pop())
        drawn += 1
    return drawn


def _gain_whitespace(game: Game, player: int) -> bool:
    """REQ1/TURN-11."""
    other = game.players[game.other(player)]
    if game.middle_whitespace > 0:
        game.middle_whitespace -= 1
    elif other.whitespace > 0:
        other.whitespace -= 1
    else:
        return False
    game.players[player].whitespace += 1
    game.log.append(f"P{player} gains a Whitespace")
    return True


def _take_from_board(game: Game, player: int, cell: Cell) -> str:
    kind = game.board[cell]
    game.board[cell] = None
    game.players[player].tokens[kind] += 1
    return kind


def _pay(game: Game, player: int, cost: Dict[str, int]) -> None:
    p = game.players[player]
    for kind, n in cost.items():
        p.tokens[kind] -= n
        game.bag.extend([kind] * n)  # REQ1/TURN-10: spent tokens return to the bag


def _play(game: Game, player: int, cid: str, face_up: bool) -> int:
    p = game.players[player]
    p.hand.remove(cid)
    lane = lane_of(game, player, game.cards[cid].chapter)
    game.lanes[lane][player].append((cid, face_up))
    return lane


def _fire(game: Game, player: int, card: Card, target: object) -> None:
    """REQ1/CARD-3, REQ1/CARD-4."""
    other = game.other(player)
    if card.ability == "draw":
        n = _draw(game, player, 2)
        game.log.append(f"P{player} draws {n}")
    elif card.ability == "whitespace":
        _gain_whitespace(game, player)
    elif card.ability == "take" and target is not None:
        kind = _take_from_board(game, player, target)
        game.log.append(f"P{player} takes a {kind} token")
    elif card.ability == "steal" and target is not None:
        game.players[other].tokens[target] -= 1
        game.players[player].tokens[target] += 1
        game.log.append(f"P{player} steals a {target} token")
    elif card.ability == "flip" and target is not None:
        lane = lane_of(game, player, card.chapter)
        cid, _ = game.lanes[lane][other].pop(target)
        game.players[other].discard.append(cid)
        game.log.append(f"P{player} reviews P{other}'s face-down card in lane {lane + 1}: {cid} is found wrong and removed")


def _end_turn(game: Game) -> None:
    game.current = game.other()
    if game.current == 0:
        game.round += 1
    _begin_turn(game)
    if game.winner is None and game.round > ROUND_LIMIT:
        _end_by_limit(game)


def _begin_turn(game: Game) -> None:
    """REQ1/LANE-2, REQ1/LANE-3, REQ1/END-1: the compile check."""
    me = game.current
    p = game.players[me]
    for lane in range(LANES):
        chapter = p.chapters[lane]
        if chapter in p.compiled:
            continue
        mine, theirs = lane_value(game, lane, me), lane_value(game, lane, game.other(me))
        if mine >= TARGET and mine > theirs:
            p.compiled.append(chapter)
            for side in (0, 1):
                game.players[side].discard.extend(cid for cid, _ in game.lanes[lane][side])
                game.lanes[lane][side] = []
            game.log.append(f"P{me} compiles chapter {chapter} in lane {lane + 1} ({mine} to {theirs})")
            if len(p.compiled) == LANES and game.winner is None:
                game.winner, game.reason = me, "all three chapters compiled"
                game.log.append(f"P{me} wins: {game.reason}")


def _end_by_limit(game: Game) -> None:
    """REQ1/END-2."""
    a, b = game.players
    ca, cb = len(a.compiled), len(b.compiled)
    va = sum(lane_value(game, i, 0) for i in range(LANES))
    vb = sum(lane_value(game, i, 1) for i in range(LANES))
    if ca != cb:
        game.winner, how = (0 if ca > cb else 1), f"more chapters compiled ({ca} to {cb})"
    elif va != vb:
        game.winner, how = (0 if va > vb else 1), f"higher total lane value ({va} to {vb})"
    else:
        game.winner, how = 1, "tie; the second player wins"
    game.reason = f"round limit of {ROUND_LIMIT} reached: {how}"
    game.log.append(f"P{game.winner} wins: {game.reason}")


def apply(game: Game, move: object, check: bool = True) -> Game:
    """The state after `move`, which must be one of `legal_moves(game)`. A caller that took the
    move from `legal_moves` itself may pass check=False and skip the second enumeration."""
    if check and move not in legal_moves(game):
        raise IllegalMove(f"{move} is not legal for P{game.current}")
    g = game.clone()
    me = g.current
    p = g.players[me]
    if isinstance(move, Whitespace):
        p.whitespace -= 1
        g.middle_whitespace += 1
        kind = _take_from_board(g, me, move.cell)
        g.log.append(f"P{me} spends a Whitespace for a {kind} token")
        return g
    if isinstance(move, Replenish):
        filled = 0
        for cell in SPIRAL:
            if g.board[cell] is None and g.bag:
                g.board[cell] = g.bag.pop()
                filled += 1
        g.log.append(f"P{me} replenishes the board ({filled} tokens)")
        _gain_whitespace(g, g.other())
        return g
    if isinstance(move, Gather):
        kinds = [_take_from_board(g, me, cell) for cell in move.cells]
        g.log.append(f"P{me} gathers {', '.join(kinds)}")
        if (len(kinds) == 3 and len(set(kinds)) == 1) or (len(kinds) == 2 and kinds == [SLACK, SLACK]):
            _gain_whitespace(g, g.other())  # REQ1/TURN-5
    elif isinstance(move, TakeConfidence):
        _take_from_board(g, me, move.cell)
        g.log.append(f"P{me} takes a Confidence token")
    elif isinstance(move, Demonstrate):
        card = g.cards[move.card]
        _pay(g, me, cost_for(g, me, card))
        lane = _play(g, me, move.card, True)
        g.log.append(f"P{me} demonstrates {card.citation} in lane {lane + 1}")
        _fire(g, me, card, move.target)
    elif isinstance(move, Assert):
        _pay(g, me, {CONFIDENCE: 1})
        lane = _play(g, me, move.card, False)
        g.log.append(f"P{me} asserts a card face-down in lane {lane + 1}")
    elif isinstance(move, Refresh):
        p.discard.extend(p.hand)
        p.hand = []
        n = _draw(g, me, HAND)
        g.log.append(f"P{me} refreshes ({n} drawn)")
    _end_turn(g)
    return g


def resign(game: Game, player: int) -> Game:
    """REQ1/CLI-4: the game ends with the other player the winner."""
    g = game.clone()
    if g.winner is None:
        g.winner, g.reason = g.other(player), f"P{player} resigned"
        g.log.append(f"P{g.winner} wins: {g.reason}")
    return g
