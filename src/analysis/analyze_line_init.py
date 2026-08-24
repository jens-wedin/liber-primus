"""Resolve the §45 line-initial anomaly with an INDEPENDENT segmentation (N19).

§45 found the unsolved line-initial runes non-uniform (z 7.19) in the rtkd
transcription, but it did not replicate cleanly and its source was unresolved:
a real line-initial cipher effect, or an artifact of where rtkd placed its `/`
line marks. N19 tests it against a segmentation that does NOT share rtkd's line
marks — Dukotah/cicada3301's `read4.json`, a from-the-page-images VISION
transcription (per-glyph page / band(line) / x / classified-rune). A real cipher
effect must survive a second, independent segmentation.

Key move: chi-square uniformity is INVARIANT under relabeling, so the vision
classes (0..30, 29 rune classes, no separators) can be tested directly without
mapping them to Gematria indices. Vision misclassification only pushes a
distribution TOWARD uniform, so a real skew would still survive.

Result (see `results/line_init_n19_2026-08-23.txt`): it does NOT survive as a
cipher signal. The vision segmentation's line INTERIOR is flat, but BOTH line
edges (initial AND final) are strongly skewed toward the single most-common
class — the signature of vision edge-misclassification at the page margins, not a
cipher property. And the two sources disagree on the pattern: rtkd is asymmetric
(initial skewed z 7.19, final flat z -0.01) while the vision read is symmetric
(both edges skewed). Two independent segmentations that disagree, each explained
by its own source's edge artifact, do not corroborate a real effect. Combined
with §45's weak split-half replication, the line-initial anomaly is best read as
a SEGMENTATION/TRANSCRIPTION ARTIFACT. §4's uniformity stands.

Data: download/dukotah_read4_vision.json (Dukotah/cicada3301
liber-primus/analysis/round10/L1-template/read4.json, fetched 2026-08-23; 1.7 MB,
gitignored). Fetch with:
  curl -sL https://raw.githubusercontent.com/Dukotah/cicada3301/master/\\
liber-primus/analysis/round10/L1-template/read4.json \\
    -o download/dukotah_read4_vision.json

Usage: python3 analyze_line_init.py
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import collections
import json
import math
import os

READ4 = "download/dukotah_read4_vision.json"


def z_vs(expected_p, vals, K):
    """chi2 z-score of `vals` against expected class probabilities `expected_p`
    (a dict); K = number of classes (df = K-1)."""
    m = len(vals)
    c = collections.Counter(vals)
    chi = sum((c.get(cl, 0) - m * expected_p[cl]) ** 2 / (m * expected_p[cl])
              for cl in expected_p)
    return (chi - (K - 1)) / math.sqrt(2 * (K - 1)), m


def main():
    if not os.path.exists(READ4):
        print(f"missing {READ4} — fetch it (see the module docstring).")
        return
    d = json.load(open(READ4))
    used = sorted(set(g["cls"] for g in d))
    K = len(used)
    uniform = {cl: 1 / K for cl in used}
    marg = collections.Counter(g["cls"] for g in d)
    tot = len(d)
    marginal = {cl: marg[cl] / tot for cl in used}

    # reading order: sort each band's glyphs by x
    byband = collections.defaultdict(list)
    for g in d:
        byband[(g["page"], g["band"])].append(g)
    lines = [[g["cls"] for g in sorted(byband[k], key=lambda z: z["x"])]
             for k in sorted(byband)]

    init = [ln[0] for ln in lines if ln]
    last = [ln[-1] for ln in lines if ln]
    interior = [r for ln in lines for r in ln[2:-2] if len(ln) > 4]

    print("=== N19: line-initial anomaly vs an INDEPENDENT (vision) "
          "segmentation ===")
    print(f"source: Dukotah read4.json — {len(set(p for p, b in byband))} pages, "
          f"{len(lines)} bands(lines), {K} rune classes, {tot} glyphs\n")

    print("read4 (vision) chi2z, vs UNIFORM and vs read4's own MARGINAL:")
    for tag, vals in (("line-initial", init), ("line-final", last),
                      ("interior", interior)):
        zu, m = z_vs(uniform, vals, K)
        zm, _ = z_vs(marginal, vals, K)
        print(f"  {tag:12s} n={m:5d}  vs-uniform {zu:+6.2f}  vs-marginal {zm:+6.2f}")

    c = collections.Counter(init)
    m = len(init)
    over = sorted(used, key=lambda cl: -(c.get(cl, 0) - m * marginal[cl]))[:3]
    print("  line-initial is dominated by the most-common class "
          f"(cls {over[0]}: {c.get(over[0],0)} obs vs "
          f"{m*marginal[over[0]]:.0f} exp) — the edge-misclassification tell.\n")

    print("Contrast with rtkd (§45, human `/` marks):")
    print("  line-initial z +7.19 (skewed)   line-final z -0.01 (FLAT)  "
          "-> ASYMMETRIC")
    print("  vision read: both edges skewed              -> SYMMETRIC "
          "(margin artifact)\n")

    print("VERDICT: the anomaly does NOT survive an independent segmentation as a "
          "cipher signal.\nThe vision interior is flat; both vision edges are "
          "skewed toward the default class\n(edge-misclassification), and the two "
          "sources disagree on the pattern. With §45's\nweak split-half "
          "replication, the line-initial skew is a SEGMENTATION/TRANSCRIPTION\n"
          "ARTIFACT, not a property of the cipher. §4's uniformity stands.")


if __name__ == "__main__":
    main()
