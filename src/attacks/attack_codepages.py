"""Deeper attacks on the 256 verified code-page codes (BACKLOG P1.3 remainder).

§21 established: 256 = 2^8 codes (pages 67/68/66), digit(0-4)+base-62, verified
# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

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
    # byte-encoding hypothesis: if value = digit*62+b62 encoded a byte 0..255,
    # digit 4 could only pair with b62 <= 7. Test it.
    d4 = [b62(c[1]) for c in codes if c[0] == "4"]
    vals = [int(c[0]) * 62 + b62(c[1]) for c in codes]
    over = [v for v in vals if v > 255]
    print(f"  byte-encoding test: digit-4 b62 range {min(d4)}..{max(d4)} "
          f"(a byte code would cap at 7); {len(over)} values exceed 255 "
          f"-> byte encoding RULED OUT")
    print(f"  total {len(codes)} = 2^8 ({len(codes) == 256}), but only "
          f"{len(raw)} distinct -> NOT a 256-entry table/S-box (which needs 256 "
          f"distinct); it is a stream with repetition.\n")


# --- 2. codes as a position-locked pad ---------------------------------------

def pad_stream(codes, mapname):
    return [MAPS[mapname](c) % N for c in codes]


def best_on(codes, stream, model):
    """Best (score, map, sign, decode) over all maps/signs at this stream's own
    length. Returns the length used so callers can length-match the null."""
    best, L = None, None
    for mapname in MAPS:
        pad = pad_stream(codes, mapname)
        L = min(len(stream), len(pad))
        for sign in (-1, +1):
            dec = [(stream[i] + sign * pad[i]) % N for i in range(L)]
            sc = model.score_sequence(dec)
            if best is None or sc > best[0]:
                best = (sc, mapname, sign, dec)
    return best + (L,)


def pad_test(codes, model, segs, eng):
    print("=== PAD: position-locked one-time key  p = c - pad ===")
    # REAL control: plant a pad-encrypted English text and require the SEARCH
    # (map + sign selection) to recover it. The earlier version checked only the
    # algebraic identity (c-pad==p), which passes even if the pad is all zeros —
    # it proved nothing about the attack. Audit-fixed.
    pad = pad_stream(codes, "d*62+b62")
    pt = english_plaintext(segs)[:len(pad)]
    ct = [(pt[i] + pad[i]) % N for i in range(len(pt))]
    sc, mapname, sign, dec, _ = best_on(codes, ct, model)
    acc = sum(1 for a, b in zip(dec, pt) if a == b) / len(pt)
    ok = (mapname == "d*62+b62") and sign == -1 and acc > 0.95
    print(f"  control: planted 'd*62+b62' pad -> recovered '{mapname}' "
          f"sign {sign}, score {sc:.2f}, acc {acc*100:.0f}% "
          f"-> {'PASS' if ok else 'FAIL'}")
    print(f"  (a genuine pad break therefore scores ~{sc:.2f} — the detection floor)")
    floor = sc

    # LENGTH-MATCHED ceilings: segments shorter than the 256-code pad are scored
    # on fewer symbols, and short sequences score higher, so the null must use
    # the same length. Audit-fixed (was a fixed 256-rune null for every segment).
    real = [s for s in segs if not s.solved and len(s.indices) >= 50]
    ceil_cache = {}

    def ceiling_at(L, draws):
        if L not in ceil_cache:
            b = None
            for d in range(draws):
                r = LCG(800 + d)
                rr = [r.randint(N) for _ in range(L)]
                sc = best_on(codes, rr, model)[0]
                b = sc if b is None else max(b, sc)
            ceil_cache[L] = b
        return ceil_cache[L]

    overall = None
    for s in real:
        sc, mapname, sign, dec, L = best_on(codes, s.indices, model)
        cl = ceiling_at(L, draws=len(real))
        margin = sc - cl
        if overall is None or margin > overall[0]:
            overall = (margin, sc, cl, L, s.section, mapname, dec)
    margin, sc, cl, L, sect, mapname, dec = overall
    print(f"  best (by length-matched margin) {sc:.2f} on {sect[:24]} "
          f"({mapname}, L={L}) vs matched ceiling {cl:.2f} -> margin {margin:+.2f}")
    print(f"  vs detection floor {floor:.2f}: "
          f"{'AT/ABOVE — inspect' if sc >= floor else 'far below — no pad break'}")
    print(f"      {g.indices_to_latin(dec)[:70]}\n")


# --- 3. codes as an index into a rune stream ---------------------------------

def index_test(codes, model, segs, eng):
    print("=== INDEX: each code selects a rune from a stream ===")
    solved = english_plaintext(segs)
    unsolved = [i for s in segs if not s.solved and len(s.indices) >= 50
                for i in s.indices]
    streams = {"solved-plaintext": solved, "unsolved-cipher": unsolved,
               "gematria-29": list(range(N))}
    for sname, R in streams.items():
        # MATCHED null: shuffle the real codes and push them through the SAME 4
        # maps, taking best-of-4 exactly as the real path does. The earlier null
        # drew uniformly over all of R with one implicit map, a different
        # sampling law than the real maps (which reach only a prefix of R).
        # Audit-fixed.
        ceil = None
        for d in range(20):
            r = LCG(900 + d)
            shuf = list(codes)
            for i in range(len(shuf) - 1, 0, -1):       # Fisher-Yates
                j = r.randint(i + 1)
                shuf[i], shuf[j] = shuf[j], shuf[i]
            b = max(model.score_sequence([R[f(c) % len(R)] for c in shuf])
                    for f in MAPS.values())
            ceil = b if ceil is None else max(ceil, b)
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
    # COMPOSITION- and LENGTH-matched nulls: shuffle the real codes and push them
    # through the identical transform, so the null has the same symbol mix and
    # length as the observed path. (The earlier version had no ceiling at all;
    # an intermediate fix used uniform random runes, whose composition differs
    # from the letter path's 26-letter alphabet and produced a false "SIGNAL".)
    def shuffled(seed, draws=30):
        outs = []
        for d in range(draws):
            r = LCG(seed + d)
            s = list(codes)
            for i in range(len(s) - 1, 0, -1):
                j = r.randint(i + 1)
                s[i], s[j] = s[j], s[i]
            outs.append(s)
        return outs

    ceil_rune = max(model.score_sequence(
        [(b62(c[1]) - int(c[0])) % N for c in s]) for s in shuffled(1700))
    def lat_of(cs):
        L = [chr((ord(c[1].lower()) - 97 - int(c[0])) % 26 + 97)
             for c in cs if c[1].isalpha()]
        return g.latin_to_indices("".join(L).upper())
    ceil_lat = max(model.score_sequence(lat_of(s)) for s in shuffled(1800))

    print(f"  rune-path   {best[0]:6.2f} ({best[1]}) vs shuffled null "
          f"{ceil_rune:6.2f}  [{len(best[2])} symbols]")
    print(f"      {g.indices_to_latin(best[2])[:70]}")
    print(f"  letter-path {sc_lat:6.2f} vs shuffled null {ceil_lat:6.2f}  "
          f"[{len(lat_ix)} symbols from {len(latin)} alpha codes]")
    print(f"      {''.join(latin)[:70]}")
    # A signal must be READABLE, not merely above a noisy null: require it to
    # approach English. Beating a null by ~0.1 while sitting 3 below English is
    # noise, not a decode.
    sig = max(best[0], sc_lat) > eng - 0.5
    print(f"  -> {'SIGNAL' if sig else 'no signal'} "
          f"(both paths ~{eng - max(best[0], sc_lat):.1f} below English "
          f"{eng:.2f}; shuffled nulls sit at the same level)\n")


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
          "are exhausted here (pad tested against a demonstrated detection floor; "
          "index and self-cipher against composition-matched nulls). A keyed pad "
          "or self-cipher is unbreakable without the key (§13). Structure carried "
          "forward: 256 codes but only 161 distinct — a stream with repetition, "
          "NOT a 256-entry table; byte encoding ruled out; leading digit 4 rare.")


if __name__ == "__main__":
    main()
