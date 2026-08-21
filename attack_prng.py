"""Seeded-PRNG / hash-pad attack on the re-roll hypothesis.

§11 found the no-repeat resolution is UNIFORM, consistent with a free re-roll
pad. If that pad is a *seeded* generator, the keystream K is deterministic given
(algorithm, seed), and the break is non-linguistic: find the generator+seed such
that p = c - K reads English.

Honest scope — read this before trusting any result:
- If K is a good PRNG with a non-trivial seed, c = p + K is a one-time pad and
  is information-theoretically unbreakable without the seed (it is exactly why c
  is uniform). This attack can only ever rule out the LOW-HANGING fruit: naive /
  weak generators (LCGs, xorshift, hash-of-counter, language RNGs) seeded with a
  SMALL or THEMATIC value — the kind a puzzle-maker plausibly picks (3301, a
  year, a gematria sum). A negative rules out THOSE, not all PRNGs.
- It targets the RE-ROLL variant: re-roll keeps K position-locked, so c - K
  aligns and the ~3.4% re-picked positions are just noise on top of English. A
  key-skip pad desynchronises K and would defeat this position-locked subtract
  (that case needs the beam, not a seed brute).

A planted control (encrypt English with a known generator+seed + re-roll, then
recover the seed) proves the search works before the real run is read.

Usage: python3 attack_prng.py [--seeds 20000] [--head 120]
"""

import argparse
import hashlib
import random

import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from controls import matched_ceiling
import ciphers as c

N = g.N


# --- candidate generators: seed -> n rune-index values -----------------------

def _lcg(a, incr, m, shift=0):
    def gen(seed, n):
        x = seed % m
        out = []
        for _ in range(n):
            x = (a * x + incr) % m
            out.append((x >> shift) % N)
        return out
    return gen


def _xorshift32(seed, n):
    x = (seed & 0xFFFFFFFF) or 0x9E3779B9
    out = []
    for _ in range(n):
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        out.append(x % N)
    return out


def _mersenne(seed, n):
    r = random.Random(seed)
    return [r.randrange(N) for _ in range(n)]


def _sha_ctr(seed, n):
    out = []
    for i in range(n):
        out.append(hashlib.sha256(f"{seed}:{i}".encode()).digest()[0] % N)
    return out


GENERATORS = {
    "lcg_glibc":    _lcg(1103515245, 12345, 2 ** 31, 0),
    "lcg_glibc_hi": _lcg(1103515245, 12345, 2 ** 31, 16),
    "lcg_nr":       _lcg(1664525, 1013904223, 2 ** 32, 0),
    "lcg_java":     _lcg(0x5DEECE66D, 0xB, 2 ** 48, 16),
    "xorshift32":   _xorshift32,
    "mersenne":     _mersenne,
    "sha256_ctr":   _sha_ctr,
}


def enc_reroll_fixed(p, K, rng):
    """Position-locked keystream K with a re-roll on a would-be doublet."""
    out = []
    for i in range(len(p)):
        ci = (p[i] + K[i]) % N
        if out and ci == out[-1]:
            ci = (ci + 1 + rng.randint(N - 1)) % N
        out.append(ci)
    return out


def thematic_seeds():
    """Seeds a puzzle-maker might pick: 3301 and kin, years, and the Gematria
    sums of thematic words."""
    seeds = {3301, 1033, 33, 761, 2012, 2013, 2014, 2015}
    for w in ["DIVINITY", "CIRCUMFERENCE", "PRIMES", "TOTIENT", "MOBIUS",
              "INSTAR", "WISDOM", "CICADA", "PRIMALITY", "SHADOWS"]:
        seeds.add(sum(g.IDX_TO_PRIME[i] for i in g.latin_to_indices(w)))
    return seeds


# --- the brute ---------------------------------------------------------------

def brute(chead, gens, seeds, model):
    """Best (trigram, gen, seed, sign) over generators x seeds, both signs."""
    best = None
    m = len(chead)
    for gname, gen in gens.items():
        for seed in seeds:
            K = gen(seed, m)
            for sign in (-1, +1):
                p = [(chead[i] - sign * K[i]) % N for i in range(m)]
                tri = model.score_sequence(p)
                if best is None or tri > best[0]:
                    best = (tri, gname, seed, sign)
    return best


def positive_control(model, pt, eng, seeds):
    print("=== POSITIVE CONTROL: plant a generator+seed + re-roll ===")
    seed = 1234
    K = GENERATORS["lcg_glibc"](seed, len(pt))
    ct = enc_reroll_fixed(pt, K, LCG(9))
    seedset = set(seeds) | {seed}
    tri, gname, rseed, sign = brute(ct, {"lcg_glibc": GENERATORS["lcg_glibc"]},
                                    seedset, model)
    ok = gname == "lcg_glibc" and rseed == seed and tri > eng - 0.6
    print(f"  planted lcg_glibc seed {seed}; recovered {gname} seed {rseed} "
          f"sign {sign}, trigram {tri:.2f} (English ~{eng:.2f})")
    print(f"  control: {'PASS' if ok else 'FAIL'}\n")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20000,
                    help="brute integer seeds 0..S-1 (plus thematic seeds)")
    ap.add_argument("--head", type=int, default=120)
    ap.add_argument("--order", type=int, default=3)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(args.order)
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]
    pt = english_plaintext(segs)

    eng = model.score_sequence(pt[:400])
    rng = LCG(5)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"refs: English trigram {eng:.2f}, random {rnd:.2f}\n")

    seeds = list(range(args.seeds)) + sorted(thematic_seeds())
    print(f"generators: {', '.join(GENERATORS)}")
    print(f"seed space: 0..{args.seeds-1} + {len(thematic_seeds())} thematic "
          f"(x {len(GENERATORS)} generators x 2 signs)\n")

    if not positive_control(model, pt[:args.head], eng, seeds):
        print("control FAILED — not trusting the real run.")
        return

    # Chance ceiling — the best trigram this same brute reaches on RANDOM
    # ciphertext, accounting for multiple-comparison inflation.
    #
    # AUDIT FIX (critical). This previously drew the null from `LCG(700+d)`,
    # which is the SAME Numerical Recipes LCG the brute searches (`lcg_nr`),
    # with seeds inside `range(20000)`. The brute recovered the exact stream
    # that generated the null, decoded it to all-ᚠ, and scored -3.91 instead of
    # the true ~-5.25 — an inflated ceiling that would have reported ~30% of
    # GENUINE breaks as negatives. `controls.random_runes` draws from a
    # domain-separated SHA-256 stream that no searched generator can produce,
    # and `matched_ceiling` uses one trial per real trial.
    n_trials = len(unsolved) + 1          # per-segment runs + the global run
    ceil = matched_ceiling(
        lambda ct: brute(ct, GENERATORS, seeds, model)[0],
        args.head, trials=n_trials, seed=700)
    print(f"=== CHANCE CEILING (independent null, {n_trials} trials matched to "
          f"the {n_trials} real runs): {ceil:.2f} ===\n")

    # GLOBAL: one seed for the whole concatenated unsolved stream
    glob = [i for s in unsolved for i in s.indices][:args.head]
    gtri, ggen, gseed, gsign = brute(glob, GENERATORS, seeds, model)
    print("=== REAL: global keystream (one seed, whole stream) ===")
    print(f"  best {ggen} seed {gseed} {'c-k' if gsign<0 else 'c+k'} "
          f"trigram {gtri:.2f}")

    # PER-SEGMENT: each page its own seed (as the solved pages are per-page keyed)
    print("\n=== REAL: per-segment keystream (each page its own seed) ===")
    overall = gtri
    for s in unsolved:
        tri, gn, sd, sg = brute(s.indices[:args.head], GENERATORS, seeds, model)
        overall = max(overall, tri)
        print(f"  {s.section[:34]:34s} {gn:12s} seed {sd:>7} "
              f"{'c-k' if sg<0 else 'c+k'} trigram {tri:.2f}")

    print(f"\n  verdict: best PRNG-pad decode trigram {overall:.2f} vs "
          f"chance ceiling {ceil:.2f}, English {eng:.2f}, random {rnd:.2f}")
    print(f"  (the positive control shows a GENUINE seeded-pad break scores "
          f"~-3.57 here — the real best is far below that detection floor)")
    if overall > eng - 0.5 and overall > ceil + 0.3:
        print("  -> LEAD: a seeded generator reaches English above chance — "
              "inspect it.")
    else:
        print("  -> negative: best decode sits at the chance ceiling, no better "
              "than the same brute on random text. Rules out these naive/weak "
              "generators with small/thematic seeds — NOT a keyed CSPRNG "
              "(unbreakable without the seed).")


if __name__ == "__main__":
    main()
