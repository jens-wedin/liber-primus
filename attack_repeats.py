"""Long exact ciphertext repeats vs a Smirnov null (N11).

A repeating-key or running-key cipher leaks through repeated ciphertext: the same
plaintext under the same key phase encrypts to the same runes, and the gap
between two such repeats is a multiple of the key period (Kasiski). The community
eyeballed ~5 multi-rune repeats book-wide; this mines EVERY exact repeat and asks
whether there are more than chance gives.

The null must be right. The real stream is uniform BUT almost never repeats an
adjacent rune (the 0.66% doublet rate), so an iid-uniform null is wrong — it
would over-count short repeats and overstate significance. The correct null is a
SMIRNOV sequence: uniform with no two adjacent runes equal. (The real stream's
tiny 0.66% doublet residual is negligible for k >= 5 repeats.)

Statistic: for each length k, the number of distinct k-grams occurring >= 2
times, computed identically on the real stream and on many Smirnov nulls.

If the real counts sit at the null, the repeats are coincidental — no Kasiski
anchors, and the gap-as-key-period step is vacuous (reported as such). If they
exceed it, the significant gaps are listed with their factorisations.

Usage: python3 attack_repeats.py [--kmin 5] [--kmax 12] [--nulls 300]
"""

import argparse
import collections
import math

import gematria as g
from parse_lp import parse
from doublet_sim import LCG

N = g.N


def unsolved_stream():
    segs = parse("data/liber_primus.md")
    return [i for s in segs if not s.solved and len(s.indices) >= 50
            for i in s.indices]


def smirnov(length, rng):
    """Uniform sequence with no two adjacent runes equal."""
    out = []
    for _ in range(length):
        r = rng.randint(N)
        if out and r == out[-1]:
            r = (r + 1 + rng.randint(N - 1)) % N
        out.append(r)
    return out


def repeated_kgrams(seq, k):
    """Number of distinct k-grams that occur >= 2 times, and the map of the
    repeated ones to their start positions."""
    pos = collections.defaultdict(list)
    for i in range(len(seq) - k + 1):
        pos[tuple(seq[i:i + k])].append(i)
    rep = {kg: p for kg, p in pos.items() if len(p) >= 2}
    return len(rep), rep


def factors(n):
    fs = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            fs.append(d)
            n //= d
        d += 1
    if n > 1:
        fs.append(n)
    return fs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kmin", type=int, default=5)
    ap.add_argument("--kmax", type=int, default=12)
    ap.add_argument("--nulls", type=int, default=300)
    args = ap.parse_args()

    U = unsolved_stream()
    L = len(U)
    print(f"unsolved stream: {L} runes\n")

    # self-check: the miner finds a planted repeat; the null is doublet-free
    probe = list(range(20)) + list(range(20))
    assert repeated_kgrams(probe, 5)[0] >= 1, "miner broken"
    s = smirnov(5000, LCG(7))
    assert all(s[i] != s[i - 1] for i in range(1, len(s))), "null not Smirnov"
    print("self-check: miner finds a planted repeat; Smirnov null is doublet-free\n")

    print(f"{'k':>3}  {'real':>6}  {'null mean':>9}  {'null sd':>7}  {'z':>6}")
    real_rep = {}
    flagged = []
    for k in range(args.kmin, args.kmax + 1):
        real_ct, rep = repeated_kgrams(U, k)
        real_rep[k] = rep
        null_cts = []
        for t in range(args.nulls):
            null_cts.append(repeated_kgrams(smirnov(L, LCG(5000 + t)), k)[0])
        mean = sum(null_cts) / len(null_cts)
        var = sum((x - mean) ** 2 for x in null_cts) / len(null_cts)
        sd = math.sqrt(var)
        z = (real_ct - mean) / sd if sd > 0 else (real_ct - mean)
        # exceedance p: fraction of nulls >= real
        p = (sum(1 for x in null_cts if x >= real_ct) + 1) / (args.nulls + 1)
        tag = "  <-- above null" if p < 0.05 and real_ct > mean else ""
        if tag:
            flagged.append(k)
        print(f"{k:>3}  {real_ct:>6}  {mean:>9.2f}  {sd:>7.2f}  {z:>6.2f}"
              f"  p={p:.3f}{tag}")

    # longest real repeats, with gaps and Kasiski factors
    print("\nlongest exact repeats in the real stream:")
    longest_k = max((k for k in real_rep if real_rep[k]), default=args.kmin - 1)
    shown = 0
    for k in range(longest_k, args.kmin - 1, -1):
        for kg, positions in sorted(real_rep[k].items(),
                                    key=lambda kv: kv[1][0]):
            if k < longest_k and shown >= 6:
                break
            gaps = [positions[i + 1] - positions[i]
                    for i in range(len(positions) - 1)]
            latin = g.indices_to_latin(list(kg))
            print(f"  len {k}: {latin:16s} at {positions}  gaps {gaps} "
                  f"factors {[factors(gp) for gp in gaps]}")
            shown += 1
        if shown >= 6:
            break

    print()
    if flagged:
        print(f"LEADS: k = {flagged} exceed the Smirnov null. The gaps above are "
              f"candidate key periods (Kasiski) — test them.")
    else:
        print("VERDICT: exact repeats sit at the Smirnov null at every length — "
              "coincidental, not structure. There are no Kasiski anchors, so the "
              "gap-as-key-period test is vacuous. Consistent with §4's uniformity, "
              "and it explains the community's ~5 eyeballed repeats as chance.")


if __name__ == "__main__":
    main()
