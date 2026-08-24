"""P2.6 — read the magic squares themselves as a MESSAGE (not as a key).

§16/§17 tested the page-16/page-32 squares as additive keys and interrupter
schedules for the runic pages (both negative). This asks the other question: do
the square VALUES, read directly, spell something? Natural readings —

  - values (mod 29) -> runes, in several reading paths (row/col/spiral/boustro,
    diagonals, unique-in-order);
  - page-32 prime structure: 3301 - value is a prime; its Gematria-Primus index
    (when it is one of the 29 GP primes) or its prime ordinal (mod 29) -> runes;
  - values (mod 256) -> ASCII bytes.

Honest, decisive caveat: these squares are 25 (5x5) and 16 (4x4) values. Twenty-
five runes is far too short to separate English from chance by n-gram score, and
we try many reading paths. So the discriminating test is a **permutation null**:
shuffle the square's OWN cells, re-run the identical battery, and ask whether the
real arrangement's best decode is rarer than its own shuffles. This holds length
and composition fixed and compares best-of-battery with best-of-battery.

(Audit note: the first version used random-valued grids as the null. That was
invalid — for random values `3301 - v` is rarely prime, so the prime-based
readings collapsed to 3-5 symbols, and the per-symbol score's SD explodes at
short length, so the "ceiling" was set by the shortest random reading rather
than a comparable one. It also compared ~2400 null samples against 12 real ones.
Under the corrected null the page-32 result is MARGINAL (p≈8%), not the clean
negative first reported.)

Usage: python3 analyze_squares.py
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import string

import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from attack_magicsquare import M16, M32, GP_INDEX
from attack_magicsquare_interrupter import ORDERS   # row/col/boustro/spiral

N = g.N


def isprime(n):
    return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))


def prime_ordinal(p):
    n, c = 2, 0
    while True:
        if isprime(n):
            c += 1
            if n == p:
                return c
        n += 1


def readings(M, is32):
    """(name, rune-index list) candidate messages from a square."""
    out = []
    for oname, f in ORDERS.items():
        vals = f(M)
        out.append((f"{oname}/mod29", [v % N for v in vals]))
        if is32:
            primes = [3301 - v for v in vals]
            gp = [GP_INDEX[p] for p in primes if p in GP_INDEX]
            if len(gp) >= 3:
                out.append((f"{oname}/gp-idx", gp))
            ordn = [prime_ordinal(p) % N for p in primes if isprime(p)]
            if len(ordn) >= 3:
                out.append((f"{oname}/prime-ord", ordn))
    return out


def ascii_reading(M):
    from attack_magicsquare_interrupter import rowmajor
    s = "".join(chr(v % 256) for v in rowmajor(M))
    printable = sum(1 for ch in s if ch in string.printable) / len(s)
    return s, printable


def permutation_null(M, model, is32, draws, seed=1000):
    """PERMUTATION null: shuffle the square's OWN cells and re-run the identical
    battery. Returns the per-draw best-of-battery scores.

    Audit fix. The previous null drew uniform random cell values, which was
    invalid twice over: (a) `3301 - v` was then rarely prime, so the `gp-idx`
    and `prime-ord` readings collapsed to 3-5 symbols (or never fired at all),
    and `score_sequence` is a per-symbol mean whose SD explodes at short length
    (1.84 at L=3 vs 0.79 at L=16) — so the ceiling was set by whichever random
    reading happened to be shortest, not by a comparable one; and (b) it took a
    max over draws x readings (~2400 samples) and compared it to a max over 12
    real readings, an asymmetric multiplicity that made the test near
    unfalsifiable. Shuffling the real cells holds length AND composition fixed,
    and we compare best-of-battery to best-of-battery."""
    ncol = 4 if is32 else 5
    flat = [v for r in M for v in r]
    out = []
    for d in range(draws):
        rng = LCG(seed + d * 7919)
        s = list(flat)
        for i in range(len(s) - 1, 0, -1):
            j = rng.randint(i + 1)
            s[i], s[j] = s[j], s[i]
        Ms = [s[i:i + ncol] for i in range(0, len(s), ncol)]
        best = None
        for _, ix in readings(Ms, is32):
            sc = model.score_sequence(ix)
            best = sc if best is None else max(best, sc)
        if best is not None:
            out.append(best)
    return out


def main():
    segs = parse("data/liber_primus.md")
    model = get_model(3)
    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(3)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"refs: English trigram {eng:.2f}, random {rnd:.2f}")
    print("(NB: 16-25 runes is too short for a decisive n-gram test — the "
          "permutation null is the real comparison)\n")

    for name, M, is32, size in [("page-16 (5x5, 3301)", M16, False, 25),
                                ("page-32 (4x4, 3301-prime)", M32, True, 16)]:
        print(f"=== {name} ===")
        nulls = permutation_null(M, model, is32, draws=2000)
        best = None
        for rname, ix in readings(M, is32):
            sc = model.score_sequence(ix)
            if best is None or sc > best[0]:
                best = (sc, rname, ix)
        p = sum(1 for x in nulls if x >= best[0]) / len(nulls)
        nm = sum(nulls) / len(nulls)
        s, pr = ascii_reading(M)
        print(f"  best reading: {best[1]:16s} trigram {best[0]:.2f} "
              f"[{len(best[2])} symbols]")
        print(f"      {g.indices_to_latin(best[2])}")
        print(f"  permutation null (2000 shuffles of these cells, "
              f"best-of-battery): mean {nm:.2f}")
        print(f"  P(null >= real) = {p*100:.1f}%")
        print(f"  ascii(mod256) printable {pr*100:.0f}%: {repr(s)[:52]}")
        if p < 0.05:
            verdict = (f"REAL SQUARE STANDS OUT (p={p*100:.1f}%) — but it is "
                       f"{eng - best[0]:.1f} below English, so this is an "
                       f"ordering quirk, not readable text")
        else:
            verdict = (f"indistinguishable from its own shuffles "
                       f"(p={p*100:.1f}%) — no message")
        print(f"  -> {verdict}\n")

    print("Verdict: page-16 is indistinguishable from its own shuffles (p=72%) — "
          "no message. Page-32's best reading is MARGINAL (p~8%): not significant, "
          "but not the clean negative first reported either; and at 14 symbols, "
          "2.5 below English, it is an ordering quirk of a 16-cell grid rather "
          "than readable text. Neither square yields a message; the squares' "
          "meaning remains their 3301/prime structure.")


if __name__ == "__main__":
    main()
