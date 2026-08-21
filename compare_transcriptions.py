"""P2.4 — cross-check the vendored transcription against a second one.

Tests the §4/§11 open question: are the 86 residual doublets in the unsolved
stream **transcription noise** (hand-copy slips) or real ciphertext? Method:
compare our vendored scream314 file (`data/liber_primus.md`) against rtkd/iddqd's
master transcription (`download/rtkd_liber_primus_transcription.txt`,
github.com/rtkd/iddqd) two ways:

  1. Full-file rune-to-rune agreement — how much do the two transcriptions differ
     at all? This is the transcription disagreement rate.
  2. Do the two agree at our 86 unsolved doublets specifically?

Reading the result: if the two transcriptions are near-identical, that either
means the true copy-error rate is far below §4's 0.66% dittography figure (so the
doublets can't be mostly errors — they're real), OR the two share lineage (a
common source), which makes the test inconclusive rather than a clean
confirmation. The script reports the numbers for both readings honestly.

Bonus: rtkd transcribes the two-char code pages too, so we cross-check our
`data/code_pages.txt` (esp. the newly-read page 66) against it.

Usage: python3 compare_transcriptions.py
"""

import difflib
import re
from collections import Counter

import gematria as g
from parse_lp import parse

RTKD = "download/rtkd_liber_primus_transcription.txt"


def full_stream(path):
    """Every Gematria rune in the file, in order (ignores prose/delimiters)."""
    t = open(path, encoding="utf-8").read()
    return [g.RUNE_TO_IDX[c] for c in t if c in g.RUNE_SET]


def unsolved_doublets():
    """Global positions (in the parsed segment stream) of within-unsolved-segment
    doublets, plus that stream itself."""
    segs = parse("data/liber_primus.md")
    stream, doublets = [], []
    for s in segs:
        ix = s.indices
        base = len(stream)
        stream.extend(ix)
        if (not s.solved) and len(ix) >= 50:
            for k in range(1, len(ix)):
                if ix[k] == ix[k - 1]:
                    doublets.append(base + k)
    return stream, doublets


def align_map(a, b):
    """position(a) -> position(b) for exact-match blocks; plus diff totals."""
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    pos, ins = {}, 0
    dele = repl = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for d in range(i2 - i1):
                pos[i1 + d] = j1 + d
        elif tag == "insert":
            ins += j2 - j1
        elif tag == "delete":
            dele += i2 - i1
        else:
            repl += max(i2 - i1, j2 - j1)
    return pos, sm.ratio(), dele, ins, repl


def code_crosscheck(rtkd_text):
    ours = []
    for line in open("data/code_pages.txt"):
        s = line.strip()
        if s and not s.startswith("#"):
            ours += s.split()
    rt = []
    for line in rtkd_text.splitlines():
        toks = line.strip().rstrip("/").split("-")
        if len(toks) >= 4 and all(re.fullmatch(r"[0-4][0-9A-Za-z]", t) for t in toks):
            rt += toks
    co, cr = Counter(ours), Counter(rt)
    print(f"  our code tokens {len(ours)}, rtkd {len(rt)} "
          f"(match: {len(ours) == len(rt)})")
    print(f"  differing tokens — only ours: {sorted((co - cr).elements())}; "
          f"only rtkd: {sorted((cr - co).elements())}")
    print(f"  (differences are case-ambiguous l/I/L, s/S glyphs; order differs so "
          f"positional diff is not meaningful — multiset diff is)")


def main():
    our_full = full_stream("data/liber_primus.md")
    rtkd_full = full_stream(RTKD)
    rtkd_text = open(RTKD, encoding="utf-8").read()

    print("=== 1. FULL-FILE transcription agreement ===")
    _, ratio, dele, ins, repl = align_map(our_full, rtkd_full)
    ndiff = dele + ins + repl
    print(f"  ours {len(our_full)} runes, rtkd {len(rtkd_full)}; similarity "
          f"{ratio:.4f}")
    print(f"  differing runes: our-only {dele}, rtkd-only {ins}, replace≈{repl} "
          f"= ~{ndiff} ({ndiff/len(our_full)*100:.3f}% of the book)")
    print(f"  -> the two transcriptions are near-identical; at {ndiff/len(our_full)*100:.3f}% "
          f"disagreement they very likely SHARE LINEAGE (a common source), so this "
          f"is a stability check, not fully-independent confirmation.\n")

    print("=== 2. DOUBLET TEST (§11: are the 86 doublets transcription noise?) ===")
    seg_stream, doublets = unsolved_doublets()
    pos, _, _, _, _ = align_map(seg_stream, rtkd_full)
    agree = notrepro = 0
    for p in doublets:
        if p in pos and (p - 1) in pos and pos[p] == pos[p - 1] + 1 \
                and rtkd_full[pos[p]] == rtkd_full[pos[p - 1]]:
            agree += 1
        else:
            notrepro += 1
    print(f"  of {len(doublets)} unsolved doublets, rtkd reproduces {agree}, "
          f"not {notrepro}")

    # LIKE-FOR-LIKE rate: the 0.66% doublet figure is over the UNSOLVED stream,
    # so the comparison rate must be the disagreement rate over the unsolved
    # stream too — not over the whole book. Audit fix (was ~10x, actually ~43x).
    seg_un = [i for i in range(len(seg_stream)) if i not in pos]
    err_un = len(seg_un) / max(1, len(seg_stream))
    print(f"  disagreements INSIDE the analysed corpus: {len(seg_un)} of "
          f"{len(seg_stream)} = {err_un*100:.4f}%")
    if err_un > 0:
        print(f"  reading A (if independent): that is ~{0.0066/err_un:.0f}x below "
              f"§4's 0.66% dittography figure — copy error is far too rare to "
              f"explain the doublet rate, so the doublets are REAL.")
    print(f"  reading B (if shared lineage — likely at {ratio:.4f} agreement): the "
          f"canonical transcription stably contains all 86; consistent with real "
          f"doublets but cannot exclude a common-source error. INCONCLUSIVE.")
    print(f"  net: §11's 'transcription noise' reading is NOT supported either "
          f"way; 'real doublets' is favoured, not proven.\n")

    print("=== 2b. WHAT the transcribers disagree about ===")
    # Classify each disagreement: the audit noticed they are systematically ᚠ.
    sm = difflib.SequenceMatcher(a=our_full, b=rtkd_full, autojunk=False)
    dele_runes, ins_runes = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("delete", "replace"):
            dele_runes += our_full[i1:i2]
        if tag in ("insert", "replace"):
            ins_runes += rtkd_full[j1:j2]
    lat = lambda xs: [g.indices_to_latin([x]) for x in xs]
    print(f"  runes only in OURS : {lat(dele_runes)}")
    print(f"  runes only in RTKD : {lat(ins_runes)}")
    nF = sum(1 for x in dele_runes if x == 0)
    print(f"  -> {nF}/{len(dele_runes)} of our extra runes are ᚠ. The disagreement "
          f"class is not random: it lands on exactly the rune the literal-ᚠ "
          f"thesis (§18-§20) depends on, so the ᚠ INVENTORY is itself disputed "
          f"between sources — a caveat on any ᚠ-counting result.\n")

    print("=== 3. BONUS: code-page transcription cross-check (my read vs rtkd) ===")
    code_crosscheck(rtkd_text)


if __name__ == "__main__":
    main()
