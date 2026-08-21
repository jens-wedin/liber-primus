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
we try many reading paths. So the discriminating test is a **numerology ceiling**:
run the identical battery on random "squares" and see whether the real square's
best decode stands out. It will not — which is the point: a short value grid
plus reading-path freedom hits gibberish that looks language-ish either way.

Usage: python3 analyze_squares.py
"""

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


def numerology_ceiling(model, is32, size, draws):
    """Best trigram from the same battery on random value-grids of the same shape."""
    best = None
    for d in range(draws):
        rng = LCG(1000 + d)
        flat = [rng.randint(4000) for _ in range(size)]
        M = [flat[i:i + (4 if is32 else 5)]
             for i in range(0, size, 4 if is32 else 5)]
        for _, ix in readings(M, is32):
            sc = model.score_sequence(ix)
            best = sc if best is None else max(best, sc)
    return best


def main():
    segs = parse("data/liber_primus.md")
    model = get_model(3)
    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(3)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"refs: English trigram {eng:.2f}, random {rnd:.2f}")
    print("(NB: 16-25 runes is too short for a decisive n-gram test — the "
          "numerology ceiling is the real comparison)\n")

    for name, M, is32, size in [("page-16 (5x5, 3301)", M16, False, 25),
                                ("page-32 (4x4, 3301-prime)", M32, True, 16)]:
        print(f"=== {name} ===")
        ceil = numerology_ceiling(model, is32, size, 200)
        best = None
        for rname, ix in readings(M, is32):
            sc = model.score_sequence(ix)
            if best is None or sc > best[0]:
                best = (sc, rname, ix)
        s, pr = ascii_reading(M)
        flag = " > ceiling" if best[0] > ceil else ""
        print(f"  numerology ceiling (random grids, same battery): {ceil:.2f}")
        print(f"  best reading: {best[1]:16s} trigram {best[0]:.2f}{flag}")
        print(f"      {g.indices_to_latin(best[2])}")
        print(f"  ascii(mod256) printable {pr*100:.0f}%: "
              f"{repr(s)[:56]}")
        verdict = ("stands out — inspect" if best[0] > ceil + 0.5 and best[0] > eng - 0.5
                   else "at/below the numerology ceiling — no message")
        print(f"  -> {verdict}\n")

    print("Verdict: reading the squares directly as runes/ASCII yields nothing "
          "above the numerology ceiling; and at 16-25 symbols no such test could "
          "be decisive anyway. The squares' meaning is their 3301/prime structure "
          "(established), not a hidden runic message.")


if __name__ == "__main__":
    main()
