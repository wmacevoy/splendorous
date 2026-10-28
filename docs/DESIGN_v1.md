# Design — v1

How we intend to satisfy [REQUIREMENTS_v1](REQUIREMENTS_v1.md), and what we rejected. Every
mechanism here should be replaceable without renegotiating a requirement
([SE1/R5](../vendor/software-engineering/guide/04-requirements.md#r5)). Written 2026-10-28 with
the first version of the code; every decision's source is this session's chat with the client
unless marked otherwise.

## Components and the dependency rule

| Component | Layer | Kind | Contract (one line) | Holds state? |
| --------- | ----- | ---- | ------------------- | ------------ |
| `splendorous/guide.py` | 0 | parser | Markdown of the vendored guide in; `Guide` (principles with id, chapter, title, Ask) out; `GuideError` if the guide is absent or misshapen. | no |
| `splendorous/cards.py` | 1 | table + rule | the value/ability table; `base_cost`, `discounted_cost` (REQ1/CARD-1, REQ1/CARD-2); `build_cards` refuses a guide the table does not match (REQ1/GUIDE-1). | no |
| `splendorous/engine.py` | 2 | rules | `new_game(cards, seed, chapters)`, `legal_moves(game)`, `apply(game, move)`, `resign`. Pure over `Game`; `apply` raises `IllegalMove` for a move not in `legal_moves`. | no (the `Game` value is passed in and a new one returned) |
| `splendorous/bots.py` | 3 | players | `bot(game, rng) -> move`, one of `legal_moves(game)` (REQ1/BOT-1). | no |
| `splendorous/cli.py` | 4 | edge | `render`, `describe`, `choose`, `play`, `simulate` are functions of state and an injected reader/writer; `main` binds the terminal. The only module that does I/O. | no |
| `vendor/software-engineering/` | — | data | the guide at v1.3.1, unedited; the authority for every card's text. | — |

A component may import only from strictly lower layers; `tests/test_layers.py` enforces it by
reading the imports ([SE1/D10](../vendor/software-engineering/guide/05-design.md#d10)).

## State

The whole game is one value, `Game`, built by `new_game` and replaced by `apply`
([SE1/D1](../vendor/software-engineering/guide/05-design.md#d1)). Nothing is cached, nothing is
written to disk, and the only clock is the round counter.

| State | Owner (authoritative) | Copies | Max staleness | While wrong, the user sees |
| ----- | --------------------- | ------ | ------------- | -------------------------- |
| `Game` (board, bag, players, lanes, scrolls, round, winner, log) | the value returned by the last `apply` | the previous values a bot's lookahead made, discarded at once | none: every render is from the current value | n/a |
| The random generator | `Game.rng`, seeded once (REQ1/SET-1) | copied with the state | none | a replay that diverges |
| Card text (title, Ask) | the vendored guide's Markdown | `Card` values built at start-up | the length of one run | a card that says what an older guide said |
| Lane values | derived every time from the cards in the lane (REQ1/LANE-1) | none: never stored | — | — |
| The 25 tokens, 3 scrolls, and every card | the bag, board, and players together | none | — | — (an invariant test checks the counts stay 25, 3, and all) |

## Essential complexity

Each line traces to a requirement; anything in the code that is not here must say why it exists
([SE1/D8](../vendor/software-engineering/guide/05-design.md#d8)).

1. Tokens are taken from a grid in straight adjacent lines, and the grid refills from a bag
   (REQ1/TURN-3, REQ1/TURN-4).
2. Two ways to play a card: pay evidence and get the value and the ability, or pay Confidence
   and get two and nothing (REQ1/TURN-7, REQ1/TURN-8).
3. A card's cost is a function of its value and chapter, discounted by compiled chapters
   (REQ1/CARD-1, REQ1/CARD-2).
4. Five abilities, each a choice the player makes, enumerated as part of the move so that a bot
   and a person choose the same way (REQ1/CARD-3).
5. Lanes compile at ten and more than the opponent, at the start of the turn, clearing both sides
   (REQ1/LANE-2).
6. Whitespace scrolls move between the middle and the players by one rule (REQ1/TURN-11).
7. A deck recycles its discard when empty (REQ1/TURN-12).
8. The game ends by three compiles or by a round limit with tie-breaks (REQ1/END-1, REQ1/END-2).
9. The cards' text is the guide's, read at start-up and checked against the table
   (REQ1/GUIDE-1..3).
10. A seed determines everything random (REQ1/SET-1).

## The card table

**Chapter kinds** (REQ1/CARD-1): the primary kind is the evidence the chapter is mostly about,
the secondary the next.

| Chapter | Primary | Secondary | Why |
| ------- | ------- | --------- | --- |
| P Purpose | ask | note | a purpose is agreed with people and written down |
| U Unknowing | review | run | only reality and another person find a K3 ([SE1/U3](../vendor/software-engineering/guide/02-unknowing.md#u3)) |
| F Feedback | test | run | the cheap loops |
| R Requirements | ask | note | asked of the client, then numbered |
| D Design | note | review | written, then held by someone who says no |
| T Testing | test | run | a test seen red |
| O Operating | run | test | the thing running where its users are |
| W Work | note | ask | the working set, and the demo |
| H People | ask | review | the first conversation, and review by another |
| A Agents | review | run | never let confidence substitute for a run ([SE1/A2](../vendor/software-engineering/guide/10-agents.md#a2)) |

**Abilities** (REQ1/CARD-3) are assigned per principle in `cards.py` by one reading of its meaning:
*flip* where the principle is about someone who does not share your assumption finding the K3;
*draw* where it is about turning a known unknown into known; *take* where it is about gathering
or recording evidence; *whitespace* where it is about slack, deletion, or time with no agenda;
*steal* for the two principles about an adversary (SE1/O8, and SE1/R6's "the unknown that
optimizes" is folded into O8). Values 0–5 spread each chapter roughly like a Compile protocol.
The table is untuned *(invented)* and is a question for the client (REQUIREMENTS_v1, *Not yet
answered*).

## One-way doors

- **Requirement IDs and their version** (`REQ1/SET-1`): cited by every test and commit. Reviewed
  by the client when the requirements are read back; until then the only reader was the agent
  that wrote them.
- **The vendored release** (v1.3.1): the card text depends on it. Changing it is a re-vendor with
  a line in `vendor/README.md`, never an edit inside the copy.
- Nothing else: no schema, no file format, no published interface. The move classes are internal.

## Decisions

- **Pure engine, thin edge** — REQ1/SET-1, REQ1/CLI-1 — so the rules are tested with values and the
  interface with a scripted reader; a browser page later is a second edge, not a second engine —
  rejected: a game loop that prints as it goes (SE1/D7, SE1/T7).
- **Moves carry their choices** (`Demonstrate(card, target)`) — REQ1/CARD-3 — so `legal_moves`
  enumerates every option and a bot, a test, and a person all choose from the same list; `apply`
  validates by membership — rejected: a callback for the player's choice inside `apply`, which
  would put I/O in the rules.
- **The state is copied, never mutated in place** — REQ1/SET-1, REQ1/BOT-1 — so a bot's lookahead and
  a test's setup cannot leak; the copy avoids `deepcopy`, which was 93% of a bot game's time
  (measured 2026-10-28; see FINDINGS) — rejected: an undo log.
- **The random generator lives in the state** — REQ1/SET-1 — a replay is the same seed and the
  same moves; tests choose seeds — rejected: a module-level generator (global state, SE1/T5).
- **Card text parsed from Markdown at start-up** — REQ1/GUIDE-1..3 — one authority; the guide's
  index and heading format are stable within SE1 — rejected: a generated `cards_text.py` (a copy
  that goes stale) and a submodule (needs the network to clone, and the game must run offline).
- **The cost rule is uniform** — REQ1/CARD-1 — so only values and abilities are hand-written;
  per-card costs are deferred until play shows a need.
- **The round limit is a tie-break, not a draw** — REQ1/END-2 — bots that never compile must
  still produce a result the simulation can count.
- **The token limit refuses moves instead of forcing a discard** — REQ1/TURN-10 — one fewer
  choice to enumerate. It was expected to bind rarely; measured, the greedy bot starts 24% of
  its turns at the limit (FINDINGS, 2026-10-28), so the rule shapes play more than planned and
  is a question for the client.
- **`check.sh` does not run `se --doctor`** — chore — the doctor's release check needs the GitHub
  API, which CI runners may be rate-limited on and this session's proxy refused; a check that
  fails for reasons outside the repository trains people to ignore red (SE1/T4). The doctor is a
  command in CONTRIBUTING, run by a person.

## Deferred

Named so they are not mistaken for oversights
([SE1/R9](../vendor/software-engineering/guide/04-requirements.md#r9)).

- *Not yet:* a browser interface — after the client has played the terminal version; the engine
  needs no change.
- *Not yet:* per-card cost tuning and ability review — after a few human games; the data is
  `cards.TABLE`.
- *Not yet:* a two-ply or search-based bot — if the greedy one is too weak to teach anything.
- *Not yet:* a session-start hook (`./se --hook --write`) — the harness this was built in refused
  to write `.claude/settings.json`; one command for the owner (QUEUE #1).
