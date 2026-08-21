"""P2.5 — a GP-sum plausibility filter (tie-breaker for candidate decrypts).

§18's signature: two ADJACENT rune-runs whose Gematria-Primus sums hit 3301 and
1033 (with a ±2 literal-ᚠ knob). This asks whether that conjunction is rare
enough in ordinary text to be worth anything as a decrypt scorer.

TWO AUDIT FIXES (2026-08-21) — the first version was invalid:

1. The detector could not represent the signature it claimed to test. It gated
   BOTH runs to prime lengths, but §18's 3301 run is **74 runes** (75 with the
   skipped ᚠ) — not prime. So `themed_runs(...,3301,...)` returned nothing and
   the "real = 7" count contained ZERO true signatures: it compared noise to
   noise. Now only the 1033 run is prime-length (31, per §18) and the 3301 run
   is searched over a length WINDOW around 74.

2. The reference text excluded the run. `english_plaintext()` drops every keyed
   page, including page 73 "AN END" — the page carrying "…PILGRIM TO SEEK OUT
   THIS PAGE". We now use `solved_text.full_plaintext()`, which includes it.

The null is a SHUFFLE of the same plaintext (identical rune multiset, random
order), so composition is held fixed and only arrangement varies — the correct
null for "is this arrangement special?". (A uniform-random null would also
change the mean GP value per rune: 44.6 English vs 51.0 uniform.)

Usage: python3 gp_filter.py [--sims 400]
"""

import argparse

import gematria as g
from doublet_sim import LCG
from solved_text import full_plaintext

P = g.IDX_TO_PRIME
N = g.N
GP_SLACK = 2          # the literal-ᚠ (GP value 2) knob, in GP-VALUE units
ADJ_SLACK = 2         # run-abutment tolerance, in RUNE-POSITION units


def is_prime(n):
    return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))


def prefix_sums(pt):
    pref = [0] * (len(pt) + 1)
    for i, x in enumerate(pt):
        pref[i + 1] = pref[i] + P[x]
    return pref


def runs_hitting(pref, target, lengths, n):
    """(start, length) windows whose GP sum is within GP_SLACK of target."""
    out = []
    for ln in lengths:
        for a in range(0, n - ln + 1):
            if abs((pref[a + ln] - pref[a]) - target) <= GP_SLACK:
                out.append((a, ln))
    return out


def signature_count(pt, len3301, len1033):
    """Adjacent (3301-run, 1033-run) pairs, either order."""
    n = len(pt)
    pref = prefix_sums(pt)
    r3301 = runs_hitting(pref, 3301, len3301, n)
    r1033 = runs_hitting(pref, 1033, len1033, n)
    ends = {a + ln for a, ln in r3301}
    starts = {a for a, ln in r3301}
    cnt = 0
    for a, ln in r1033:
        if any(abs(a - e) <= ADJ_SLACK for e in ends) or \
           any(abs((a + ln) - s) <= ADJ_SLACK for s in starts):
            cnt += 1
    return cnt, len(r3301), len(r1033)


def shuffled(pt, rng):
    s = list(pt)
    for i in range(len(s) - 1, 0, -1):
        j = rng.randint(i + 1)
        s[i], s[j] = s[j], s[i]
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=400)
    args = ap.parse_args()

    pt = full_plaintext()
    n = len(pt)
    # §18: the 3301 run is 74-75 runes; the 1033 run is 31 (prime).
    len3301 = list(range(60, 91))
    len1033 = [L for L in range(20, 46) if is_prime(L)]
    print(f"solved plaintext (FULL, keyed pages included): {n} runes")
    print(f"  3301 searched at lengths {len3301[0]}..{len3301[-1]} "
          f"(§18's run is 74 — NOT prime, which the old prime-only gate could "
          f"not represent)")
    print(f"  1033 searched at prime lengths {len1033[0]}..{len1033[-1]} "
          f"(§18's run is 31)\n")

    real, n3301, n1033 = signature_count(pt, len3301, len1033)
    print(f"=== REAL solved plaintext ===")
    print(f"  3301-hitting runs {n3301}, 1033-hitting runs {n1033}, "
          f"ADJACENT pairs (the §18 signature) = {real}")
    if n3301 == 0:
        print("  !! zero 3301 runs — the detector cannot see the signature; "
              "do not interpret the comparison below.")

    print(f"\n=== NULL: {args.sims} shuffles of the SAME runes "
          f"(composition fixed, arrangement varied) ===")
    counts = []
    for d in range(args.sims):
        rng = LCG(5000 + d * 7919)
        counts.append(signature_count(shuffled(pt, rng), len3301, len1033)[0])
    counts.sort()
    mean = sum(counts) / len(counts)
    p_ge = sum(1 for x in counts if x >= real) / len(counts)
    pct95 = counts[int(len(counts) * 0.95)]
    print(f"  null mean {mean:.2f}, 95th pct {pct95}, max {counts[-1]}")
    print(f"  P(null >= real {real}) = {p_ge*100:.1f}%")

    if p_ge < 0.05:
        print("\n  -> DISCRIMINATES: the real arrangement is rarer than chance. "
              "Usable as a weak tie-breaker beside the n-gram score.")
    else:
        print("\n  -> does NOT discriminate: the §18 conjunction is as common in "
              "shuffles of the same text as in the real arrangement. The filter "
              "is unusable, and §18's co-occurrence carries no evidential "
              "weight — it is numerology.")
    print("\nEither way: never a primary signal — a real break must read as "
          "English first.")


if __name__ == "__main__":
    main()
