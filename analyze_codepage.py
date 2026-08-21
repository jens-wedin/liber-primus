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
    ceils = []
    for d in range(6):
        r = LCG(500 + d)
        ct = [r.randint(N) for _ in range(34)]
        ceils.append(attack_segment(ct, keys, model, 30, 100, 2)[0])
    ceil = max(ceils)
    print(f"  chance ceiling (these keys on random text): {ceil:.2f}")
    overall = None
    for s in segs:
        if s.solved or len(s.indices) < 50:
            continue
        bl, name, sign, dec, _ = attack_segment(s.indices, keys, model, 30, 100, 2)
        if overall is None or bl > overall[0]:
            overall = (bl, s.section, name)
    sig = overall[0] > eng - 0.5 and overall[0] > ceil + 0.5
    print(f"  best key decode trigram {overall[0]:.2f} on {overall[1][:26]} "
          f"({overall[2]}) vs ceiling {ceil:.2f} -> "
          f"{'SIGNAL' if sig else 'NO SIGNAL — gibberish'}")


if __name__ == "__main__":
    main()
