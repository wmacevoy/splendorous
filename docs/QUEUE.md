# Queue

What is being worked, in what order, by whom, and what would make it done. The shared cursor
([SE1/W10](../vendor/software-engineering/guide/08-work.md#w10)). Nothing enters without a *done*
sentence that can be checked from outside. An item that contradicts the requirements is a question
for the client, not a task; mark it blocked, and say on what. An agent may move an item to
*review*; only a human marks it *done*.

| # | Item | Versioned requirement IDs (or *chore*) | Owner | Done when | Estimate (number / range / time box) | Status | Since |
| - | ---- | ---------------------------- | ----- | --------- | ------------------------------------ | ------ | ----- |
| 1 | **Install the session-start hook.** `./se --hook --write` adds `se --post` to `.claude/settings.json`; the harness that built v1 refused to write that file. | chore | owner | `./se --doctor` reports the handoff hook as configured; a fresh session's context shows the self test's report. | number: 5 minutes | done: the owner ran it and confirmed in session, 2026-10-28 | 2026-10-28 |
| 2 | **Read the requirements back.** The client reads `REQUIREMENTS_v1` and the six assumptions at its end, and objects to at least one sentence. | REQ1 (all) | client | at least one objection is recorded, and the answers to the assumptions are written beside them; if a rule changes, `REQUIREMENTS_v2`. | time box: 1 hour | ready | 2026-10-28 |
| 3 | **Play two human games** and write down every "huh" verbatim; set a fault in front of the client: assert a card face-down and have it reviewed. | REQ1/TURN-8, REQ1/CARD-3 | owner + one player | a FINDINGS entry with the verbatim list and the costed options, within the week. | time box: 2 evenings | ready | 2026-10-28 |
| 4 | **Decide the numbers from the measurements:** the lane target of 10, the round limit of 100, and the token limit of 10 (which binds on 24% of greedy turns, not rarely). | REQ1/LANE-2, REQ1/END-2, REQ1/TURN-10 | client | each number is confirmed or changed in `REQUIREMENTS_v2`, with the measurement that decided it. | time box: 30 minutes after #3 | blocked: on #2 and #3 | 2026-10-28 |
| 5 | **Review the ability and value table** (`cards.TABLE`) principle by principle; the current table is one agent's reading. | REQ1/CARD-3 | client or a student | every card's ability has a one-line reason the client accepts, or is changed; a test still proves every ID has a card. | range: 1–3 hours | ready | 2026-10-28 |
| 6 | **Run the doctor with the network once** so its release check has a cache; this session's proxy refused `api.github.com`. | chore | owner | `./se --doctor` reports `release check made`. | number: 1 minute | ready | 2026-10-28 |
| 7 | **Watch CI go green on all six runners** after the first push; Windows and macOS have not run the check yet. | chore | owner | the `check` workflow is green on ubuntu, macos, and windows with Python 3.9 and 3.x. | number: 10 minutes | done: run 40780587811 green on all six, confirmed by the owner, 2026-10-28 | 2026-10-28 |
| 8 | **Decide what to do with REQ1/TURN-3's "at most once" and REQ1/CARD-4**, both of which cannot be observed under the v1 numbers (FINDINGS). | REQ1/TURN-3, REQ1/CARD-4 | client | kept as stated with a note, or removed in `REQUIREMENTS_v2`. | number: 10 minutes | blocked: on #2 | 2026-10-28 |
| 9 | **A browser interface**, as a second thin edge over the same engine. | REQ1 Deferred | — | not before #2–#4; a new requirement in `REQUIREMENTS_v2` with its own done sentence. | time box: 2 days | blocked: on #4 | 2026-10-28 |
