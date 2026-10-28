# Vendored sources

Copies of other projects kept in this repository so that the game can be built, run, and read
without the network. Each copy is unedited; a change to one is made upstream and re-vendored, never
here, so the copy can always be diffed against its source
([SE1/U7](software-engineering/guide/02-unknowing.md#u7),
[SE1/D13](software-engineering/guide/05-design.md#d13)).

| Directory | Source | Pinned at | Date | License |
| --------- | ------ | --------- | ---- | ------- |
| `software-engineering/` | https://github.com/wmacevoy/software-engineering | tag `v1.3.1`, commit `00488c8066c8637b94c28aa5fdb2cb6ed4e71533` | 2026-10-28 | MIT (its `LICENSE`) |

## What the game takes from the guide

- Every principle card's ID, chapter, title, and *Ask* line are read from
  `software-engineering/guide/*.md` at run time; the game stores no copy of that text
  ([SE1/D6](software-engineering/guide/05-design.md#d6): derive instead of store). A test fails if
  the guide's principle index and the game's card table disagree.
- `AGENTS.md`, `se`, `se.py`, and `se.ps1` at the repository root are copies of the files of the
  same name here, as the guide's [ADOPT.md](software-engineering/ADOPT.md) asks.

## Re-vendoring

```sh
git clone --depth 1 --branch vX.Y https://github.com/wmacevoy/software-engineering /tmp/se
rm -rf vendor/software-engineering && mkdir vendor/software-engineering
(cd /tmp/se && tar --exclude=.git -cf - .) | (cd vendor/software-engineering && tar -xf -)
cp vendor/software-engineering/AGENTS.md vendor/software-engineering/se vendor/software-engineering/se.py vendor/software-engineering/se.ps1 .
```

Then update the table above, read *For copies* under the new release in its `CHANGELOG.md`, and
run `./se --doctor` and `sh check.sh`.
