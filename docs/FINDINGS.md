# Findings

What we learned the expensive way: surprises, dead ends, measurements, the attack that worked. The
only document reality writes
([SE1/W10](../vendor/software-engineering/guide/08-work.md#w10)). Blameless: say what would have
found it, not who should have asked
([SE1/H12](../vendor/software-engineering/guide/09-people.md#h12)).

## 2026-10-28 — Every test seen red: 28 planted breakages, 27 caught, one unobservable rule

- **What happened:** after the suite of 59 tests passed, a script planted one breakage at a time
  in the game (a tie compiling, a face-down card worth 1, Confidence gatherable, no discount, the
  spiral from a corner, spent tokens vanishing, a flipped card lost, any number accepted at the
  prompt, the Ask dropped from the card, a wrapped Ask not joined, a guide mismatch ignored, the
  greedy bot choosing at random, draw drawing one, steal taking nothing, no win on the third
  compile, an unseeded game, an upward import, a free assert, a kept scroll, a compiled lane not
  cleared, and eight more) and ran the suite. Each of 27 turned red exactly the test written for
  its requirement, and only that test or the invariant test besides. The 28th, "replenish
  repeatable", turned nothing red.
- **Kind:** K3. The `replenished` flag and its test both read as covering "at most once per
  turn"; the test passed for another reason.
- **Cost:** twenty minutes, and a flag that would have been carried for nothing.
- **Findable by:** exactly this: a test never seen red proves nothing
  ([SE1/T3](../vendor/software-engineering/guide/06-testing.md#t3)). A replenish always leaves
  the board full or the bag empty, either of which already forbids a second one, so the flag could
  never decide anything.
- **Changed:** the flag was deleted (what can we delete?
  [SE1/D12](../vendor/software-engineering/guide/05-design.md#d12)); the test says why; QUEUE #8
  asks the client whether REQ1/TURN-3's "at most once" stays as a true-but-idle sentence.

## 2026-10-28 — REQ1/CARD-4 cannot happen under the v1 numbers

- **What happened:** writing the test for REQ1/CARD-4 (take and steal do nothing at ten tokens) showed
  that no card with those abilities is free, so paying its cost always frees a slot before the
  ability fires. The rule can never be exercised in play.
- **Kind:** K3 — the requirement was written as if the case were reachable.
- **Cost:** a requirement that cannot be tested from outside, and a guard that is tested only at
  the function level.
- **Findable by:** "what test would pass if this worked?"
  ([SE1/T8](../vendor/software-engineering/guide/06-testing.md#t8)) asked while writing the
  sentence, not after.
- **Changed:** the test says so in its docstring; QUEUE #8 asks whether to drop REQ1/CARD-4 in v2.

## 2026-10-28 — The token limit binds a quarter of the time, not rarely

- **What happened:** the design said the ten-token limit "is rarely reached". Measured over 50
  greedy-versus-greedy games, the mover started 24% of 5,416 turns at the limit.
- **Kind:** K3, written into DESIGN_v1 before any measurement.
- **Cost:** none yet; the sentence was corrected the same day.
- **Findable by:** measuring before claiming
  ([SE1/O10](../vendor/software-engineering/guide/07-operating.md#o10)); the simulation already
  existed.
- **Changed:** DESIGN_v1's decision now carries the number; QUEUE #4 puts the limit to the client
  with the measurement.

## 2026-10-28 — Measurements of the bots, 100 games each, seeds 0–99

| Match | Seat 0 wins | Seat 1 wins | Mean rounds | Ended by compile | Mean chapters compiled | Seconds |
| ----- | ----------- | ----------- | ----------- | ---------------- | ---------------------- | ------- |
| greedy v greedy | 48 | 52 | 52.7 | 88 | 4.38 | 14.6 |
| random v random | 44 | 56 | 91.1 | 32 | 2.38 | 2.2 |
| greedy v random | 82 | 18 | 63.2 | 67 | 3.12 | 7.5 |
| random v greedy | 21 | 79 | 74.8 | 47 | 2.87 | 8.0 |

- REQ1/BOT-2 (greedy beats random in more than 60%) holds at 80.5%. Seats look balanced between
  equal bots (48 to 52), so player 1's starting scroll is in the right range.
- A greedy game runs 53 rounds, about 105 turns; two people would take longer. The lane target of
  10 and the limit of 100 rounds are questions for the client (QUEUE #4).
- In 50 greedy games: 1,431 demonstrations, 328 face-down asserts, and 74 face-down cards removed
  by a review — the Confidence path is used and punished, which is the lesson intended
  ([SE1/A2](../vendor/software-engineering/guide/10-agents.md#a2)).

## 2026-10-28 — `deepcopy` of the random generator was 93% of a bot game

- **What happened:** the greedy bot's one-move lookahead copied the state with `copy.deepcopy`,
  and profiling one game showed 93% of 5.4 seconds inside copying the `random.Random` (a
  625-word state, element by element). Copying its state with `getstate`/`setstate` and the
  lists by hand made 20 games take 2.9 seconds instead of 14.0, with identical results.
- **Kind:** K2.
- **Cost:** an hour, including the profile.
- **Findable by:** measuring before optimizing
  ([SE1/O10](../vendor/software-engineering/guide/07-operating.md#o10)): the first guess was the
  move enumeration, which was 2% of the time.
- **Changed:** `Game.clone` says why it does not use `deepcopy`.

## 2026-10-28 — The doctor found 40 citations with no version

- **What happened:** the first `./se --doctor` run over the staged files reported 40 unversioned
  requirement citations: every list of IDs carried the version on its first ID and then
  dropped it from the rest, in the design, the queue, the code's docstrings, and the tests.
- **Kind:** K3 — each read as cited; a search for `REQ1/TURN-4` would have missed most of them.
- **Cost:** ten minutes with a script.
- **Findable by:** the doctor, which found it; the habit it enforces is
  [SE1/R10](../vendor/software-engineering/guide/04-requirements.md#r10).
- **Changed:** every citation is versioned; the doctor's citation row is green and stays part of
  what `./se --doctor` checks before a commit.

## 2026-10-28 — The doctor cannot reach GitHub from this session

- **What happened:** `se --doctor` tries `api.github.com` for the newest release; this session's
  proxy answers 403, so the release check reads "never checked: this copy knows only v1.3" and the
  doctor exits 1 on that row alone. The copy is in fact the newest (v1.3.1 changed no copies).
- **Kind:** K1, known and recorded.
- **Cost:** the doctor's first row is red until someone runs it with the network (QUEUE #6).
- **Findable by:** the doctor itself, which says exactly this.
- **Changed:** `check.sh` does not run the doctor (DESIGN_v1, decisions), so CI cannot go red for a
  reason outside the repository.

## 2026-10-28 — The harness refused to install the hook

- **What happened:** `./se --hook --write` and a direct write of `.claude/settings.json` were both
  refused by the agent harness as self-modification. ADOPT.md step 8 and the guide's own trials
  say a rule the agent must choose to follow is not enough; the hook is the mechanism.
- **Kind:** K2 for this repository; the guide's GAPS.md predicts the shape.
- **Cost:** the handoff hook is "none yet" until the owner runs one command (QUEUE #1).
- **Changed:** CONTRIBUTING maps "the handoff check" to that command.

## 2026-10-28 — Retro questions, answered by the agent that built v1

Asked by [SE1/A10](../vendor/software-engineering/guide/10-agents.md#a10); the answers are
proposals from something with no stake in the outcome.

- **What did you have to read that you should not have needed?** The whole of `se.py`, to learn
  what the doctor would scan and which requirement-ID prefixes the vendored templates already
  use (`UI-1`, `COL-1`), so as not to collide. Proposed home: a line in ADOPT.md's step 4 saying
  which example IDs the templates use.
- **What would have let you get this right the first time?** A sentence from the client on
  whether the learning is the card text or a quiz, and whether one win condition is enough; both
  are now the first two assumptions in REQUIREMENTS_v1.
- **What did you assume because nobody wrote it down?** That the chapters are the protocols,
  that the vendored guide is a plain copy rather than a submodule, that a text interface is the
  first slice, and every number in the rules. All are in the assumptions and marked *(invented)*.
