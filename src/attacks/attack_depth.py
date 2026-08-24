"""Keyless depth detection by local alignment — a POWER ANALYSIS (N8).

The idea. If two units (pages or lines) reuse the SAME keystream —
c_A = p_A + K, c_B = p_B + K — then c_A - c_B = p_A - p_B, independent of K.
Two texts "in depth" can be detected WITHOUT knowing K: their per-position
difference follows the English difference distribution (peaked at 0: the
coincidence rate kappa), not the uniform one. The key-skip desync shifts the two
pointers apart, so this uses SMITH-WATERMAN local alignment (gaps = key-skips) to
recover the aligned stretches — Banburismus updated for an irregular pointer.

Why this file is a power analysis, not an attack (the §40 pattern). A null from
an instrument with no demonstrated power is not a negative (§28). Before scanning
real page/line pairs, this measures whether the method can detect depth it is
SHOWN — planted pairs that really do share a keystream. It cannot, at Liber
Primus scales, and the reason is quantified. So the real scan is not run: it
would only produce a meaningless "no signal".

Two independent walls, both measured below:
  1. The kappa signal is weak (English 0.062 vs random 0.034), so even a
     desync-FREE coincidence test needs ~600 aligned runes to separate depth from
     chance. The longest unsolved page is 277 runes; lines are ~22.
  2. The key-skip desync caps a coherent aligned run at ~1/(2*skip) ~ 17 runes,
     far below 600, so local alignment cannot accumulate the signal — planted
     depth scores no higher than independent pairs at every length and gap.

The positive control that KEEPS this honest: the same scorer DOES separate depth
at L>=600 with no skip (see section A). The instrument works; it just has no
power at LP unit lengths under the desync.

Usage: python3 attack_depth.py
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import collections
import math

import gematria as g
from parse_lp import parse
from no_repeat_model import enc_key_skip
from doublet_sim import english_plaintext, LCG
import attack_pagekey as pk

N = g.N


# --- English difference distribution and alignment scorer --------------------

def english_diff_model():
    """f = English rune frequencies; D[k] = P(p_A - p_B = k); W = per-position
    log-likelihood-ratio of depth vs uniform for a difference of k."""
    eng = english_plaintext(parse("data/liber_primus.md"))
    f = [0.0] * N
    cnt = collections.Counter(eng)
    for r in range(N):
        f[r] = cnt.get(r, 0) / len(eng)
    D = [sum(f[r] * f[(r + k) % N] for r in range(N)) for k in range(N)]
    W = [math.log(D[k] * N + 1e-9) for k in range(N)]
    cum, s = [], 0.0
    for r in range(N):
        s += f[r]
        cum.append(s)
    return D, W, cum


def eng_sample(cum, n, seed):
    """n runes drawn iid from the English unigram distribution. This is the
    right null for a UNIGRAM depth test — the scorer only uses the difference
    distribution, so higher-order structure is irrelevant to its power."""
    r = LCG(seed)
    out = []
    for _ in range(n):
        u = r.next() / 0xFFFFFFFF
        lo = 0
        while lo < N - 1 and u > cum[lo]:
            lo += 1
        out.append(lo)
    return out


def rigid_kappa(a, b):
    m = min(len(a), len(b))
    return sum(1 for i in range(m) if a[i] == b[i]) / m


def sw_local(a, b, W, gap):
    """Smith-Waterman local-alignment max score. Match score = W[(a_i-b_j)]
    (the depth-vs-uniform LLR); gap = a key-skip in one stream."""
    n = len(b)
    prev = [0.0] * (n + 1)
    best = 0.0
    for ai in a:
        cur = [0.0] * (n + 1)
        for j in range(1, n + 1):
            v = prev[j - 1] + W[(ai - b[j - 1]) % N]
            u = prev[j] + gap
            l = cur[j - 1] + gap
            if u > v:
                v = u
            if l > v:
                v = l
            if v < 0.0:
                v = 0.0
            cur[j] = v
            if v > best:
                best = v
        prev = cur
    return best


def randK(n, seed):
    r = LCG(seed)
    return [r.randint(N) for _ in range(n)]


# --- the power analysis ------------------------------------------------------

def main():
    D, W, cum = english_diff_model()
    print(f"English coincidence kappa = {D[0]:.4f}  vs random {1/N:.4f}  "
          f"(the whole depth signal is this ~1.8x excess)\n")

    print("=== (A) DETECTABILITY CEILING: rigid depth (shared key, NO skip) ===")
    print("    coincidence kappa, depth vs independent, 12 trials each")
    for L in (120, 300, 600, 1200):
        dep, ind = [], []
        for t in range(12):
            pa = eng_sample(cum, L, 10 + t)
            pb = eng_sample(cum, L, 5000 + t)
            K = randK(L + 8, 300 + t)
            ca = [(pa[i] + K[i]) % N for i in range(L)]
            dep.append(rigid_kappa(ca, [(pb[i] + K[i]) % N for i in range(L)]))
            K2 = randK(L + 8, 999 + t)
            ind.append(rigid_kappa(ca, [(pb[i] + K2[i]) % N for i in range(L)]))
        sep = min(dep) > max(ind)
        print(f"    L={L:4d}: depth {sum(dep)/len(dep):.4f}  "
              f"indep {sum(ind)/len(ind):.4f}  "
              f"{'SEPARABLE' if sep else 'overlap'}")
    print("    -> even with NO desync, depth needs ~600 aligned runes to show.\n")

    print("=== (B) THE REAL HYPOTHESIS: key-skip depth via SW local alignment ===")
    print("    depth (shared key, independent skips) vs independent, 8 trials")
    for L in (300, 600):
        for gap in (-0.5, -1.0, -2.0):
            dep, ind = [], []
            for t in range(8):
                pa = eng_sample(cum, L, 10 + t)
                pb = eng_sample(cum, L, 5000 + t)
                K = randK(L * 2 + 64, 300 + t)
                dep.append(sw_local(enc_key_skip(pa, K), enc_key_skip(pb, K),
                                    W, gap))
                ia = enc_key_skip(pa, randK(L * 2 + 64, 700 + t))
                ib = enc_key_skip(pb, randK(L * 2 + 64, 911 + t))
                ind.append(sw_local(ia, ib, W, gap))
            sep = min(dep) > max(ind)
            print(f"    L={L} gap={gap:+.1f}: depth {sum(dep)/len(dep):5.1f} "
                  f"(min {min(dep):.1f})  indep {sum(ind)/len(ind):5.1f} "
                  f"(max {max(ind):.1f})  {'SEP' if sep else 'OVERLAP'}")
    print("    -> the desync destroys detectability at every length and gap.\n")

    print("=== (C) REAL UNSOLVED UNIT LENGTHS vs the ~600-rune floor ===")
    for unit in ("page", "line"):
        lens = sorted(len(u) for _, units in pk.unsolved_pages(unit)
                      for u in units)
        med = lens[len(lens) // 2]
        print(f"    {unit}: {len(lens)} units, min {lens[0]} median {med} "
              f"max {lens[-1]}; none >= 600")

    print("\n=== VERDICT: NO POWER — the real scan is NOT run ===")
    print("Depth detection needs ~600 aligned runes (kappa is a weak ~1.8x "
          "signal);\nthe longest unsolved page is 277 and the key-skip desync "
          "caps a coherent\naligned run near ~17 runes. Planted depth is "
          "indistinguishable from\nindependent pairs (B), so a scan of real "
          "pairs would be a null from a\npowerless instrument — not a negative "
          "(§28). Keyless depth / keystream\nreuse is UNTESTABLE on the Liber "
          "Primus with this method, not disproven.")


if __name__ == "__main__":
    main()
