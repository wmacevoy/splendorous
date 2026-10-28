# Contributing

How to work on this repository — for a new teammate and for an agent, who both arrive knowing
nothing ([SE1/A3](vendor/software-engineering/guide/10-agents.md#a3)). Keep it short and true: a
change that makes a line here untrue updates it in the same change
([SE1/W11](vendor/software-engineering/guide/08-work.md#w11)). This is the repository guide that
[SE1/W10](vendor/software-engineering/guide/08-work.md#w10) asks for; it wins over `AGENTS.md`
where they disagree.

## Run it

- **Prerequisites:** Python 3.9 or newer, standard library only. Nothing to install; there is no
  install step and no build. `git` for the history.
- **Build:** none. Run from the checkout.
- **Run:** `python3 -m splendorous` — you (seat 0) against the greedy bot. You should see the seed,
  the two players' chapters, the board, and a numbered list of moves. `python3 -m splendorous
  --help` lists the seats, `--seed`, `--chapters TDR,HOA`, and `--simulate N`.
- **Reset to a known state:** nothing to reset — the game writes no file. `git checkout -- . &&
  git clean -fdx` returns the checkout itself to clean (it removes `__pycache__` and nothing
  else) ([SE1/T5](vendor/software-engineering/guide/06-testing.md#t5)).
- **Is the repository sound:** `./se --doctor` (or `python3 se.py --doctor --offline` without the
  network); `./se --post` is the session's self test.

## Check it

- **The full check:** `sh check.sh` — the same script CI runs on Linux, macOS, and Windows with
  Python 3.9 and the newest ([SE1/O3](vendor/software-engineering/guide/07-operating.md#o3)). It
  byte-compiles the package and the tests, then runs every test in `tests/`.
- **Success prints:** `check: OK` as the last line (unittest's own `OK` comes just before it).
  It takes about 10 seconds; the strength test (REQ1/BOT-2) plays 100 bot games.
- **Instruments, and how each was seen to fire**
  ([SE1/T3](vendor/software-engineering/guide/06-testing.md#t3)): the suite, on 28 planted
  breakages, one at a time, each recorded in `docs/FINDINGS.md` with the tests it turned red;
  `tests/test_layers.py`, on a planted upward import. There is no coverage tool, linter, or type
  checker: adding one is a dependency and so a proposal.

## Rules for this repository

- **Requirements are versioned, never edited in place.** A change to a rule is
  `docs/REQUIREMENTS_v2.md`. Cite with the version that last changed the requirement:
  `REQ1/LANE-2`, never the ID alone
  ([SE1/R10](vendor/software-engineering/guide/04-requirements.md#r10)).
- **Every test names its requirement in its docstring** (`REQ1/TURN-4: ...`) and has been seen
  red; `./se --doctor` reports any requirement no test names.
- **`vendor/` is never edited.** Re-vendor from a release and update `vendor/README.md`
  (which says how). The card text comes from there at run time.
- **The engine does no I/O.** Clocks, randomness, and the terminal stay in `cli.py` and the seeded
  generator inside the state ([SE1/D7](vendor/software-engineering/guide/05-design.md#d7)). The
  layer order in `docs/DESIGN_v1.md` is enforced by `tests/test_layers.py`.
- **Standard library only.** A dependency is a proposal, not a change
  ([SE1/D12](vendor/software-engineering/guide/05-design.md#d12)).
- **Commits:** one concern per commit, naming the versioned requirement ID or saying *chore*. An
  agent commits or pushes only when asked; the trailer credits it, the author signs
  ([SE1/A7](vendor/software-engineering/guide/10-agents.md#a7)).
- **No code from the two source games.** Mechanics are inspired by *Splendor Duel* and *Compile*;
  no text, art, or component list of theirs is copied, and their names appear only as
  inspiration (REQUIREMENTS_v1, *Security, law, and ethics*).

## Where things are

- **The game:** `splendorous/` — `guide.py` (reads the vendored guide), `cards.py` (the
  value/ability table and the cost rule), `engine.py` (the rules), `bots.py`, `cli.py`.
- **Tests:** `tests/`, one file per module plus `test_layers.py`; `support.py` holds the helpers.
- **Working set:** `docs/` — `REQUIREMENTS_v1`, `DESIGN_v1`, `QUEUE`, `FINDINGS`
  ([SE1/W10](vendor/software-engineering/guide/08-work.md#w10)).
- **The guide:** `vendor/software-engineering/` (release v1.3.1, unedited; provenance in
  `vendor/README.md`). `AGENTS.md`, `se`, `se.py`, `se.ps1` at the root are copies from it.
- **Agents:** `CLAUDE.md` imports `AGENTS.md` at every start; read it, then this file, before
  acting.

## The words AGENTS.md uses, here

| AGENTS.md says | In this repository |
| -------------- | ------------------ |
| the repository guide | `CONTRIBUTING.md` (this file) |
| the queue | `docs/QUEUE.md` |
| findings | `docs/FINDINGS.md` |
| the check command | `sh check.sh`; success prints `check: OK` |
| the handoff check | none yet: `./se --hook --write` installs `se --post` as a SessionStart hook (QUEUE #1) |
| `Non-goals`, `Scope decisions` | sections of `docs/REQUIREMENTS_v1.md` |
| the client | Warren MacEvoy; the proxy for the players is the issue tracker and the bots |
