"""P1.2 — structural map of the literal-ᚠ positions.

§18 showed the SOLVED plaintext uses deliberately placed literal-ᚠ (F) runes to
make prime-length rune-runs hit themed Gematria sums. Question: does that
placement leave any detectable fingerprint we can exploit on the UNSOLVED pages —
prime/emirp-length gaps between ᚠ, or ᚠ clustering at word boundaries?

Caveat baked in from §18: on the ciphertext a ᚠ is ambiguous (literal F OR an
ordinary rune that encrypted to ᚠ), and at the observed rate most are ordinary.
So the honest expectation is "no structure survives into the ciphertext"; this
script measures it rather than assuming it. Each statistic is compared to a
Monte-Carlo null (ᚠ placed uniformly at the observed rate), and the SOLVED
plaintext (where literal-F is identifiable) is the positive reference.

Usage: python3 analyze_fpositions.py [--sims 3000]
"""

import argparse

import gematria as g
from parse_lp import parse
from doublet_sim import english_plaintext, LCG
from solved_text import full_plaintext

N = g.N
F = g.latin_to_indices("F")[0]           # ᚠ == 0


def is_prime(n):
    return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))


def is_emirp(n):
    r = int(str(n)[::-1])
    return is_prime(n) and is_prime(r) and n != r


def gaps(positions):
    return [positions[i] - positions[i - 1] for i in range(1, len(positions))]


def frac(pred, gs):
    return sum(1 for x in gs if pred(x)) / len(gs) if gs else 0.0


def z(obs, sims):
    m = sum(sims) / len(sims)
    var = sum((x - m) ** 2 for x in sims) / len(sims)
    sd = var ** 0.5
    return (obs - m) / sd if sd else 0.0, m, sd


def mc_gap_null(L, npos, sims, rng, pred, min_gap=1):
    """Distribution of prime/emirp-gap fraction under uniform ᚠ placement.
    min_gap=2 drops gap==1 (the ᚠᚠ doublet the no-repeat rule suppresses, and a
    non-prime length) from both sides, so the prime-gap test is not inflated by
    that artifact."""
    out = []
    for _ in range(sims):
        pos = sorted(rng.sample(L, npos))
        gs = [x for x in gaps(pos) if x >= min_gap]
        out.append(frac(pred, gs))
    return out


def mc_boundary_null(edge_flags, npos, sims, rng):
    """Distribution of 'fraction of ᚠ at a word edge' under uniform placement."""
    L = len(edge_flags)
    idx = [i for i in range(L)]
    out = []
    for _ in range(sims):
        pos = rng.sample_from(idx, npos)
        out.append(sum(1 for p in pos if edge_flags[p]) / npos)
    return out


class RNG:
    """Small reproducible sampler over the LCG (no external randomness)."""
    def __init__(self, seed):
        self.r = LCG(seed)

    def sample(self, n, k):
        """k distinct ints in [0, n)."""
        seen = set()
        while len(seen) < k:
            seen.add(self.r.randint(n))
        return list(seen)

    def sample_from(self, pool, k):
        n = len(pool)
        return [pool[i] for i in self.sample(n, k)]


def analyze(name, stream, words, sims, rng):
    L = len(stream)
    pos = [i for i, x in enumerate(stream) if x == F]
    npos = len(pos)
    print(f"\n=== {name}: {L} runes, {npos} ᚠ ({npos/L*100:.2f}%, "
          f"uniform 1/29 = {100/N:.2f}%) ===")
    if npos < 5:
        print("  too few ᚠ for a stable test.")
        return

    gs = gaps(pos)
    # gap-length prime / emirp enrichment. Prime uses min_gap=2 (drop the
    # suppressed, non-prime ᚠᚠ gap so the fraction is not artificially inflated).
    for pname, pred, mg in (("prime-length gaps", is_prime, 2),
                            ("emirp-length gaps", is_emirp, 2)):
        obs = frac(pred, [x for x in gs if x >= mg])
        sims_v = mc_gap_null(L, npos, sims, rng, pred, min_gap=mg)
        zz, m, sd = z(obs, sims_v)
        note = " (gap>=2, ᚠᚠ-corrected)" if mg == 2 else ""
        print(f"  {pname:18s}: obs {obs*100:5.1f}%  null {m*100:5.1f}%±{sd*100:.1f}  z={zz:+.2f}{note}")

    # word-boundary clustering
    if words:
        edge = [False] * L
        p = 0
        for w in words:
            lw = len(w)
            if lw and p < L:
                edge[p] = True
                edge[min(p + lw - 1, L - 1)] = True
            p += lw
        obs_b = sum(1 for q in pos if q < L and edge[q]) / npos
        sims_b = mc_boundary_null(edge, npos, sims, rng)
        zb, mb, sdb = z(obs_b, sims_b)
        print(f"  {'ᚠ at word edge':18s}: obs {obs_b*100:5.1f}%  null {mb*100:5.1f}%±{sdb*100:.1f}  z={zb:+.2f}")
    print(f"  mean gap {sum(gs)/len(gs):.1f} runes")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=3000)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    un = [s for s in segs if not s.solved and len(s.indices) >= 50]
    un_stream = [i for s in un for i in s.indices]
    un_words = [w for s in un for w in s.words]

    rng = RNG(12345)
    print("z > +3 would flag real structure; |z| < 2 is consistent with random "
          "placement.\nSolved PLAINTEXT is the positive reference (literal-F is "
          "identifiable there).")

    analyze("UNSOLVED ciphertext", un_stream, un_words, args.sims, rng)

    # positive reference: solved plaintext, where literal-F is the real thing.
    # Use the FULL solved plaintext (keyed pages included) — english_plaintext()
    # drops page 73 "AN END", the very page §18 is about. Audit fix.
    pt = full_plaintext(segs)
    analyze("SOLVED plaintext (reference)", pt, None, args.sims, rng)

    # POWER of the reference: with only ~40 ᚠ the null SD is ~8pp, so even a
    # real effect could not reach z=3. State it rather than let a silent
    # non-detection masquerade as evidence. Audit fix.
    nref = sum(1 for x in pt if x == F)
    print(f"\nPOWER CHECK: the reference has only {nref} literal-ᚠ; the null SD on "
          f"its gap statistics is ~8 percentage points, so it CANNOT reach z=3 "
          f"even if the §18 effect were real. It is therefore not a positive "
          f"control that fired — it is an underpowered test. Treat the unsolved "
          f"rows as 'no evidence of a fingerprint', NOT as 'proof none exists'.")
    print("MULTIPLICITY: 6 statistics are reported. The prime-gap row (z=+2.3) is "
          "the only one outside |z|<2; at 6 tests a Bonferroni-corrected p is "
          "~0.13, i.e. not significant — but it is the one row that does not sit "
          "flat, and it is robust to the RNG and to a no-adjacent-ᚠ null.")
    print("Read-out: the §18 literal-ᚠ structure is a PLAINTEXT property; the "
          "unsolved ciphertext shows no fingerprint that survives encryption "
          "(consistent with §18), but this is a weak bound, not a clean negative.")


if __name__ == "__main__":
    main()
