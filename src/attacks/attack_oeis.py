"""Doublet-suppressing keystream families — OEIS-mod-29 & arithmetic keys (N16).

A wiki lead: an integer sequence with near-constant first differences, used as a
stream key, suppresses ciphertext doublets. This tests that two ways.

1. THE PREMISE IS REFUTED for a no-output-rule cipher, and the script shows why.
   With c = p + k position-locked, the ciphertext first difference is
   Δc = Δp + Δk. A constant-difference key (Δk = d) makes Δc = Δp + d — the
   ENGLISH difference distribution, shifted: strongly NON-uniform. But §4/§12
   measured the real Δc as uniform. So no fixed keystream applied without an
   output rule can give BOTH a uniform Δc AND the 0.66% doublet rate; that
   combination is the signature of an output-stage no-repeat rule (§4). The
   demonstration prints the contrast.

2. THE ACTIONABLE VERSION, consistent with the output rule (§4), is to add the
   OEIS-mod-29 sequences and arithmetic progressions to the keystream families
   already tried (prime/totient/word, §3), and run them through the key-skip
   beam. Control-validated with a detection floor and a matched ceiling.

Usage: python3 attack_oeis.py [--head 44] [--beam 150]
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import argparse
import collections
import math

import gematria as g
from parse_lp import parse
from language_model import get_model
from attack_keyskip import beam_decode
from no_repeat_model import enc_key_skip
from doublet_sim import english_plaintext, LCG
from controls import matched_ceiling, detection_floor, verdict

N = g.N


# --- OEIS-style sequences mod 29 ---------------------------------------------

def seq_fib(n, a=0, b=1):
    out = []
    for _ in range(n):
        out.append(a % N)
        a, b = b, a + b
    return out


def seq_linear(n, k0, d):
    return [(k0 + i * d) % N for i in range(n)]


def seq_poly(n, f):
    return [f(i) % N for i in range(n)]


def seq_bigint(n, gen):
    out, it = [], gen()
    for _ in range(n):
        out.append(next(it) % N)
    return out


def _catalan():
    c = 1
    n = 0
    while True:
        yield c
        n += 1
        c = c * 2 * (2 * n - 1) // (n + 1)


def _factorial():
    f, n = 1, 0
    while True:
        yield f
        n += 1
        f *= n


def _partition():
    # p(n) via pentagonal recurrence
    p = [1]
    n = 0
    while True:
        yield p[n]
        n += 1
        total, k = 0, 1
        while True:
            g1 = k * (3 * k - 1) // 2
            g2 = k * (3 * k + 1) // 2
            if g1 > n and g2 > n:
                break
            sign = 1 if k % 2 else -1
            if g1 <= n:
                total += sign * p[n - g1]
            if g2 <= n:
                total += sign * p[n - g2]
            k += 1
        p.append(total)


def sequences(n):
    out = {
        "fibonacci":   seq_fib(n, 0, 1),
        "lucas":       seq_fib(n, 2, 1),
        "tribonacci":  _trib(n),
        "pell":        _pell(n),
        "triangular":  seq_poly(n, lambda i: i * (i + 1) // 2),
        "squares":     seq_poly(n, lambda i: i * i),
        "pentagonal":  seq_poly(n, lambda i: i * (3 * i - 1) // 2),
        "pow2":        seq_poly(n, lambda i: pow(2, i, N)),
        "pow3":        seq_poly(n, lambda i: pow(3, i, N)),
        "catalan":     seq_bigint(n, _catalan),
        "factorial":   seq_bigint(n, _factorial),
        "partition":   seq_bigint(n, _partition),
    }
    for d in (1, 2, 3, 7):
        out[f"arith_d{d}"] = seq_linear(n, 0, d)
    return out


def _trib(n):
    a, b, c = 0, 0, 1
    out = []
    for _ in range(n):
        out.append(a % N)
        a, b, c = b, c, a + b + c
    return out


def _pell(n):
    a, b = 0, 1
    out = []
    for _ in range(n):
        out.append(a % N)
        a, b = b, 2 * b + a
    return out


# --- demonstration: constant-difference key breaks Δc uniformity -------------

def demonstrate():
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)
    un = [i for s in segs if not s.solved and len(s.indices) >= 50
          for i in s.indices]

    def dc_chi2_nonzero(seq):
        # §4's "first differences are uniform" is about the NON-ZERO differences
        # {1..28}; the 0 bin is the doublet notch and is excluded here so the two
        # rows compare like with like.
        d = [(seq[i] - seq[i - 1]) % N for i in range(1, len(seq))
             if seq[i] != seq[i - 1]]
        c = collections.Counter(d)
        e = len(d) / (N - 1)
        return sum((c.get(k, 0) - e) ** 2 / e for k in range(1, N))

    def doublet(seq):
        return sum(1 for i in range(1, len(seq)) if seq[i] == seq[i - 1]) \
            / (len(seq) - 1) * 100

    K = seq_linear(len(pt), 3, 1)               # arithmetic key, Δk = 1
    c_arith = [(pt[i] + K[i]) % N for i in range(len(pt))]
    print("=== why a doublet-suppressing keystream (no output rule) is refuted "
          "===")
    print(f"  REAL unsolved stream:          nonzero-Δc chi2 "
          f"{dc_chi2_nonzero(un):6.1f} (uniform, df 27)  doublet {doublet(un):.2f}%")
    print(f"  English + arithmetic key Δk=1:  nonzero-Δc chi2 "
          f"{dc_chi2_nonzero(c_arith):6.1f} (NON-uniform)      "
          f"doublet {doublet(c_arith):.2f}%")
    print("  The real Δc is uniform on its non-zero values with a notch at 0; a "
          "fixed\n  keystream on English instead makes Δc carry the English "
          "difference structure.\n  Only an output-stage no-repeat rule gives "
          "uniform Δc AND a 0.66% notch (§4),\n  so the brute below runs these "
          "sequences WITH the key-skip, not as a bare pad.\n")


# --- beam brute over the sequence keystreams ---------------------------------

def attack_segment(cidx, model, head, beam, max_skip, seqs):
    chead = cidx[:head]
    best = None
    for name, K in seqs.items():
        for sign in (-1, +1):
            sc, dec = beam_decode(chead, K, 0, sign, model, beam, max_skip)
            bl = sc / max(1, len(chead) - 1)
            if best is None or bl > best[0]:
                best = (bl, name, sign, dec)
    return best


def calibrate(model, head, beam, max_skip):
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:head]
    need = head * (max_skip + 1) + 64
    allseq = sequences(need)
    names = ["fibonacci", "catalan", "arith_d7", "pow2"]

    def plant(nm):
        return enc_key_skip(pt, allseq[nm])

    def recover(ct):
        bl, nm, sign, dec = attack_segment(ct, model, head, beam, max_skip,
                                            allseq)
        m = min(len(dec), len(pt))
        acc = sum(1 for x, y in zip(dec[:m], pt[:m]) if x == y) / m
        return bl, nm, acc

    return detection_floor(names, plant, recover, label="sequence key")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", type=int, default=44)
    ap.add_argument("--beam", type=int, default=150)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--order", type=int, default=3)
    args = ap.parse_args()
    model = get_model(args.order)
    segs = parse("data/liber_primus.md")
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]

    demonstrate()

    need = args.head * (args.max_skip + 1) + 64
    seqs = sequences(need)
    print(f"keystream sequences ({len(seqs)}): {', '.join(seqs)}\n")

    floor, cov, unc, _ = calibrate(model, args.head, args.beam, args.max_skip)

    ceil = matched_ceiling(
        lambda ct: attack_segment(ct, model, args.head, args.beam,
                                  args.max_skip, seqs)[0],
        args.head, trials=len(unsolved), seed=1616)
    print(f"=== MATCHED CHANCE CEILING ({len(unsolved)} trials): {ceil:.2f} "
          f"===\n")

    print("=== REAL unsolved segments (best sequence key + key-skip) ===")
    overall = None
    for s in unsolved:
        bl, nm, sign, dec = attack_segment(s.indices, model, args.head,
                                           args.beam, args.max_skip, seqs)
        if overall is None or bl > overall[0]:
            overall = (bl, s.section, nm)
        print(f"  {s.section[:30]:30s} {nm:12s} "
              f"{'c-k' if sign<0 else 'c+k'} {bl:.2f}")

    print(f"\nbest real: {overall[2]} on {overall[1][:30]}")
    print(verdict(overall[0], floor, ceil, n_covered=len(cov),
                  n_total=len(cov) + len(unc), label="sequence keys"))


if __name__ == "__main__":
    main()
