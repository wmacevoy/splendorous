# Requirements — v1

What must be observably true of Splendorous, and what is not being built. Changes only with the
client; a change is a new version (`REQUIREMENTS_v2.md`), never an edit to this one. See
[SE1/R1–R11](../vendor/software-engineering/guide/04-requirements.md).

Client (the one voice who can decide): Warren MacEvoy. The proxy for the users, who are players
and students never in the room ([SE1/H5](../vendor/software-engineering/guide/09-people.md#h5)):
the issue tracker, and the bots, whose games are the only play this version has seen. Date sent:
2026-10-28 · *Tell us what is wrong with it.*

This is the first draft, written by an agent from one sentence of the client's (*a mash-up of
Splendor Duel and Compile where the moves are to learn how to build things better according to
the software-engineering guide*). Every number in it is *(invented)*; every rule is a guess the
client has not yet objected to ([SE1/R2](../vendor/software-engineering/guide/04-requirements.md#r2)).
The assumptions at the end are the read-back.

## Glossary

One thing, one word ([SE1/D9](../vendor/software-engineering/guide/05-design.md#d9)).

| Term | Meaning |
| ---- | ------- |
| Guide | The vendored copy of `wmacevoy/software-engineering`, release v1.3.1, in `vendor/`. |
| Principle | One numbered idea in the guide, cited as `SE1/T3`. There is one card per principle. |
| Chapter | One of the guide's ten chapters (P, U, F, R, D, T, O, W, H, A). Each player is learning three. |
| Card | A principle card: its chapter, ID, title, *Ask* line, value (0–5), cost, and ability. |
| Evidence | A token of one of five kinds: **run**, **test**, **ask**, **note**, **review** — what moves a belief toward K0 ([SE1/U2](../vendor/software-engineering/guide/02-unknowing.md#u2)). |
| Slack | The sixth token kind, rare, needed for the most valuable cards; nothing substitutes for it. |
| Confidence | The seventh token kind. It buys a face-down play: a claim, not a demonstration. |
| Token | Any of the seven kinds above. There are 25. |
| Board | The 5×5 grid tokens are taken from. |
| Bag | The tokens that are neither on the board nor held by a player. |
| Whitespace | One of three scrolls; spending one takes one token from the board. |
| Lane | One of three. Each holds one chapter of each player and the cards they have played there. |
| Face-up | A card played by paying its cost in evidence: its value counts and its ability fires. |
| Face-down | A card played by paying one Confidence: worth 2, no ability, and a review can remove it. |
| Compile | What happens to a chapter when its lane reaches ten: it is learned, and the lane is cleared. |
| Deck, hand, discard | Each player's own: the cards of their chapters, the cards they hold, the cards used up. |
| Turn, round | One player's turn; a round is one turn each. |
| Bot | A program that chooses a legal move for a seat. |
| Seat | Player 0 (moves first) or player 1. |

## The pain

A reader of the guide can recite a principle and still not reach for it under pressure: the
guide's own trials found agents that wrote a rule into their notes and left it out of their work
([SE1/A11](../vendor/software-engineering/guide/10-agents.md#a11)). The pain is that reading is
not practice. A game makes the principles into moves that cost something, pay off, and can be
lost, so that "a test never seen red proves nothing" is felt before it is believed. Who gets the
call today: the instructor, in week nine, when the project has a schema and no `Non-goals`.

## People this touches

- Two players at one terminal, or one player against a bot: students and engineers learning the
  guide.
- The instructor, who wants the mechanics to teach the right lesson and nothing false.
- The guide's author, whose text is read at run time and whose license must be kept.
- The publishers of *Splendor Duel* (Space Cowboys) and *Compile* (Greater Than Games), whose
  games inspired the mechanics and whose names are their trademarks.
- Nobody else: the game keeps no record about anyone.

## Requirements

Numbered, observable, with numbers. Cite them as `REQ1/SET-1` in tests, commits, and the queue
([SE1/R10](../vendor/software-engineering/guide/04-requirements.md#r10)). This document never
lists its tests ([SE1/R11](../vendor/software-engineering/guide/04-requirements.md#r11)).

**Setup**

- **SET-1** *(since v1)* A game is determined by a seed and the chapters chosen: the same seed and
  chapters give the same setup, and the same sequence of moves gives the same game, on any
  machine.
- **SET-2** *(since v1)* Each player has three distinct chapters and the six are distinct; they are
  given by the players or dealt from the ten by the seed.
- **SET-3** *(since v1)* A player's deck is every card of their three chapters, shuffled by the
  seed; each player starts with five cards in hand.
- **SET-4** *(since v1)* The bag holds 25 tokens *(invented)*: four of each evidence kind, two
  Slack, three Confidence. The board is filled from the shuffled bag in a spiral from the center
  outward, so a full board holds all 25.
- **SET-5** *(since v1)* There are three Whitespace scrolls *(invented)*: player 1 starts holding
  one; two start in the middle.
- **SET-6** *(since v1)* Lane *i* holds player 0's *i*-th chapter and player 1's *i*-th chapter.

**A turn**

- **TURN-1** *(since v1)* Players alternate, player 0 first. A turn is: the compile check
  (LANE-2), then any number of optional actions, then exactly one main action, which ends the
  turn.
- **TURN-2** *(since v1)* Optional: spend one Whitespace to take one token that is not Confidence
  from the board. Repeatable while scrolls are held.
- **TURN-3** *(since v1)* Optional, at most once per turn, only while the bag is not empty:
  replenish — empty cells are filled from the bag in spiral order until the board is full or the
  bag is empty, and the opponent gains one Whitespace (TURN-11).
- **TURN-4** *(since v1)* Main action *gather*: take one, two, or three tokens from cells that are
  adjacent in one straight line (a row, a column, or a diagonal), with no empty cell between
  them and no Confidence among them.
- **TURN-5** *(since v1)* Gathering three tokens of one evidence kind, or two Slack, gives the
  opponent one Whitespace (TURN-11).
- **TURN-6** *(since v1)* Main action *take confidence*: take one Confidence token from the board.
- **TURN-7** *(since v1)* Main action *demonstrate*: play a card from hand face-up into the lane
  of its chapter, paying its cost (CARD-1, CARD-2) in tokens; its ability then fires (CARD-3).
- **TURN-8** *(since v1)* Main action *assert*: play any card from hand face-down into the lane of
  its chapter, paying one Confidence. The card's identity is not shown to the opponent.
- **TURN-9** *(since v1)* Main action *refresh*: discard the whole hand and draw five.
- **TURN-10** *(since v1)* A player holds at most ten tokens *(invented)*; an action that would
  exceed ten is not offered. Tokens spent return to the bag.
- **TURN-11** *(since v1)* When a player gains a Whitespace, it comes from the middle; if the middle
  is empty, from the other player; if that player holds none, nothing happens.
- **TURN-12** *(since v1)* A draw from an empty deck first shuffles that player's discard pile into
  the deck (by the seed); if both are empty, nothing is drawn.

**Cards**

- **CARD-1** *(since v1)* A card's cost follows from its value and its chapter's two evidence
  kinds, *primary* and *secondary* (DESIGN_v1 lists them): value 0 costs nothing; 1 costs one
  primary; 2 costs one primary and one secondary; 3 costs two and one; 4 costs two and two; 5
  costs two, two, and one Slack.
- **CARD-2** *(since v1)* Each compiled chapter a player holds lowers the primary-kind part of the
  cost of every later face-up play by one, never below zero; Slack is never discounted.
- **CARD-3** *(since v1)* An ability fires once, when its card is played face-up, and is one of:
  **draw** (draw two cards); **take** (take one non-Confidence token of the player's choice from
  the board); **whitespace** (gain one, TURN-11); **flip** (remove one face-down card of the
  player's choice from the opponent's side of that lane to the opponent's discard); **steal**
  (take one non-Confidence token of the player's choice from the opponent); or none. An ability
  with no legal target does nothing.
- **CARD-4** *(since v1)* The token limit (TURN-10) holds for *take* and *steal*: at ten tokens
  the ability does nothing.

**Lanes**

- **LANE-1** *(since v1)* A player's value in a lane is the sum of their face-up cards' values plus
  two per face-down card.
- **LANE-2** *(since v1)* At the start of a player's turn, every lane in which that player's value
  is at least ten *(invented)* and greater than the opponent's compiles that player's chapter in
  the lane, if it was not compiled already: every card in the lane, both sides, goes to its
  owner's discard pile.
- **LANE-3** *(since v1)* A compiled chapter stays compiled. Cards may still be played into its
  lane, and they count toward LANE-2 for the opponent, but the chapter does not compile again.

**The end**

- **END-1** *(since v1)* A player whose three chapters are all compiled wins at that moment.
- **END-2** *(since v1)* If 100 rounds *(invented)* pass with no winner, the game ends and the
  winner is the player with more compiled chapters; if equal, the higher total value across the
  three lanes; if still equal, player 1, who moved second.
- **END-3** *(since v1)* An ended game names its winner and the reason, and offers no legal move.

**The guide's text**

- **GUIDE-1** *(since v1)* The cards are exactly the principles in the guide's principle index
  (100 at v1.3.1): one card per ID, no card without one. The game refuses to start on a mismatch
  and names the IDs that differ.
- **GUIDE-2** *(since v1)* A card shows its principle's versioned ID (`SE1/T3`), the title, and the
  *Ask* line where the guide has one; a face-up play prints all three in the interface.
- **GUIDE-3** *(since v1)* Changing a principle's title or *Ask* line in the vendored guide changes
  the card, with no change to the game's code.

**The interface**

- **CLI-1** *(since v1)* `python3 -m splendorous` plays a game in the terminal: it shows the
  board, each player's tokens, the lanes, and the current player's hand, then lists the legal
  moves numbered from 1, and the player chooses by number.
- **CLI-2** *(since v1)* Each seat is a person, the greedy bot, or the random bot, chosen with
  `--p0` and `--p1`; the default is a person at seat 0 against the greedy bot.
- **CLI-3** *(since v1)* `--seed N` fixes the game (SET-1); `--chapters` names the six chapters as
  letters, player 0's three then player 1's (`--chapters TDR,HOA`).
- **CLI-4** *(since v1)* A move prompt handles its input's four failures: *absent* (end of input)
  ends the game as a resignation by the prompted player; *wrong* (not a number, or not in the
  list) is refused with the list shown again; *late* has no answer, since nothing times out; and
  *lying* cannot happen, because only a listed number is accepted.
- **CLI-5** *(since v1)* `--simulate N` plays N games between the chosen bots and prints, per
  seat, the wins; the mean rounds; how many games ended by END-1 and by END-2; and the mean
  chapters compiled per game. 100 games finish in under 60 seconds *(invented)* on an ordinary
  laptop.

**The bots**

- **BOT-1** *(since v1)* Any bot, given a state, returns one of that state's legal moves; a single
  conformance check holds for every bot ([SE1/T6](../vendor/software-engineering/guide/06-testing.md#t6)).
- **BOT-2** *(since v1)* The greedy bot wins more than 60% *(invented)* of 100 games against the
  random bot, 50 from each seat, with seeds 0–99.

## Inputs: absent, late, wrong, lying

| Input | Absent | Late | Wrong | Lying |
| ----- | ------ | ---- | ----- | ----- |
| The vendored guide | the game refuses to start, naming the path (GUIDE-1) | n/a: a file | a principle index that the card table does not match: refuse, naming the IDs (GUIDE-1) | a principle with no *Ask* line: the title stands (GUIDE-2) |
| A move from a person | resignation (CLI-4) | no timeout (CLI-4) | refused, list shown again (CLI-4) | impossible: only listed numbers are accepted (CLI-4) |
| A move from a bot | n/a: a function call | n/a | an illegal move is an error that stops the game, naming the bot (BOT-1) | same as wrong |
| The seed | a seed is drawn from the system and printed, so the game can be replayed | n/a | a non-integer is refused by the argument parser | n/a |
| `--chapters` | dealt by the seed (SET-2) | n/a | an unknown letter, a repeat, or not six: refused with the ten letters listed | n/a |

## Operating envelope

- **Scale:** two players, 100 cards, 25 tokens, three lanes; a game of at most 100 rounds. Not
  designed for more players, more cards, or a larger board.
- **Speed:** a bot game ends in under one second *(invented)*; a person's move is shown in under
  100 ms *(invented)*.
- **Recovery:** there is nothing to recover. The game holds no state outside the running process;
  closing the terminal loses the game, and that is accepted (Non-goals).
- **Availability:** not applicable; it runs on the player's machine.
- **Resources:** Python 3.9 or newer, the standard library only, under 10 MB of memory *(invented)*.
- **Interruption:** nothing is written to disk, so an interrupt at any instant leaves nothing
  torn.

## Security, law, and ethics

- **Threat model:** none worth the name. The program reads the vendored guide and the terminal
  and writes the terminal. It opens no network connection and no file for writing.
- **Data about people:** none is collected, kept, or shown.
- **Law:** the guide's text is MIT-licensed and its license file is vendored with it; the card
  text is read from that copy and attributed to it. *Splendor Duel* and *Compile* are trademarks of
  their publishers; this game names them only as inspiration, copies none of their text or art,
  and is not sold. Mechanics are not copyrightable; names are protected, so the product name is
  Splendorous and nothing else.
- **Ethics:** the lesson the mechanics teach must be the guide's lesson, not a flattering version
  of it; a mechanic that teaches something the guide calls wrong is a defect, not a feature.

## Assumptions (K4s), read back to the client

- "We're assuming the learning is in reading the card when it is played — the title and the Ask
  line — and not in a quiz. True?" — *not yet answered*
- "We're assuming one win condition (compile all three chapters) is enough, and Splendor Duel's
  three ways to win are not wanted. True?" — *not yet answered*
- "We're assuming a text interface is the right first slice, and a browser page can wait. True?"
  — *not yet answered*
- "We're assuming the chapters are the protocols: a player learns three of the ten, and the six
  in play are distinct. True?" — *not yet answered*
- "We're assuming Confidence should be a real but worse way to progress — two points, no
  ability, removable — rather than a trap that is never worth taking. True?" — *not yet answered*
- "We're assuming the guide is vendored as an unedited copy at a release, re-copied by hand, and
  not a git submodule. True?" — *not yet answered*

## Scope decisions

- **Python, standard library only** — nothing to install, one interpreter to pin, and the guide's
  own tool is Python; a dependency is a permanent obligation
  ([SE1/D12](../vendor/software-engineering/guide/05-design.md#d12)).
- **Card text is derived from the vendored guide at run time, not stored** — one authority; a
  re-vendor updates every card ([SE1/D6](../vendor/software-engineering/guide/05-design.md#d6)).
- **Costs follow one rule from value and chapter (CARD-1)** — uniform, so the one odd card would
  be a signal; per-card tuning is deferred.
- **Confidence buys a face-down card** — the guide's lesson is that confidence is not a run
  ([SE1/A2](../vendor/software-engineering/guide/10-agents.md#a2)); a face-down card is worth
  less, does nothing, and a review removes it.
- **A removed face-down card is discarded, not revealed** — the simplest rule that says "the
  claim was found wrong"; a demonstrate-or-lose rule is deferred.
- **The token limit refuses rather than discards** — fewer choices to enumerate; the limit is
  rarely reached.
- **Refresh discards the whole hand** — one move, no subset to choose; it exists so that a player
  with nothing to play is never stuck.
- **Lanes are shared, as in Compile** — compiling clears both sides, so the opponent's play in a
  lane matters.

## Non-goals

- *Not building* online or networked play — two people share one terminal, or one plays a bot.
- *Not building* saved games — a game is minutes long and holds nothing worth keeping.
- *Not building* graphics or a browser page in this version — the text interface is the slice.
- *Not building* more than two players — both source games are for two.
- *Not building* Compile's *control* component or Splendor Duel's *reserve* action, royal cards,
  or three win conditions — each is a mechanic that would need a principle to justify it.
- *Not building* a quiz, scoring of answers, or any record of what a player learned.
- *Not building* a bot stronger than one-move greedy — it is a sparring partner, not an opponent.

## Not yet answered

- Should chapters be chosen by draft rather than dealt? — the client, after the first play.
- Is ten the right lane target, and 100 the right round limit? — measured by the bots; decided by
  the client.
- Which abilities should which principles carry? — the current table is one agent's reading of
  the principles' meaning; the client, or a student, may disagree per card.

## Deferred

- *Not yet:* per-card cost tuning — after play reveals which cards are never bought.
- *Not yet:* a browser interface — after the rules settle; the engine is pure so a second
  interface is only a second thin edge.
- *Not yet:* a *demonstrate-or-lose* rule for a flipped face-down card (pay the cost now to keep
  it) — if removal proves too harsh in play.
- *Not yet:* Compile's *control* — if the game proves to need a second axis of interaction.
