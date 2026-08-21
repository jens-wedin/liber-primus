"""Analyse the two-character code pages the transcription drops (§15, P1.3).

Pages 66/67/68 carry two-character codes: a digit 0-4 followed by a base-62
character (0-9, a-z, A-Z). Page 67 is a full 13x8 grid (104 codes, no runes);
page 68 is 9x8 (72) above 4 rune lines; page 66 is 10x8 (80) below 3 rune lines
and a red pixel-block. All three are transcribed in `data/code_pages.txt` and
were re-verified against the scans on 2026-08-21 (67/68 exact, 66 first pass).

This asks what the codes are: their alphabet/statistics, whether a natural
numeric decode reads as a rune MESSAGE (trigram English test), and whether they
act as a KEY for the unsolved runic pages — now on the full, verified 256-code
set rather than page 67 alone.

Honest scope: the map from a 2-char code to a value is not given, so we try the
natural ones (base-62; digit x 26 + letter; second char alone) mod-29 into rune
space. A negative across these is not proof the pages are meaningless — only that
these natural readings don't yield English.

Usage: python3 analyze_codepage.py
"""

import string
from collections import Counter

import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from attack_vigenere_skip import attack_segment
from no_repeat_model import enc_key_skip
from controls import detection_floor, matched_ceiling, verdict

N = g.N
B62 = string.digits + string.ascii_lowercase + string.ascii_uppercase   # 0..61


def load_pages(path="data/code_pages.txt"):
    """Parse the `## page NN ...` blocks into {page: [codes]}."""
    pages, name, cur = {}, None, []
    for line in open(path):
        s = line.strip()
        if s.startswith("## page"):
            if name is not None:
                pages[name] = cur
            name, cur = s.split()[2], []
        elif s and not s.startswith("#"):
            cur.extend(s.split())
    if name is not None:
        pages[name] = cur
    return pages


def b62(ch):
    return B62.index(ch)


def validate(pages):
    """Every code must be digit(0-4) + base-62 char; flag anything else."""
    bad = []
    for pg, cs in pages.items():
        for c in cs:
            if not (len(c) == 2 and c[0] in "01234" and c[1] in B62):
                bad.append((pg, c))
    if bad:
        print(f"  !! {len(bad)} malformed codes: {bad[:8]}")
    else:
        print("  format OK: every code is digit(0-4) + base-62 char")
    return not bad


def stats(name, cs):
    firsts = Counter(c[0] for c in cs)
    seconds = Counter(c[1] for c in cs)
    sec_max = seconds.most_common(1)[0][1]
    print(f"  {name:9s} {len(cs):3d} codes | 1st {dict(sorted(firsts.items()))} "
          f"| 2nd {len(seconds)} distinct, max count {sec_max}")


def decodings(cs):
    """(name, rune-index list) for several natural code->rune maps."""
    out = []
    out.append(("d*62+b62 %29", [(int(c[0]) * 62 + b62(c[1])) % N for c in cs]))
    out.append(("b62*5+d %29", [(b62(c[1]) * 5 + int(c[0])) % N for c in cs]))
    out.append(("b62(second) %29", [b62(c[1]) % N for c in cs]))

    def d26(c):
        s = c[1]
        if s.isalpha():
            return (int(c[0]) * 26 + (ord(s.lower()) - 97)) % N
        return (int(c[0]) * 10 + int(s)) % N
    out.append(("d*26+letter %29", [d26(c) for c in cs]))
    return out


def main():
    pages = load_pages()
    order = [p for p in ("67", "68", "66") if p in pages]
    allcodes = [c for p in order for c in pages[p]]
    print(f"loaded {len(pages)} pages, {len(allcodes)} codes total "
          f"({' + '.join(f'{p}:{len(pages[p])}' for p in order)})")
    validate(pages)
    for p in order:
        stats(f"page {p}", pages[p])
    stats("COMBINED", allcodes)
    print()

    segs = parse("data/liber_primus.md")
    model = get_model(3)
    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(3)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"refs: English trigram {eng:.2f}, random {rnd:.2f}\n")

    print("=== code stream as a MESSAGE (decode -> runes -> trigram) ===")
    best_msg = None
    for name, ix in decodings(allcodes):
        tri = model.score_sequence(ix)
        print(f"  {name:18s} trigram {tri:.2f}   {g.indices_to_latin(ix)[:46]}")
        if best_msg is None or tri > best_msg[0]:
            best_msg = (tri, name)
    print(f"  best message trigram {best_msg[0]:.2f} ({best_msg[1]}) "
          f"vs English {eng:.2f} -> "
          f"{'ENGLISH?' if best_msg[0] > eng - 0.5 else 'gibberish'}\n")

    print("=== code stream as a KEY for the unsolved runic pages ===")
    keys = decodings(allcodes)
    real = [s for s in segs if not s.solved and len(s.indices) >= 50]

    # Calibrated threshold (R1 fix): the old rule was `best > English - 0.5`,
    # which is wrong for beam scores (they carry a per-skip penalty and are
    # normalised by len-1), so a genuine break scores ~-4.0 and would have been
    # reported as "NO SIGNAL". Plant each code-derived key and recover it.
    pt = english_plaintext(segs)[:30]
    kmap = dict(keys)

    def plant(name):
        k = kmap[name]
        reps = len(pt) * 3 // len(k) + 4
        return enc_key_skip(pt, k * reps)

    def recover(ct):
        sc, nm, sign, dec, _ = attack_segment(ct, keys, model, 30, 100, 2)
        acc = sum(1 for a, b in zip(dec, pt) if a == b) / len(pt)
        return sc, nm, acc

    floor, covered, uncovered, _ = detection_floor(
        [n for n, _ in keys], plant, recover, label="code key")

    score_fn = lambda ct: attack_segment(ct, keys, model, 30, 100, 2)[0]
    ceil = matched_ceiling(score_fn, 30, trials=len(real), seed=500, extra=4)
    print(f"  matched chance ceiling (max over {len(real)} random texts): "
          f"{ceil:.2f}")
    overall = None
    for s in real:
        bl, name, sign, dec, _ = attack_segment(s.indices, keys, model, 30, 100, 2)
        if overall is None or bl > overall[0]:
            overall = (bl, s.section, name)
    print(f"  best on {overall[1][:26]} (map '{overall[2]}')")
    print(verdict(overall[0], floor, ceil, len(covered), len(keys),
                  label="code keys"))


if __name__ == "__main__":
    main()
