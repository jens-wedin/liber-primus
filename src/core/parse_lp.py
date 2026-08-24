"""Parse liber_primus.md (scream314/cicada3301) into (section, key, rune-text)
segments. A segment is one `**Key:** ...` annotation plus the indented rune
block that follows its `Runes:` marker."""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import re
from dataclasses import dataclass, field

import gematria as g


@dataclass
class Segment:
    section: str
    key: str
    rune_text: str = ""

    @property
    def indices(self):
        return g.runes_to_indices(self.rune_text)

    @property
    def words(self):
        return g.runes_to_words(self.rune_text)

    @property
    def solved(self):
        return not self.key.strip().startswith("?")


def parse(path):
    segments = []
    section = None
    key = None
    lines = open(path, encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            section = line[3:].strip()
        m = re.match(r"\*\*Key:\*\*\s*(.*)", line)
        if m:
            key = m.group(1).strip()
        if line.strip() == "Runes:" and section is not None and key is not None:
            i += 1
            block = []
            while i < len(lines):
                l = lines[i]
                if l.startswith("    ") or l.strip() == "":
                    block.append(l)
                    i += 1
                else:
                    break
            segments.append(Segment(section, key, "\n".join(block)))
            continue
        i += 1
    return segments


if __name__ == "__main__":
    segs = parse("data/liber_primus.md")
    total = solved = 0
    for s in segs:
        n = len(s.indices)
        total += n
        if s.solved:
            solved += n
        tag = "SOLVED " if s.solved else "UNSOLVED"
        print(f"{tag} {n:5d} runes | {s.section[:40]:40s} | key: {s.key[:60]}")
    print(f"\n{len(segs)} segments, {total} runes total, "
          f"{solved} in solved segments, {total - solved} unsolved")
