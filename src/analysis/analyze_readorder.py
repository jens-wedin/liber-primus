"""Reading-order diagnostic: does a geometric transpose beat row-major? (N23)

The Swedish paper reads the page-4 imagery (MOBIUS, AETHEREAL BUFFERS, OBSCURA;
"shed our circumference") as evidence that the runes must be re-ordered
geometrically — a concentric "circumference peel" or a Möbius half-twist — before
decryption. This tests that directly, without a brute, because the campaign's
central finding hands us a discriminator for free.

The unsolved stream's ONE structure is a lag-1 no-repeat deficiency (doublets
0.66% vs 3.45%). A no-repeat rule suppresses equal ADJACENT outputs, so the
deficiency lives in the cipher's true output order and nowhere else. Re-order the
runes and the deficiency moves with the true order: the reading order that carries
it (lowest doublet rate) is the cipher order. So we lay each page out as a grid
(rows = physical lines) and measure the doublet rate under each candidate reading
order. The lowest wins.

Power is shown by a planted control: a stream whose doublets are suppressed along
COLUMNS is detected as column-order (its row-major projection reads as random).

Run: python3 src/analysis/analyze_readorder.py
"""

# --- path bootstrap ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end bootstrap ---

from collections import Counter

import gematria as g
from parse_lp import parse
from doublet_sim import LCG

N = g.N


def rows_of(seg):
    rows = []
    for ln in seg.rune_text.split("\n"):
        idx = g.runes_to_indices(ln)
        if idx:
            rows.append(idx)
    return rows


def _rect(rows):
    w = max(len(r) for r in rows)
    return [r + [None] * (w - len(r)) for r in rows], w


def peel(rows, outer_first=True):
    grid, _ = _rect(rows)
    rings = []
    top, bot, left, right = 0, len(grid) - 1, 0, len(grid[0]) - 1
    while top <= bot and left <= right:
        ring = [grid[top][j] for j in range(left, right + 1)]
        ring += [grid[i][right] for i in range(top + 1, bot + 1)]
        if top < bot:
            ring += [grid[bot][j] for j in range(right - 1, left - 1, -1)]
        if left < right:
            ring += [grid[i][left] for i in range(bot - 1, top, -1)]
        rings.append(ring)
        top += 1; bot -= 1; left += 1; right -= 1
    if not outer_first:
        rings = rings[::-1]
    return [x for r in rings for x in r if x is not None]


def transforms(rows):
    grid, w = _rect(rows)
    boust = []
    for k, r in enumerate(rows):
        boust += r if k % 2 == 0 else r[::-1]
    return {
        "row-major(=transcription)": [x for r in rows for x in r],
        "reverse-rows":              [x for r in rows[::-1] for x in r],
        "boustrophedon":             boust,
        "rot180(Möbius)":            [x for r in rows[::-1] for x in r[::-1]],
        "column-major(transpose)":   [grid[i][j] for j in range(w)
                                      for i in range(len(grid))
                                      if grid[i][j] is not None],
        "peel outer→in":             peel(rows, True),
        "peel in→out":               peel(rows, False),
    }


def rate_ioc(segments_flats):
    """Doublet rate and IoC over concatenated segment streams (segment breaks
    never count as an adjacency)."""
    db = adj = 0
    pool = []
    for flat in segments_flats:
        pool += flat
        for i in range(len(flat) - 1):
            adj += 1
            if flat[i] == flat[i + 1]:
                db += 1
    c = Counter(pool)
    n = len(pool)
    ioc = sum(v * (v - 1) for v in c.values()) / (n * (n - 1)) * N
    return db, adj, 100 * db / adj, ioc


def run(segs):
    uns = [s for s in segs if not s.solved and len(s.indices) >= 50]
    by = {}
    for s in uns:
        rows = rows_of(s)
        if len(rows) < 2:
            continue
        for name, flat in transforms(rows).items():
            by.setdefault(name, []).append(flat)
    print("reading order                doublets/adj    rate     IoC")
    results = {}
    for name, flats in by.items():
        db, adj, rate, ioc = rate_ioc(flats)
        results[name] = rate
        print(f"  {name:26s} {db:4d}/{adj:5d}   {rate:6.3f}%   {ioc:.3f}")
    best = min(results, key=results.get)
    print(f"\n  random expectation {100/N:.3f}%.  lowest (=cipher order): {best}")
    return results, best


def planted_control():
    """A stream with doublets suppressed along COLUMNS, laid out row-major.
    The diagnostic must pick column-major as the lowest-rate order."""
    rng = LCG(20260826)
    R, C = 40, 30
    cols = []
    for _ in range(C):
        col = []
        for _ in range(R):
            v = rng.randint(N)
            while col and v == col[-1]:      # suppress column doublets
                v = rng.randint(N)
            col.append(v)
        cols.append(col)
    rows = [[cols[j][i] for j in range(C)] for i in range(R)]

    class Seg:
        solved = False
        rune_text = "\n".join("".join(g.IDX_TO_RUNE[i] for i in r) for r in rows)
        @property
        def indices(self):
            return [x for r in rows for x in r]
        section = "planted-col"
    print("\n=== PLANTED CONTROL (doublets suppressed along COLUMNS) ===")
    res, best = run([Seg()])
    print(f"  -> control detects '{best}'"
          f" ({'PASS' if best.startswith('column') else 'FAIL'}: test resolves reading direction)")


def main():
    segs = parse("data/liber_primus.md")
    print("=== REAL unsolved stream ===")
    run(segs)
    planted_control()


if __name__ == "__main__":
    main()
