"""P2.4 — cross-check the vendored transcription against a second, independent one.

Tests the §4/§11 open question: are the 86 residual doublets in the unsolved
stream **transcription noise**, or real? Method: align our vendored scream314
stream (`data/liber_primus.md`) to rtkd/iddqd's independent master transcription
(`download/rtkd_liber_primus_transcription.txt`, from github.com/rtkd/iddqd) and
ask, at each of our unsolved doublets, whether rtkd reproduces it. If our
doublets disagree with rtkd at a much higher rate than runes in general, they are
transcription-dependent (noise); if rtkd reproduces them, they are real.

Bonus: rtkd also transcribes the two-char code pages, so we cross-check our
`data/code_pages.txt` (esp. the newly-read page 66) against rtkd independently.

Usage: python3 compare_transcriptions.py
"""

import difflib
import re

import gematria as g
from parse_lp import parse

RTKD = "download/rtkd_liber_primus_transcription.txt"


def our_stream():
    """Full ordered rune-index stream + a per-rune unsolved flag + the global
    positions of within-unsolved-segment doublets."""
    segs = parse("data/liber_primus.md")
    full, unsolved, doublets = [], [], []
    for s in segs:
        ix = s.indices
        base = len(full)
        un = (not s.solved) and len(ix) >= 50
        full.extend(ix)
        unsolved.extend([un] * len(ix))
        if un:
            for k in range(1, len(ix)):
                if ix[k] == ix[k - 1]:
                    doublets.append(base + k)          # 2nd rune of the pair
    return full, unsolved, doublets


def rtkd_stream():
    t = open(RTKD, encoding="utf-8").read()
    return g.runes_to_indices(t), t


def align(our, rtkd):
    sm = difflib.SequenceMatcher(a=our, b=rtkd, autojunk=False)
    pos_map, matched = {}, 0
    repl = dele = ins = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for d in range(i2 - i1):
                pos_map[i1 + d] = j1 + d
            matched += i2 - i1
        elif tag == "replace":
            repl += max(i2 - i1, j2 - j1)
        elif tag == "delete":
            dele += i2 - i1
        else:
            ins += j2 - j1
    return pos_map, matched, repl, dele, ins, sm.ratio()


def codepage_crosscheck(rtkd_text):
    """Extract rtkd's two-char code tokens and diff against data/code_pages.txt."""
    ours = []
    for line in open("data/code_pages.txt"):
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("##"):
            ours += s.split()
    # rtkd code rows: dash-joined [0-4][alnum] tokens, e.g. 3N-3p-2l-36-...
    rt = []
    for line in rtkd_text.splitlines():
        toks = line.strip().rstrip("/").split("-")
        if len(toks) >= 4 and all(re.fullmatch(r"[0-4][0-9A-Za-z]", t) for t in toks):
            rt += toks
    print(f"  our code tokens: {len(ours)}; rtkd code tokens: {len(rt)}")
    from collections import Counter
    co, cr = Counter(ours), Counter(rt)
    only_ours = list((co - cr).elements())
    only_rtkd = list((cr - co).elements())
    print(f"  multiset diff — only in ours: {sorted(set(only_ours))[:12]}")
    print(f"                  only in rtkd: {sorted(set(only_rtkd))[:12]}")
    # positional diff if same length (align by page-66 block, which both end with)
    if len(ours) == len(rt):
        d = [(i, a, b) for i, (a, b) in enumerate(zip(ours, rt)) if a != b]
        print(f"  same count; positional mismatches: {len(d)} {d[:6]}")
    return co, cr


def main():
    our, unsolved, doublets = our_stream()
    rtkd, rtkd_text = rtkd_stream()
    print(f"our runes: {len(our)} ({sum(unsolved)} unsolved); "
          f"rtkd runes: {len(rtkd)}")
    print(f"our unsolved within-segment doublets: {len(doublets)}\n")

    pos_map, matched, repl, dele, ins, ratio = align(our, rtkd)
    print(f"=== ALIGNMENT (difflib) ===")
    print(f"  similarity ratio {ratio:.4f}; matched {matched}/{len(our)} "
          f"({matched/len(our)*100:.1f}%) of our runes")
    print(f"  differing regions: replace≈{repl}, our-only(delete) {dele}, "
          f"rtkd-only(insert) {ins}\n")

    # baseline disagreement rate over all unsolved positions
    un_pos = [i for i, u in enumerate(unsolved) if u]
    un_diff = sum(1 for i in un_pos if i not in pos_map)
    base_rate = un_diff / len(un_pos)
    print(f"=== DOUBLET TEST (§11: are the doublets transcription noise?) ===")
    print(f"  baseline: {un_diff}/{len(un_pos)} unsolved runes fall in a "
          f"disagreeing region = {base_rate*100:.2f}%")

    agree = diff_runes = in_indel = 0
    for p in doublets:
        if p in pos_map and (p - 1) in pos_map and pos_map[p] == pos_map[p - 1] + 1:
            if rtkd[pos_map[p]] == rtkd[pos_map[p - 1]]:
                agree += 1                    # rtkd reproduces the doublet -> real
            else:
                diff_runes += 1               # rtkd has different runes here
        else:
            in_indel += 1                     # doublet sits in an indel/replace region
    not_repro = diff_runes + in_indel
    dbl_rate = not_repro / len(doublets)
    print(f"  of {len(doublets)} unsolved doublets: rtkd REPRODUCES {agree}, "
          f"does NOT reproduce {not_repro} ({diff_runes} different runes, "
          f"{in_indel} in an indel region) = {dbl_rate*100:.0f}% not reproduced")
    enrich = dbl_rate / base_rate if base_rate else float('inf')
    print(f"  doublet disagreement {dbl_rate*100:.0f}% vs baseline "
          f"{base_rate*100:.2f}% -> {enrich:.1f}x enriched")
    if agree <= not_repro and enrich > 3:
        print("  -> doublets are strongly transcription-DEPENDENT: the two "
              "transcribers largely disagree exactly at our doublets. Supports "
              "§11 'the 86 doublets are transcription noise'.")
    elif agree > not_repro:
        print("  -> rtkd REPRODUCES most doublets: they are REAL in both "
              "transcriptions, NOT mere transcription noise. Revises §11.")
    else:
        print("  -> mixed; see the numbers above.")

    print("\n=== BONUS: code-page transcription cross-check (my read vs rtkd) ===")
    codepage_crosscheck(rtkd_text)


if __name__ == "__main__":
    main()
