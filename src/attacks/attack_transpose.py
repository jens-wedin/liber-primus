"""Ciphertext orientation / transposition search (N3, mortlach).

mortlach's enumerable space is {interrupter} × {gematria rotation} × {atbash} ×
{L2R/R2L transposition} × {cipher function}. Most of it collapses onto ground we
have already covered, and the collapse is worth stating:

  * A GEMATRIA ROTATION (a monoalphabetic shift of the 29-ring) is absorbed into
    the additive key for an index-space cipher c = p + k — it adds nothing beyond
    §3/§48. (It would only bite a prime-VALUE cipher, a niche not tested here.)
  * ATBASH (i -> 28-i) is the affine multiplier a = 28, already swept in §48/N12.
  * "L2R/R2L transposition" is a READING DIRECTION, not an arbitrary reordering.
    Arbitrary rune transposition is un-searchable for the Liber Primus: it
    preserves unigram frequencies and our bigrams are flat (§4), so there is no
    statistical handle to find the right permutation — unlike Zodiac Z340, whose
    period-19 bigram spike revealed its transposition. So only the enumerable
    reading-direction / reflection cases are testable.

What is genuinely NEW, then, is running the keystream + key-skip battery on the
ciphertext in each ORIENTATION — forward, reversed, atbash, atbash+reversed — a
high-prior variant (Cicada uses reversed gematria on solved pages) that our
attacks only ever applied to the KEY texts (§32/§36), never to the ciphertext.
All four transforms are involutions, so the control plants an encryption already
put into that orientation and confirms the attack recovers it.

Control-validated through controls.py.

Usage: python3 attack_transpose.py [--head 44] [--beam 150]
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
import ciphers as c
from parse_lp import parse
from language_model import get_model
from attack_keyskip import beam_decode
from no_repeat_model import enc_key_skip
from doublet_sim import english_plaintext, LCG
from controls import matched_ceiling, detection_floor, verdict

N = g.N


# --- orientations (all involutions) ------------------------------------------

def orient(seq, name):
    if name == "fwd":
        return list(seq)
    if name == "rev":
        return list(seq)[::-1]
    if name == "atbash":
        return [N - 1 - x for x in seq]
    if name == "atbash_rev":
        return [N - 1 - x for x in seq][::-1]
    raise ValueError(name)


ORIENTS = ("fwd", "rev", "atbash", "atbash_rev")


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


def attack_segment(cidx, model, head, beam, max_skip, starts):
    best = None
    need = head * (max_skip + 1) + 64
    Ks = keystreams(need + max(starts) + 4)
    for oname in ORIENTS:
        chead = orient(cidx[:head], oname)
        for kname, K in Ks.items():
            for sign in (-1, +1):
                for st in starts:
                    sc, dec = beam_decode(chead, K, st, sign, model, beam,
                                          max_skip)
                    bl = sc / max(1, len(chead) - 1)
                    if best is None or bl > best[0]:
                        best = (bl, oname, kname, sign, st, dec)
    return best


# --- control ------------------------------------------------------------------

def calibrate(model, head, beam, max_skip, starts):
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:head]
    need = head * (max_skip + 1) + 64
    Ks = keystreams(need)
    # plant: encrypt English with a keystream + key-skip, then put the ciphertext
    # INTO an orientation; the attack must recover it (orientations are involutions)
    plants = [("fwd", "prime"), ("rev", "totient"),
              ("atbash", "DIVINITY"), ("atbash_rev", "FIRFUMFERENFE")]

    def plant(nm):
        oname, kname = nm
        ct = enc_key_skip(pt, Ks[kname])
        return orient(ct, oname)

    def recover(ct):
        bl, oname, kname, sign, st, dec = attack_segment(ct, model, head, beam,
                                                         max_skip, starts)
        m = min(len(dec), len(pt))
        acc = sum(1 for x, y in zip(dec[:m], pt[:m]) if x == y) / m
        return bl, (oname, kname), acc

    return detection_floor(plants, plant, recover, label="(orientation,key)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", type=int, default=44)
    ap.add_argument("--beam", type=int, default=150)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--max-start", type=int, default=1)
    args = ap.parse_args()
    model = get_model(args.order)
    segs = parse("data/liber_primus.md")
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]
    starts = list(range(args.max_start))

    print(f"orientations {ORIENTS} x keystreams {list(keystreams(1))} x 2 signs "
          f"x {len(starts)} starts, key-skip max {args.max_skip}")
    print("note: gematria rotation is absorbed into the additive key; atbash is "
          "the §48\naffine a=28; arbitrary transposition is un-searchable (flat "
          "bigrams, §4). Only\nreading-direction / reflection orientations are "
          "testable.\n")

    eng = model.score_sequence(english_plaintext(segs)[:400])
    print(f"refs: English trigram {eng:.2f}\n")

    floor, cov, unc, _ = calibrate(model, args.head, args.beam, args.max_skip,
                                   starts)

    ceil = matched_ceiling(
        lambda ct: attack_segment(ct, model, args.head, args.beam,
                                  args.max_skip, starts)[0],
        args.head, trials=len(unsolved), seed=303)
    print(f"=== MATCHED CHANCE CEILING ({len(unsolved)} trials): {ceil:.2f} "
          f"===\n")

    print("=== REAL unsolved segments (best orientation + keystream) ===")
    overall = None
    by_orient = {}
    for s in unsolved:
        bl, oname, kname, sign, st, dec = attack_segment(s.indices, model,
                                                         args.head, args.beam,
                                                         args.max_skip, starts)
        by_orient[oname] = by_orient.get(oname, 0) + 1
        if overall is None or bl > overall[0]:
            overall = (bl, s.section, oname, kname)
        print(f"  {s.section[:30]:30s} {oname:11s} {kname:13s} "
              f"{'c-k' if sign<0 else 'c+k'} {bl:.2f}")

    print(f"\n  winning orientation tally: {by_orient}")
    print(f"  best real: {overall[2]} + {overall[3]} on {overall[1][:28]}")
    print(verdict(overall[0], floor, ceil, n_covered=len(cov),
                  n_total=len(cov) + len(unc), label="(orientation,key)"))


if __name__ == "__main__":
    main()
