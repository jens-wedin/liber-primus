"""Non-additive two-variable cipher functions + key-skip (N12 / Dukotah D-04).

The whole campaign assumes the cipher is ADDITIVE: c = (p + k) mod 29. mortlach's
key-drag and Dukotah's D-04 (run on only 3 of 55 pages) generalise it to an
arbitrary two-variable function c = f(p, k). For a 29-PRIME alphabet the clean,
invertible, non-additive family is the AFFINE cipher:

    c = (a * p + k) mod 29,   a in 1..28,   p = inv(a) * (c - k) mod 29

Every a is coprime to 29, so it is invertible for every rune (including ᚠ = 0,
where a pure multiplicative cipher c = p*k fails — 0 is absorbing). a = 1 is the
additive cipher this project already ruled out; a = 2..28 is a MULTIPLICATIVE
RELABEL of the plaintext that the additive attacks could not see. (Bitwise XOR is
not well-defined on 29 symbols; affine is the right generalisation here.)

Under the no-repeat rule the affine output is enciphered with the same key-skip,
so decryption is the key-skip beam with the affine inverse in place of the
subtraction. Keystreams tested: the prime and totient streams (§3) and the
thematic word keys, now under every multiplier a.

Control-validated: a planted affine + key-skip encryption must be recovered by
the matching-a beam, and a detection floor and matched ceiling gate the verdict.

Usage: python3 attack_twovar.py [--head 44] [--beam 150]
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
import math

import gematria as g
import ciphers as c
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from controls import matched_ceiling, detection_floor, verdict

N = g.N


def inv(a):
    return pow(a % N, N - 2, N)      # 29 is prime → Fermat inverse


# --- keystreams ---------------------------------------------------------------

def keystreams(length):
    out = {}
    for name, gen in (("prime", c.prime_stream), ("totient", c.totient_stream)):
        it = gen()
        out[name] = [next(it) % N for _ in range(length)]
    for w in ("DIVINITY", "FIRFUMFERENFE"):
        ix = g.latin_to_indices(w)
        out[w] = [ix[i % len(ix)] for i in range(length)]
    return out


# --- affine + key-skip --------------------------------------------------------

def enc_affine_skip(p, K, a):
    """c = a*p + K[j], pointer advances an extra step to dodge a doublet."""
    out, j = [], 0
    for pi in p:
        ci = (a * pi + K[j % len(K)]) % N
        j += 1
        while out and ci == out[-1]:
            ci = (a * pi + K[j % len(K)]) % N
            j += 1
        out.append(ci)
    return out


def beam_affine(cipher, K, a, sign, model, beam_width, max_skip):
    """Key-skip beam with the affine inverse p = inv(a)*(c - sign*k)."""
    ia = inv(a)
    SKIP_PEN = math.log(0.03)
    ctx = model.order - 1
    beams = [(0.0, 0, (), ())]
    for ci in cipher:
        nxt = []
        for score, j, hist, path in beams:
            for sk in range(max_skip + 1):
                used = j + sk
                p = (ia * ((ci - sign * K[used]) % N)) % N
                s = score + SKIP_PEN * sk + model.logscore_next(hist, p)
                nxt.append((s, used + 1, (hist + (p,))[-ctx:], path + (p,)))
        nxt.sort(key=lambda t: -t[0])
        beams = nxt[:beam_width]
    return beams[0][0], list(beams[0][3])


def attack_segment(cidx, model, head, beam, max_skip, a_range):
    chead = cidx[:head]
    Ks = keystreams(len(chead) * (max_skip + 1) + 64)
    best = None
    for kname, K in Ks.items():
        for a in a_range:
            for sign in (-1, +1):
                sc, dec = beam_affine(chead, K, a, sign, model, beam, max_skip)
                bl = sc / max(1, len(chead) - 1)
                if best is None or bl > best[0]:
                    best = (bl, kname, a, sign, dec)
    return best


# --- detection floor ----------------------------------------------------------

def calibrate(model, head, beam, max_skip):
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:head]
    plants = [("prime", 5), ("totient", 12), ("DIVINITY", 3), ("FIRFUMFERENFE", 17)]

    def plant(nm):
        kname, a = nm
        K = keystreams(head * (max_skip + 1) + 64)[kname]
        return enc_affine_skip(pt, K, a)

    def recover(ct):
        bl, kname, a, sign, dec = attack_segment(ct, model, head, beam, max_skip,
                                                  range(1, N))
        m = min(len(dec), len(pt))
        acc = sum(1 for x, y in zip(dec[:m], pt[:m]) if x == y) / m
        return bl, (kname, a), acc

    return detection_floor(plants, plant, recover, label="affine (key,a)")


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

    a_range = range(1, N)      # a = 1 (additive baseline) .. 28
    print(f"affine c = a*p + k, a in 1..{N-1}, keystreams "
          f"{list(keystreams(1))}, both signs, key-skip max {args.max_skip}\n")

    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(5)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"refs: English trigram {eng:.2f}, random {rnd:.2f}\n")

    floor, cov, unc, _ = calibrate(model, args.head, args.beam, args.max_skip)

    n_trials = len(unsolved)
    ceil = matched_ceiling(
        lambda ct: attack_segment(ct, model, args.head, args.beam,
                                  args.max_skip, a_range)[0],
        args.head, trials=n_trials, seed=909)
    print(f"=== MATCHED CHANCE CEILING ({n_trials} trials): {ceil:.2f} ===\n")

    print("=== REAL unsolved segments (best affine multiplier a, both signs) ===")
    overall = None
    for s in unsolved:
        bl, kname, a, sign, dec = attack_segment(s.indices, model, args.head,
                                                 args.beam, args.max_skip, a_range)
        if overall is None or bl > overall[0]:
            overall = (bl, s.section, kname, a)
        print(f"  {s.section[:30]:30s} {kname:13s} a={a:2d} "
              f"{'c-k' if sign<0 else 'c+k'} {bl:.2f}")

    print()
    print(f"best real: a={overall[3]} {overall[2]} on {overall[1][:30]}")
    print(verdict(overall[0], floor, ceil, n_covered=len(cov),
                  n_total=len(cov) + len(unc), label="affine keys"))


if __name__ == "__main__":
    main()
