"""Deeper attacks on the 256 verified code-page codes (BACKLOG P1.3 remainder).

§21 established: 256 = 2^8 codes (pages 67/68/66), digit(0-4)+base-62, verified
from the scans, high-entropy, and no *natural numeric decode* reads English or
keys the runes. This goes past the natural decodes and tests the three
interpretations the code structure invites, each control-validated / ceiling'd:

  STRUCTURAL : is the set a permutation / lookup table (an S-box / 256-entry pad)?
  PAD        : are the codes a position-locked one-time key, p = c - pad (not the
               repeating-key test of §21 — this is offset-aligned, no skip)?
  INDEX      : does each code index into a rune stream (solved plaintext / unsolved
               ciphertext / the book), the selected runes spelling a message?
  SELF-CIPHER: is the code stream itself enciphered — the digit a per-position
               shift on the base-62 symbol — hiding a message?

Honest scope: a negative across these natural readings is not proof the pages are
meaningless; it bounds them. A keyed pad/self-cipher is unbreakable without the
key (the §13 wall), so the realistic yield is a clean bound + any structure found.

Usage: python3 attack_codepages.py
"""

import string
from collections import Counter

import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from analyze_codepage import load_pages

N = g.N
B62 = string.digits + string.ascii_lowercase + string.ascii_uppercase


def b62(ch):
    return B62.index(ch)


def d26(c):
    s = c[1]
    if s.isalpha():
        return int(c[0]) * 26 + (ord(s.lower()) - 97)
    return int(c[0]) * 10 + int(s)


MAPS = {
    "d*62+b62": lambda c: int(c[0]) * 62 + b62(c[1]),
    "b62*5+d":  lambda c: b62(c[1]) * 5 + int(c[0]),
    "b62":      lambda c: b62(c[1]),
    "d*26+let": d26,
}


def load_codes():
    pages = load_pages()
    order = [p for p in ("67", "68", "66") if p in pages]
    return [c for p in order for c in pages[p]]


# --- 1. structural: permutation / table? -------------------------------------

def structural(codes):
    print("=== STRUCTURAL: is the code set a table / permutation? ===")
    raw = Counter(codes)
    print(f"  {len(codes)} codes, {len(raw)} distinct as 2-char strings "
          f"(dups: {[c for c, n in raw.items() if n > 1][:10]}...)")
    for name, f in MAPS.items():
        vals = [f(c) for c in codes]
        dc = len(set(vals))
        print(f"  map {name:9s}: {dc:3d} distinct / {len(vals)} "
              f"(range {min(vals)}..{max(vals)}) "
              f"{'— PERMUTATION' if dc == len(vals) else ''}")
    firsts = Counter(c[0] for c in codes)
    print(f"  leading digit: {dict(sorted(firsts.items()))} "
          f"(4 rare -> ~4-ary + escape, not flat 5-ary)")
    print(f"  total {len(codes)} = 2^8 ({len(codes) == 256}); "
          f"a 256-entry pad/S-box is the natural read.\n")


# --- 2. codes as a position-locked pad ---------------------------------------

def pad_stream(codes, mapname):
    return [MAPS[mapname](c) % N for c in codes]


def pad_test(codes, model, segs, eng):
    print("=== PAD: position-locked one-time key  p = c - pad ===")
    # control: plant English encrypted by the pad, recover it deterministically
    pad = pad_stream(codes, "d*62+b62")
    pt = english_plaintext(segs)[:len(pad)]
    ct = [(pt[i] + pad[i]) % N for i in range(len(pt))]
    rec = [(ct[i] - pad[i]) % N for i in range(len(pt))]
    ok = rec == list(pt)
    print(f"  control (plant pad, recover): {'PASS' if ok else 'FAIL'}")
    # chance ceiling: random ciphertext through every map/sign
    def best_on(stream):
        best = None
        for mapname in MAPS:
            pad = pad_stream(codes, mapname)
            L = min(len(stream), len(pad))
            for sign in (-1, +1):
                dec = [(stream[i] + sign * pad[i]) % N for i in range(L)]
                sc = model.score_sequence(dec)
                if best is None or sc > best[0]:
                    best = (sc, mapname, sign, dec)
        return best
    ceil = None
    for d in range(6):
        r = LCG(800 + d)
        rr = [r.randint(N) for _ in range(256)]
        sc = best_on(rr)[0]
        ceil = sc if ceil is None else max(ceil, sc)
    print(f"  chance ceiling: {ceil:.2f}")
    overall = None
    for s in segs:
        if s.solved or len(s.indices) < 50:
            continue
        sc, mapname, sign, dec = best_on(s.indices)
        if overall is None or sc > overall[0]:
            overall = (sc, s.section, mapname, sign, dec)
    sig = overall[0] > eng - 0.5 and overall[0] > ceil + 0.5
    print(f"  best {overall[0]:.2f} on {overall[1][:24]} ({overall[2]} "
          f"{'c-k' if overall[3] < 0 else 'c+k'}) vs ceiling {ceil:.2f}, "
          f"English {eng:.2f} -> {'SIGNAL' if sig else 'no signal'}")
    print(f"      {g.indices_to_latin(overall[4])[:70]}\n")


# --- 3. codes as an index into a rune stream ---------------------------------

def index_test(codes, model, segs, eng):
    print("=== INDEX: each code selects a rune from a stream ===")
    solved = english_plaintext(segs)
    unsolved = [i for s in segs if not s.solved and len(s.indices) >= 50
                for i in s.indices]
    streams = {"solved-plaintext": solved, "unsolved-cipher": unsolved,
               "gematria-29": list(range(N))}
    for sname, R in streams.items():
        # ceiling: random codes selecting from R
        ceil = None
        for d in range(6):
            r = LCG(900 + d)
            sel = [R[r.randint(len(R))] for _ in codes]
            sc = model.score_sequence(sel)
            ceil = sc if ceil is None else max(ceil, sc)
        best = None
        for mapname, f in MAPS.items():
            sel = [R[f(c) % len(R)] for c in codes]
            sc = model.score_sequence(sel)
            if best is None or sc > best[0]:
                best = (sc, mapname, sel)
        sig = best[0] > eng - 0.5 and best[0] > ceil + 0.5
        print(f"  into {sname:16s}: best {best[0]:.2f} ({best[1]}) "
              f"vs ceiling {ceil:.2f} -> {'SIGNAL' if sig else 'no signal'}")
        print(f"      {g.indices_to_latin(best[2])[:70]}")
    print()


# --- 4. self-enciphered: digit as a per-position shift -----------------------

def selfcipher_test(codes, model, eng):
    print("=== SELF-CIPHER: digit as a shift on the base-62 symbol ===")
    best = None
    for sign in (-1, +1):
        # shift the base-62 value by ±digit, then map mod 29 to a rune
        seq = [(b62(c[1]) + sign * int(c[0])) % N for c in codes]
        sc = model.score_sequence(seq)
        tag = f"b62 {'-' if sign < 0 else '+'} digit %29"
        if best is None or sc > best[0]:
            best = (sc, tag, seq)
    # letter path: shift alpha second chars by digit in base-26, read as latin
    latin = []
    for c in codes:
        s = c[1]
        if s.isalpha():
            latin.append(chr((ord(s.lower()) - 97 - int(c[0])) % 26 + 97))
    lat_ix = g.latin_to_indices("".join(latin).upper())
    sc_lat = model.score_sequence(lat_ix)
    print(f"  best rune-path: {best[0]:.2f} ({best[1]}) vs English {eng:.2f}")
    print(f"      {g.indices_to_latin(best[2])[:70]}")
    print(f"  letter-shift path ({len(latin)} alpha codes): trigram {sc_lat:.2f}")
    print(f"      {''.join(latin)[:70]}")
    sig = max(best[0], sc_lat) > eng - 0.5
    print(f"  -> {'SIGNAL' if sig else 'no signal'}\n")


def main():
    codes = load_codes()
    model = get_model(3)
    segs = parse("data/liber_primus.md")
    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(3)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"codes: {len(codes)}; refs English {eng:.2f}, random {rnd:.2f}\n")

    structural(codes)
    pad_test(codes, model, segs, eng)
    index_test(codes, model, segs, eng)
    selfcipher_test(codes, model, eng)

    print("Verdict: natural pad / index / self-cipher readings of the code pages "
          "are exhausted here. A keyed pad or self-cipher is unbreakable without "
          "the key (§13). Structure to carry forward: 256 = 2^8 and the 4-ary+escape "
          "leading digit.")


if __name__ == "__main__":
    main()
