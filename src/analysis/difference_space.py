"""Difference-space attack on d[i] = (c[i] - c[i-1]) mod 29 (REPORT §5.2).

Motivation. The whole fingerprint — c uniform, first differences uniform with a
notch at 0 (REPORT §4, §11) — is exactly what a CUMULATIVE / chained cipher
produces:

    c[i] = (c[i-1] + m[i]) mod 29 ,   with m[i] != 0      (the notch)

Under that reading the meaningful stream is the difference itself,
d[i] = c[i] - c[i-1] = m[i]; and if m[i] = p[i] + k[i], then d IS an ordinary
keystream cipher of the plaintext. §4 already ruled out the KEYLESS cumulative
case (m = p, so d would be English — it is not: d has IoC 1.02). This tests the
KEYED case: attack d with the keystream battery — a repeating-key Vigenere
shows up as a periodic-IoC bump ON d; a prime/totient stream is recovered by
subtracting it from d and reading English.

Every path is gated by a control that plants a cumulative cipher of known
English under a known key and confirms the difference-space attack recovers it,
so a negative on the real text is meaningful.

Usage: python3 difference_space.py [--pmax 40]
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

import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import ioc, english_plaintext, LCG
import ciphers as c

N = g.N


def diff(ix):
    return [(ix[i] - ix[i - 1]) % N for i in range(1, len(ix))]


def periodic_ioc(seq, P):
    if len(seq) < 2 * P:
        return 0.0
    return sum(ioc(seq[i::P]) for i in range(P)) / P


def best_period(seq, pmax):
    best = (0.0, 1)
    for P in range(1, pmax + 1):
        v = periodic_ioc(seq, P)
        if v > best[0]:
            best = (v, P)
    return best


def stream_vals(gen_fn, n):
    out, it = [], gen_fn()
    for _ in range(n):
        out.append(next(it) % N)
    return out


def keystream_recover(d, kvals, sign, start):
    return [(d[i] - sign * kvals[i + start]) % N for i in range(len(d))]


def enc_cumulative(p, k, avoid_zero=False, rng=None):
    """c[i] = (c[i-1] + p[i] + k[i]) mod N, seed 0. avoid_zero models the notch
    by forbidding m = p+k == 0."""
    out, prev = [], 0
    for i in range(len(p)):
        m = (p[i] + k[i]) % N
        if avoid_zero and m == 0:
            m = 1 + (rng.randint(N - 1) if rng else 0)
        prev = (prev + m) % N
        out.append(prev)
    return out


# --- controls ----------------------------------------------------------------

def control_vigenere(model, pt, eng_ref, pmax):
    """Plant a cumulative-Vigenere cipher; differencing must expose the period
    as a periodic-IoC bump and key-subtraction must recover English."""
    P = 7
    key = [3, 17, 5, 22, 9, 14, 1]
    krep = [key[i % P] for i in range(len(pt))]
    ct = enc_cumulative(pt, krep)
    d = diff(ct)
    val, per = best_period(d, pmax)
    krep_d = [key[(i + 1) % P] for i in range(len(d))]      # d is m[1:]
    rec = [(d[i] - krep_d[i]) % N for i in range(len(d))]
    tri = model.score_sequence(rec)
    ok = (per % P == 0 or P % per == 0) and val > 1.4 and tri > eng_ref - 0.3
    print(f"  cumulative-Vigenere (period {P}): d best periodic-IoC {val:.2f} "
          f"@ period {per}; key-subtract trigram {tri:.2f}")
    print(f"    control: {'PASS' if ok else 'FAIL'}")
    return ok


def control_prime(model, pt, eng_ref):
    """Plant a cumulative-prime cipher; subtracting the prime stream from d must
    recover English."""
    kvals = stream_vals(c.prime_stream, len(pt) + 4)
    ct = enc_cumulative(pt, kvals[:len(pt)])
    d = diff(ct)
    kv = stream_vals(c.prime_stream, len(d) + 4)
    best = None
    for start in (0, 1, 2):
        rec = keystream_recover(d, kv, +1, start)
        tri = model.score_sequence(rec)
        if best is None or tri > best[0]:
            best = (tri, start)
    ok = best[0] > eng_ref - 0.3
    print(f"  cumulative-prime: best key-subtract trigram {best[0]:.2f} "
          f"@ start {best[1]}")
    print(f"    control: {'PASS' if ok else 'FAIL'}")
    return ok


# --- real attack -------------------------------------------------------------

def attack_stream(d, gen_fn, model):
    kv = stream_vals(gen_fn, len(d) + 4)
    best = None
    for sign in (-1, +1):
        for start in (0, 1, 2):
            rec = keystream_recover(d, kv, sign, start)
            tri = model.score_sequence(rec)
            if best is None or tri > best[0]:
                best = (tri, sign, start)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pmax", type=int, default=40)
    ap.add_argument("--order", type=int, default=3)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(args.order)
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]
    pt = english_plaintext(segs)

    eng = model.score_sequence(pt[:400])
    rng = LCG(11)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    eng_ioc = ioc(pt[:2000])
    print(f"refs: English trigram {eng:.2f}, random {rnd:.2f}; "
          f"English IoC {eng_ioc:.2f}, random ~1.00\n")

    print("=== CONTROLS: plant a cumulative cipher, recover it in diff-space ===")
    ok1 = control_vigenere(model, pt[:1200], eng, args.pmax)
    ok2 = control_prime(model, pt[:1200], eng)
    if not (ok1 and ok2):
        print("\ncontrols FAILED — not trusting the real run.")
        return
    print()

    # whole-corpus difference stream statistics
    alld = [x for s in unsolved for x in diff(s.indices)]
    val, per = best_period(alld, args.pmax)
    dtri = model.score_sequence(alld)
    print("=== REAL difference stream d = c[i]-c[i-1] ===")
    print(f"  d-IoC {ioc(alld):.3f} (random ~1.00, English ~{eng_ioc:.2f})")
    print(f"  best periodic-IoC {val:.2f} @ period {per} "
          f"(>1.3 would flag a cumulative-Vigenere period)")
    print(f"  d read as plaintext: trigram {dtri:.2f} "
          f"(keyless cumulative — English would be ~{eng:.2f})\n")

    print("  keystream subtraction on d (cumulative + fixed keystream):")
    overall = dtri
    for name, gen in [("prime", c.prime_stream), ("totient", c.totient_stream)]:
        results = []
        for s in unsolved:
            d = diff(s.indices)
            tri, sign, start = attack_stream(d, gen, model)
            results.append((tri, s.section, sign, start))
        b = max(results)
        overall = max(overall, b[0])
        print(f"    {name:8s} best trigram {b[0]:.2f} on {b[1][:30]} "
              f"({'d-k' if b[2] < 0 else 'd+k'}, start {b[3]})")

    print(f"\n  verdict: best diff-space decode trigram {overall:.2f} vs "
          f"English {eng:.2f}, random {rnd:.2f}")
    print("  -> " + ("LEAD — a diff-space decode reaches English!"
                     if overall > eng - 0.4 else
                     "negative: the difference stream is as random as the raw "
                     "stream; cumulative-Vigenere and cumulative prime/totient "
                     "are ruled out."))


if __name__ == "__main__":
    main()
