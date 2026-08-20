"""Test the Liber Primus magic squares as keys for the unsolved runic pages.

The page images carry two numeric artifacts the rune transcription drops (§15):
  - page 16: a 5x5 magic square, magic constant 3301, palindromic, centre 809
  - page 32: a 4x4 grid where every cell is 3301 - a prime, with a Mobius symbol

Both are drenched in Cicada's prime/3301 theme, so the natural question is
whether either encodes a KEY for the still-unsolved runic segments. This derives
candidate keystreams from the squares (several reading orders and prime-based
transforms into rune-index space) and runs each through the SAME key-skip beam
as the word-key attack (`attack_vigenere_skip`), so the pipeline is already
control-validated. A planted CIRCUMFERENCE key must still be recovered, and a
random-ciphertext chance ceiling bounds the multiple-comparison inflation.

Honest scope: this tests the square VALUES as a repeating keystream under a set
of natural derivations. A negative rules those out; it cannot rule out every
possible way a square might key the text (e.g. a bespoke path or a per-page
sub-square).

Usage: python3 attack_magicsquare.py [--head 30] [--beam 100]
"""

import argparse

import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from attack_vigenere_skip import attack_segment, positive_control
import ciphers as c

N = g.N

M16 = [[434, 1311, 312, 278, 966],
       [204, 812, 934, 280, 1071],
       [626, 620, 809, 620, 626],
       [1071, 280, 934, 812, 204],
       [966, 278, 312, 1311, 434]]

M32 = [[3258, 3222, 3152, 3038],
       [3278, 3299, 3298, 2838],
       [3288, 3294, 3296, 2472],
       [4516, 1206, 708, 1820]]

GP_INDEX = {p: i for i, p in enumerate(g.IDX_TO_PRIME)}   # prime -> rune index


def rowmajor(M):
    return [v for r in M for v in r]


def colmajor(M):
    return [M[i][j] for j in range(len(M[0])) for i in range(len(M))]


def uniq(seq):
    out = []
    for v in seq:
        if v not in out:
            out.append(v)
    return out


def prime_ordinal(p):
    """1 for 2, 2 for 3, ... via a small sieve; p assumed prime."""
    n, count = 2, 0
    while True:
        if all(n % d for d in range(2, int(n ** 0.5) + 1)):
            count += 1
            if n == p:
                return count
        n += 1


def build_keys():
    keys = []

    def add(name, vals):
        ix = [v % N for v in vals]
        if len(ix) >= 2:
            keys.append((name, ix))

    # --- page 16 (values mod 29) ---
    add("sq16_row",  rowmajor(M16))
    add("sq16_col",  colmajor(M16))
    add("sq16_uniq", uniq(rowmajor(M16)))
    add("sq16_rev",  list(reversed(rowmajor(M16))))

    # --- page 32 (values mod 29) ---
    add("sq32_row",  rowmajor(M32))
    add("sq32_col",  colmajor(M32))

    # --- page 32 via its prime structure (3301 - value) ---
    primes32 = [3301 - v for v in rowmajor(M32)]
    add("sq32_primes_mod29", primes32)
    # only the cells whose (3301 - value) is a Gematria-Primus prime -> rune index
    gp = [GP_INDEX[p] for p in primes32 if p in GP_INDEX]
    add("sq32_gp_runes", gp)
    # the prime ORDINAL (2->1, 3->2, ...) mod 29, for the valid primes
    def isprime(n):
        return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))
    ordn = [prime_ordinal(p) % N for p in primes32 if isprime(p)]
    add("sq32_prime_ordinal", ordn)

    return keys


def chance_ceiling(keys, model, head, beam, max_skip, draws):
    scores = []
    for d in range(draws):
        rng = LCG(400 + d)
        ct = [rng.randint(N) for _ in range(head + 4)]
        scores.append(attack_segment(ct, keys, model, head, beam, max_skip)[0])
    return max(scores)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", type=int, default=30)
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--beam", type=int, default=100)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--draws", type=int, default=6)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(args.order)
    keys = build_keys()
    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(3)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])

    print(f"magic-square key derivations ({len(keys)}):")
    for name, k in keys:
        print(f"  {name:22s} len {len(k):2d}: {g.indices_to_latin(k)[:40]}")
    print(f"\nrefs: English trigram {eng:.2f}, random {rnd:.2f}\n")

    # the control plants CIRCUMFERENCE, so it must be in the searched set to
    # prove the beam recovers a real key; the real attack below uses only the
    # square-derived keys.
    ctrl_keys = keys + [("CIRCUMFERENCE", g.latin_to_indices("CIRCUMFERENCE"))]
    if not positive_control(ctrl_keys, model, args.head, args.beam, args.max_skip):
        print("control FAILED — not trusting the real run.")
        return

    ceil = chance_ceiling(keys, model, args.head, args.beam, args.max_skip,
                          args.draws)
    print(f"=== CHANCE CEILING (these keys on random text): {ceil:.2f} ===\n")

    print("REAL unsolved segments (magic-square keys + key-skip):")
    overall = None
    for s in segs:
        if s.solved or len(s.indices) < 50:
            continue
        bl, name, sign, dec, _ = attack_segment(
            s.indices, keys, model, args.head, args.beam, args.max_skip)
        flag = "  <-- ABOVE CEILING" if bl > ceil else ""
        print(f"  {s.section[:34]:34s} key '{name}' "
              f"{('c-k' if sign < 0 else 'c+k')} trigram {bl:.2f}{flag}")
        if overall is None or bl > overall[0]:
            overall = (bl, s.section, name)
    # a genuine key lands near English (~-3.4); merely edging a noisy ceiling
    # by tenths, while still ~1 below English, is chance.
    signal = overall[0] > eng - 0.5 and overall[0] > ceil + 0.5
    verdict = ("SIGNAL — a segment reads near English; inspect" if signal else
               "NO SIGNAL — best decode is gibberish, no better than chance")
    print(f"\nbest: trigram {overall[0]:.2f} on {overall[1][:30]} "
          f"(key '{overall[2]}') vs ceiling {ceil:.2f}, English {eng:.2f} "
          f"-> {verdict}")


if __name__ == "__main__":
    main()
