"""The card table: what the game adds to each principle (value and ability), and the cost rule.

Title and Ask come from the guide (guide.py); only the numbers live here. The table is one
agent's reading of each principle's meaning, untuned (REQUIREMENTS_v1, *Not yet answered*):

- **flip** goes to principles about someone who does not share your assumption finding the K3;
- **draw** to principles about moving a known unknown to known;
- **take** to principles about gathering evidence or writing it down;
- **whitespace** to principles about slack, deletion, and time with no agenda;
- **steal** to the two principles about an adversary.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .guide import Guide, Principle

EVIDENCE = ("run", "test", "ask", "note", "review")
SLACK = "slack"
CONFIDENCE = "confidence"
KINDS = EVIDENCE + (SLACK, CONFIDENCE)
LETTER = {"run": "R", "test": "T", "ask": "A", "note": "N", "review": "V", "slack": "S", "confidence": "C"}

# REQ1/SET-4: 25 tokens.
BAG = {"run": 4, "test": 4, "ask": 4, "note": 4, "review": 4, "slack": 2, "confidence": 3}

CHAPTERS = "PUFRDTOWHA"
# REQ1/CARD-1: each chapter's primary and secondary evidence kinds.
CHAPTER_KINDS = {
    "P": ("ask", "note"),
    "U": ("review", "run"),
    "F": ("test", "run"),
    "R": ("ask", "note"),
    "D": ("note", "review"),
    "T": ("test", "run"),
    "O": ("run", "test"),
    "W": ("note", "ask"),
    "H": ("ask", "review"),
    "A": ("review", "run"),
}

ABILITIES = ("draw", "take", "whitespace", "flip", "steal", "none")

# id -> (value, ability)
TABLE: Dict[str, Tuple[int, str]] = {
    # Purpose
    "P1": (3, "none"), "P2": (4, "flip"), "P3": (1, "draw"), "P4": (5, "whitespace"), "P5": (2, "take"),
    # Unknowing
    "U1": (1, "draw"), "U2": (3, "take"), "U3": (5, "flip"), "U4": (2, "none"), "U5": (2, "draw"),
    "U6": (3, "take"), "U7": (4, "flip"), "U8": (0, "whitespace"), "U9": (4, "none"),
    # Feedback
    "F1": (3, "none"), "F2": (4, "take"), "F3": (2, "draw"), "F4": (5, "flip"), "F5": (0, "flip"),
    # Requirements
    "R1": (3, "draw"), "R2": (4, "flip"), "R3": (2, "draw"), "R4": (1, "take"), "R5": (3, "none"),
    "R6": (5, "flip"), "R7": (4, "none"), "R8": (5, "whitespace"), "R9": (2, "take"), "R10": (1, "none"),
    "R11": (3, "draw"),
    # Design
    "D1": (4, "none"), "D2": (3, "flip"), "D3": (2, "none"), "D4": (1, "draw"), "D5": (2, "take"),
    "D6": (3, "take"), "D7": (5, "draw"), "D8": (4, "whitespace"), "D9": (5, "none"), "D10": (3, "none"),
    "D11": (1, "none"), "D12": (0, "whitespace"), "D13": (2, "flip"),
    # Testing
    "T1": (2, "draw"), "T2": (4, "flip"), "T3": (5, "flip"), "T4": (1, "none"), "T5": (3, "take"),
    "T6": (3, "take"), "T7": (2, "none"), "T8": (4, "draw"), "T9": (3, "flip"), "T10": (5, "draw"),
    "T11": (1, "none"),
    # Operating
    "O1": (2, "none"), "O2": (3, "take"), "O3": (4, "none"), "O4": (5, "flip"), "O5": (3, "none"),
    "O6": (4, "flip"), "O7": (2, "take"), "O8": (5, "steal"), "O9": (1, "draw"), "O10": (3, "take"),
    "O11": (0, "whitespace"),
    # Work
    "W1": (2, "none"), "W2": (1, "none"), "W3": (4, "draw"), "W4": (5, "none"), "W5": (3, "take"),
    "W6": (3, "draw"), "W7": (4, "whitespace"), "W8": (5, "flip"), "W9": (2, "take"), "W10": (3, "take"),
    "W11": (1, "none"), "W12": (0, "draw"),
    # People
    "H1": (3, "none"), "H2": (2, "flip"), "H3": (4, "take"), "H4": (3, "take"), "H5": (4, "draw"),
    "H6": (5, "flip"), "H7": (5, "draw"), "H8": (3, "flip"), "H9": (1, "draw"), "H10": (2, "none"),
    "H11": (0, "whitespace"), "H12": (1, "none"),
    # Agents
    "A1": (2, "none"), "A2": (5, "flip"), "A3": (3, "take"), "A4": (1, "none"), "A5": (4, "take"),
    "A6": (2, "none"), "A7": (3, "none"), "A8": (4, "draw"), "A9": (3, "draw"), "A10": (1, "take"),
    "A11": (5, "flip"),
}


class GuideMismatch(Exception):
    """The guide's principle index and the card table disagree (REQ1/GUIDE-1)."""


@dataclass(frozen=True)
class Card:
    id: str
    chapter: str
    title: str
    ask: Optional[str]
    value: int
    ability: str

    @property
    def citation(self) -> str:
        return f"SE1/{self.id}"


def base_cost(value: int, chapter: str) -> Dict[str, int]:
    """REQ1/CARD-1: the cost of a card from its value and its chapter's kinds."""
    primary, secondary = CHAPTER_KINDS[chapter]
    p, s, slack = {0: (0, 0, 0), 1: (1, 0, 0), 2: (1, 1, 0), 3: (2, 1, 0), 4: (2, 2, 0), 5: (2, 2, 1)}[value]
    cost: Dict[str, int] = {}
    if p:
        cost[primary] = p
    if s:
        cost[secondary] = cost.get(secondary, 0) + s
    if slack:
        cost[SLACK] = slack
    return cost


def discounted_cost(card: Card, compiled_chapters) -> Dict[str, int]:
    """REQ1/CARD-2: one less of the primary kind per compiled chapter, never below zero."""
    cost = base_cost(card.value, card.chapter)
    for ch in compiled_chapters:
        primary = CHAPTER_KINDS[ch][0]
        if cost.get(primary, 0) > 0:
            cost[primary] -= 1
            if cost[primary] == 0:
                del cost[primary]
    return cost


def build_cards(guide: Guide) -> Dict[str, Card]:
    """One card per principle; refuses on any mismatch with the table, naming the IDs."""
    ids = {p.id for p in guide.principles}
    missing = sorted(ids - set(TABLE))
    extra = sorted(set(TABLE) - ids)
    if missing or extra:
        raise GuideMismatch(f"in the guide but not the table: {missing}; in the table but not the guide: {extra}")
    cards = {}
    for p in guide.principles:
        value, ability = TABLE[p.id]
        cards[p.id] = Card(p.id, p.chapter, p.title, p.ask, value, ability)
    return cards


def cards_of_chapter(cards: Dict[str, Card], chapter: str) -> List[str]:
    return [c.id for c in cards.values() if c.chapter == chapter]
