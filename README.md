# Splendorous

A two-player game for learning the
[software-engineering guide](vendor/software-engineering/README.md): a mash-up of *Splendor
Duel*'s token board and *Compile*'s lanes, where every card is one of the guide's hundred
principles and every move is a way of building things better. Playable in a terminal, against a
person or a bot. Python 3.9+, nothing to install.

```sh
python3 -m splendorous                 # you against the greedy bot
python3 -m splendorous --p1 human      # two people at one terminal
python3 -m splendorous --seed 7 --chapters TDR,HOA
python3 -m splendorous --p0 greedy --p1 random --simulate 100
```

## How it plays

Each player is learning **three chapters** of the guide (Purpose, Unknowing, Feedback,
Requirements, Design, Testing, Operating, Work, People, Agents). Your deck is every principle of
your three chapters; the three **lanes** each hold one chapter of yours against one of your
opponent's.

On your turn you may first spend a **Whitespace** scroll to take one token, or replenish the
board from the bag (which hands your opponent a scroll). Then you do one of:

- **Gather evidence:** take up to three adjacent tokens in a straight line from the 5×5 board.
  Evidence comes in five kinds — a **run**, a **test**, an **ask**, a **note**, a **review** —
  plus rare **Slack**. Three of a kind, or two Slack, hand your opponent a Whitespace.
- **Take Confidence:** one Confidence token from the board.
- **Demonstrate a principle:** pay a card's cost in evidence and play it face-up into its
  chapter's lane. Its value counts, and its ability fires: *draw*, *take*, *whitespace*, *flip*
  (remove one of the opponent's face-down cards in that lane), or *steal*.
- **Assert a principle:** pay one Confidence and play any card face-down. It is worth two, does
  nothing, and a review can remove it.
- **Refresh:** discard your hand and draw five.

At the start of your turn, any lane where you have **ten or more and more than your opponent**
compiles that chapter: the lane is cleared, the chapter is yours, and it discounts every later
play. **Compile all three of your chapters to win.**

The exact rules are the numbered requirements in [docs/REQUIREMENTS_v1.md](docs/REQUIREMENTS_v1.md),
which the tests cite; this page is the short version.

## What the mechanics teach

| In the game | In the guide |
| ----------- | ------------ |
| Evidence tokens: run, test, ask, note, review | what moves a belief toward known ([SE1/U2](vendor/software-engineering/guide/02-unknowing.md#u2)) |
| Confidence buys a face-down card worth less that does nothing | never let confidence substitute for a run ([SE1/A2](vendor/software-engineering/guide/10-agents.md#a2)) |
| A *review* removes a face-down card | only reality and someone who does not share your assumption find a K3 ([SE1/U3](vendor/software-engineering/guide/02-unknowing.md#u3)) |
| Slack is rare and the best cards need it | slack is the budget line for the unknown unknown ([SE1/W7](vendor/software-engineering/guide/08-work.md#w7)) |
| Whitespace scrolls | time with no agenda finds what no task does ([SE1/U8](vendor/software-engineering/guide/02-unknowing.md#u8)) |
| A compiled chapter discounts what comes after | lowering the cost of a test multiplies against every future change ([SE1/F2](vendor/software-engineering/guide/03-feedback.md#f2)) |
| Every card shows its principle's *Ask* when played | each principle ends with a question you can ask out loud |

## Where to look

- [CONTRIBUTING.md](CONTRIBUTING.md): how to run, check, and reset; the rules of this repository.
- [docs/](docs/): the working set — requirements, design, queue, findings.
- [vendor/software-engineering/](vendor/software-engineering/): the guide, release v1.3.1,
  unedited; [vendor/README.md](vendor/README.md) says how it was copied.
- [AGENTS.md](AGENTS.md): the working agreement agents follow here, copied from the guide.

## Credits and license

The principles' text is read at run time from Warren MacEvoy's
[software-engineering](https://github.com/wmacevoy/software-engineering) guide, MIT-licensed.
*Splendor Duel* (Space Cowboys) and *Compile* (Greater Than Games) are the inspirations and
their publishers' trademarks; nothing of theirs is copied. This repository is MIT-licensed
([LICENSE](LICENSE)).
