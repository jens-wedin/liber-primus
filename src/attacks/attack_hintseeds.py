"""Unused-hint numerics as keystream material (N15).

Three numbers Cicada published pre-LP2 and never consumed in a puzzle step (wiki
"Possible_hints_never_used"):

  cookie167 = 6941f707ff39d259ff71657a79cb6b54c184d2f0455810109c1a960860bde0e6
  cookie761 = 7bc1e7805ccfa518920f0d94fc4e8f7dbd83287a03b337b89109cd2287befae5
  ps2012    = 1041279065...871363   (128 decimal digits)

§26 tested the cookies as the small NUMBERS 167/761 (digits, emirps, offsets) and
was negative. N6 tested THEMATIC passphrase seeds. Neither tried these specific
256-bit / 128-digit VALUES as keystream material. N15 does, three ways, each
control-validated:

  1. DIRECT keystream — the hex/decimal digits, and the raw bytes, reduced mod 29,
     tiled and offset-scanned through the key-skip beam.
  2. HASH-CTR seed — SHA-256(f"{value}:{i}") mod 29, decoded by the beam (the N6
     construction, with these values as the seed).
  3. AUTOKEY primer — the value's leading digits prime a plaintext/ciphertext
     autokey (position-locked, both signs).

Usage: python3 attack_hintseeds.py [--head 44] [--beam 150]
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
import hashlib

import gematria as g
from parse_lp import parse
from language_model import get_model
from attack_keyskip import beam_decode
from no_repeat_model import enc_key_skip
from doublet_sim import english_plaintext, LCG
from controls import matched_ceiling, detection_floor, verdict
from attack_autokey import decrypt_plaintext_autokey, decrypt_ciphertext_autokey

N = g.N

COOKIE167 = "6941f707ff39d259ff71657a79cb6b54c184d2f0455810109c1a960860bde0e6"
COOKIE761 = "7bc1e7805ccfa518920f0d94fc4e8f7dbd83287a03b337b89109cd2287befae5"
PS2012 = ("1041279065891998535982789873959431895640442510695567564373922695"
          "237268242385295908173983439037037447576486341520342349935710871363")


# --- keystream representations of a value ------------------------------------

def reps(name, value, is_hex):
    """{repr-name: finite list of rune values} for one hint value."""
    out = {}
    if is_hex:
        out[f"{name}.hexdigits"] = [int(ch, 16) % N for ch in value]
        b = bytes.fromhex(value)
        out[f"{name}.bytes"] = [x % N for x in b]
    else:
        out[f"{name}.decdigits"] = [int(ch) % N for ch in value]
        b = int(value).to_bytes((int(value).bit_length() + 7) // 8, "big")
        out[f"{name}.bytes"] = [x % N for x in b]
    return out


def hashctr(seed, n):
    return [hashlib.sha256(f"{seed}:{i}".encode()).digest()[0] % N
            for i in range(n)]


def all_keystreams(need):
    ks = {}
    for name, val, is_hex in (("c167", COOKIE167, True),
                              ("c761", COOKIE761, True),
                              ("ps", PS2012, False)):
        for rn, seq in reps(name, val, is_hex).items():
            ks[rn] = seq
        ks[f"{name}.sha_ctr"] = hashctr(val, need)
    return ks


def tile(seq, need):
    return (seq * (need // len(seq) + 1))[:need]


# --- keystream arm (key-skip beam) -------------------------------------------

def beam_best(chead, K, model, beam, max_skip, offsets):
    best = None
    for off in offsets:
        for sign in (-1, +1):
            sc, dec = beam_decode(chead, K[off:], 0, sign, model, beam, max_skip)
            bl = sc / max(1, len(chead) - 1)
            if best is None or bl > best[0]:
                best = (bl, off, sign, dec)
    return best


def attack_segment(cidx, model, head, beam, max_skip, ks, offsets):
    chead = cidx[:head]
    need = head * (max_skip + 1) + 64
    best = None
    for name, seq in ks.items():
        K = tile(seq, need + max(offsets) + 4)
        bl, off, sign, dec = beam_best(chead, K, model, beam, max_skip, offsets)
        if best is None or bl > best[0]:
            best = (bl, name, off, sign, dec)
    return best


# --- autokey-primer arm (position-locked) ------------------------------------

def best_window(seq, model, W):
    if len(seq) < W:
        return model.score_sequence(seq) if seq else -99.0
    return max(model.score_sequence(seq[s:s + W]) for s in range(len(seq) - W + 1))


def autokey_arm(cidx, model, head, primers):
    """Leading digits of each hint value as a short autokey primer."""
    chead = cidx[:head]
    best = None
    for pname, primer in primers.items():
        for dec_fn, tag in ((decrypt_plaintext_autokey, "pt"),
                            (decrypt_ciphertext_autokey, "ct")):
            for sign in (-1, +1):
                p = dec_fn(chead, primer, sign)
                sc = best_window(p, model, min(head, 40))
                if best is None or sc > best[0]:
                    best = (sc, f"{pname}/{tag}", sign)
    return best


def primers_from_values():
    pr = {}
    for name, val, is_hex in (("c167", COOKIE167, True),
                              ("c761", COOKIE761, True),
                              ("ps", PS2012, False)):
        digs = [int(ch, 16) % N for ch in val] if is_hex else \
               [int(ch) % N for ch in val]
        for L in (2, 3, 5):
            pr[f"{name}.p{L}"] = digs[:L]
    return pr


# --- control ------------------------------------------------------------------

def calibrate(model, head, beam, max_skip, ks, offsets):
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:head]
    need = head * (max_skip + 1) + 64
    names = ["c167.hexdigits", "c761.bytes", "ps.decdigits", "c167.sha_ctr"]

    def plant(nm):
        return enc_key_skip(pt, tile(ks[nm], need))

    def recover(ct):
        bl, nm, off, sign, dec = attack_segment(ct, model, head, beam, max_skip,
                                                 ks, offsets)
        m = min(len(dec), len(pt))
        acc = sum(1 for x, y in zip(dec[:m], pt[:m]) if x == y) / m
        return bl, nm, acc

    return detection_floor(names, plant, recover, label="hint keystream")


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

    need = args.head * (args.max_skip + 1) + 64
    ks = all_keystreams(need)
    offsets = [0, 8, 16, 32]
    print(f"hint keystreams ({len(ks)}): {', '.join(ks)}")
    print(f"offsets {offsets}, both signs, key-skip max {args.max_skip}\n")

    eng = model.score_sequence(english_plaintext(segs)[:400])
    print(f"refs: English trigram {eng:.2f}\n")

    floor, cov, unc, _ = calibrate(model, args.head, args.beam, args.max_skip,
                                   ks, offsets)

    ceil = matched_ceiling(
        lambda ct: attack_segment(ct, model, args.head, args.beam,
                                  args.max_skip, ks, offsets)[0],
        args.head, trials=len(unsolved), seed=1515)
    print(f"=== MATCHED CHANCE CEILING ({len(unsolved)} trials): {ceil:.2f} "
          f"===\n")

    print("=== REAL: keystream arm (digits / bytes / hash-CTR + key-skip) ===")
    overall = None
    for s in unsolved:
        bl, nm, off, sign, dec = attack_segment(s.indices, model, args.head,
                                                args.beam, args.max_skip, ks,
                                                offsets)
        if overall is None or bl > overall[0]:
            overall = (bl, s.section, nm)
        print(f"  {s.section[:30]:30s} {nm:16s} off{off:>2} "
              f"{'c-k' if sign<0 else 'c+k'} {bl:.2f}")
    print(f"  best keystream arm: {overall[2]} on {overall[1][:28]} "
          f"({overall[0]:.2f})")

    print("\n=== REAL: autokey-primer arm (leading digits, position-locked) ===")
    primers = primers_from_values()
    ak_best = None
    for s in unsolved:
        sc, tag, sign = autokey_arm(s.indices, model, args.head, primers)
        if ak_best is None or sc > ak_best[0]:
            ak_best = (sc, s.section, tag)
    print(f"  best autokey arm: {ak_best[2]} on {ak_best[1][:28]} "
          f"({ak_best[0]:.2f})")

    best_real = max(overall[0], ak_best[0])
    print()
    print(verdict(best_real, floor, ceil, n_covered=len(cov),
                  n_total=len(cov) + len(unc), label="hint keystreams"))


if __name__ == "__main__":
    main()
