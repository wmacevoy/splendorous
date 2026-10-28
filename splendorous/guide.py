"""Reads the vendored guide: every principle's ID, chapter, title, and *Ask* line.

The game stores none of that text; it is derived from `vendor/software-engineering` at start-up
(REQ1/GUIDE-3), so a re-vendored guide changes the cards and nothing else. The parsers take
strings and return values; `load_guide` is the one function that touches the file system.
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

MAJOR = "SE1"  # the guide's major version; every citation carries it

# One line of the README's principle index:  - [**SE1/P1**](guide/01-purpose.md#p1) Title
INDEX_RE = re.compile(r"^- \[\*\*SE1/([A-Z]+\d+)\*\*\]\((guide/[^)#]+)#([a-z0-9]+)\)\s+(.+?)\s*$")
# A principle's heading in a chapter:  ### <a id="p1"></a>P1. Title
HEADING_RE = re.compile(r'^### <a id="([a-z0-9]+)"></a>([A-Z]+\d+)\. ')
ASK_RE = re.compile(r"^> \*\*Ask:\*\*\s*(.*)$")
CHAPTER_NAME_RE = re.compile(r"^# \d+\. (.+?)\s*$")


class GuideError(Exception):
    """The guide is absent or not in the shape the parsers expect."""


@dataclass(frozen=True)
class Principle:
    id: str            # "T3"
    chapter: str       # "T"
    title: str
    ask: Optional[str]  # None where the guide has no Ask line
    path: str          # "guide/06-testing.md"
    anchor: str        # "t3"

    @property
    def citation(self) -> str:
        return f"{MAJOR}/{self.id}"


@dataclass(frozen=True)
class Guide:
    principles: List[Principle]      # in index order
    chapter_names: Dict[str, str]    # "T" -> "Testing"

    def by_id(self) -> Dict[str, Principle]:
        return {p.id: p for p in self.principles}


def chapter_of(principle_id: str) -> str:
    return re.match(r"[A-Z]+", principle_id).group(0)


def parse_index(readme: str) -> List[dict]:
    """The index lines of the guide's README, in order: id, path, anchor, title."""
    out = []
    for line in readme.splitlines():
        m = INDEX_RE.match(line)
        if m:
            out.append({"id": m.group(1), "path": m.group(2), "anchor": m.group(3), "title": m.group(4)})
    return out


def parse_asks(chapter: str) -> Dict[str, Optional[str]]:
    """For each principle heading in a chapter file, its Ask line's text, or None.

    An Ask is a blockquote that may wrap onto following `> ` lines; the surrounding quotation
    marks are dropped, and inner ones (a principle with two questions) are kept.
    """
    asks: Dict[str, Optional[str]] = {}
    current = None
    lines = chapter.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        h = HEADING_RE.match(line)
        if h:
            current = h.group(2)
            asks[current] = None
        elif current is not None:
            a = ASK_RE.match(line)
            if a:
                parts = [a.group(1).strip()]
                while i + 1 < len(lines) and lines[i + 1].startswith("> ") and not lines[i + 1].startswith("> **"):
                    i += 1
                    parts.append(lines[i][2:].strip())
                asks[current] = " ".join(parts).strip().strip('"')
        i += 1
    return asks


def parse_chapter_name(chapter: str) -> Optional[str]:
    for line in chapter.splitlines():
        m = CHAPTER_NAME_RE.match(line)
        if m:
            return m.group(1)
    return None


def load_guide(root: Path) -> Guide:
    """The vendored guide at `root` (the directory holding README.md and guide/)."""
    readme = Path(root) / "README.md"
    if not readme.is_file():
        raise GuideError(f"no guide at {root}: README.md is missing")
    index = parse_index(readme.read_text(encoding="utf8"))
    if not index:
        raise GuideError(f"{readme} has no principle index")
    chapter_texts: Dict[str, str] = {}
    for entry in index:
        if entry["path"] not in chapter_texts:
            p = Path(root) / entry["path"]
            if not p.is_file():
                raise GuideError(f"the index names {entry['path']}, which is missing")
            chapter_texts[entry["path"]] = p.read_text(encoding="utf8")
    asks = {}
    names = {}
    for path, text in chapter_texts.items():
        asks.update(parse_asks(text))
        for entry in index:
            if entry["path"] == path:
                names[chapter_of(entry["id"])] = parse_chapter_name(text) or path
    principles = [Principle(e["id"], chapter_of(e["id"]), e["title"], asks.get(e["id"]), e["path"], e["anchor"])
                  for e in index]
    return Guide(principles, names)


def default_root() -> Path:
    """The vendored guide, relative to this package: vendor/software-engineering at the repository root."""
    return Path(__file__).resolve().parent.parent / "vendor" / "software-engineering"
