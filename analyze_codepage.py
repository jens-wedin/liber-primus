"""Analyse the two-character code pages the transcription drops (§15).

Page 67 is a full 13x8 grid of 104 two-character codes (no runes): each is a
digit 0-4 followed by a base-62 character (0-9, a-z, A-Z). Transcribed firsthand
below. This asks what the codes are: their alphabet/statistics, whether a
natural numeric decode of them reads as a rune MESSAGE (trigram English test),
and whether they act as a KEY for the unsolved runic pages.

Honest scope: the mapping from a 2-char code to a value is not given, so we try
the natural ones (base-62; digit x 26 + letter; second char alone) and mod-29
into rune space. A negative across these is not proof the page is meaningless —
only that these natural readings don't yield English.

Usage: python3 analyze_codepage.py
"""

import string
from collections import Counter

import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from attack_vigenere_skip import attack_segment
import ciphers as c

N = g.N

# Page 67, transcribed firsthand (13 rows x 8), reading order left-to-right.
PAGE67 = """
2M 0w 3L 3D 2r 0S 1p 15
3V 3e 3l 0n 3u 1O 0u 0Z
3g 2U 1C 0Y 1N 3n 0W 3Q
22 13 0V 3c 0E 34 0W 1t
1D 2N 3H 47 0s 2p 0Z 34
0g 3v 1Q 0s 0D 0K 2h 3D
3L 2x 1Q 20 2n 2L 1C 2p
0A 29 3r 0D 45 0k 2e 2W
25 3U 1W 2r 46 2s 2X 39
3p 0X 0E 1q 0q 4B 49 48
3r 3b 3C 1M 1j 0I 4A 48
40 3m 4E 0s 2S 1v 3T 0I
3t 2B 2k 2t 2O 0e 2l 1L
"""

B62 = string.digits + string.ascii_lowercase + string.ascii_uppercase   # 0..61


def codes():
    return PAGE67.split()


def b62(ch):
    return B62.index(ch)


def stats(cs):
    firsts = Counter(c[0] for c in cs)
    seconds = Counter(c[1] for c in cs)
    print(f"codes: {len(cs)}")
    print(f"first char (should be a small digit set): "
          f"{dict(sorted(firsts.items()))}")
    print(f"second char: {len(seconds)} distinct; range "
          f"{min(b62(c[1]) for c in cs)}..{max(b62(c[1]) for c in cs)}")
    vals62 = [5 * b62(c[1]) + int(c[0]) for c in cs]        # placeholder scan
    print(f"first-char set = {sorted(firsts)} ({len(firsts)} values)\n")


def decodings(cs):
    """Yield (name, rune-index list) for several natural code->rune maps."""
    out = []
    # A: value = digit*62 + base62(second)   -> mod 29
    out.append(("d*62+b62 %29", [(int(c[0]) * 62 + b62(c[1])) % N for c in cs]))
    # B: value = base62(second)*5 + digit    -> mod 29
    out.append(("b62*5+d %29", [(b62(c[1]) * 5 + int(c[0])) % N for c in cs]))
    # C: second char alone, base62 %29
    out.append(("b62(second) %29", [b62(c[1]) % N for c in cs]))
    # D: digit*26 + letterindex (letters only; caseless), else base62 %29
    def d26(c):
        s = c[1]
        if s.isalpha():
            return (int(c[0]) * 26 + (ord(s.lower()) - 97)) % N
        return (int(c[0]) * 10 + int(s)) % N
    out.append(("d*26+letter %29", [d26(c) for c in cs]))
    # E: pair as base-62 two-digit number, whole value %29 (same as A) -> skip
    # F: digit + 5*second-parity ... (kept minimal)
    return out


def main():
    cs = codes()
    stats(cs)

    segs = parse("data/liber_primus.md")
    model = get_model(3)
    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(3)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"refs: English trigram {eng:.2f}, random {rnd:.2f}\n")

    print("=== code page as a MESSAGE (decode -> runes -> trigram) ===")
    best_msg = None
    for name, ix in decodings(cs):
        tri = model.score_sequence(ix)
        latin = g.indices_to_latin(ix)
        print(f"  {name:18s} trigram {tri:.2f}   {latin[:46]}")
        if best_msg is None or tri > best_msg[0]:
            best_msg = (tri, name)
    print(f"  best message trigram {best_msg[0]:.2f} ({best_msg[1]}) "
          f"vs English {eng:.2f} -> "
          f"{'ENGLISH?' if best_msg[0] > eng - 0.5 else 'gibberish'}\n")

    print("=== code page as a KEY for the unsolved runic pages ===")
    keys = [(name, ix) for name, ix in decodings(cs)]
    # chance ceiling
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
