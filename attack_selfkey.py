"""Self-referential running keys, searched over KEY OFFSETS (fixes §5's coverage).

§5 concluded that "the running-key hypothesis is exhausted in every form testable
without the actual external key text". The R4b audit (§31) showed that claim is
not supported by the code behind it: `attack_keycrib.py`'s Part A has **no
positive control at all**, and it hardwires every candidate key stream to start at
rune 0 (`Kx = (K + K)[...]`). Planting the hypothesis elsewhere proved the cost —
offset 0 recovers at 95% accuracy, but offsets 50 and 300 are invisible (4% and
3%). Real coverage was ~26 of ~26,000 natural hypotheses: about **0.1%**.

This re-runs the same idea with the offset actually searched, and with the
controls the original lacked:

  key streams : the solved plaintext, plus every other unsolved page's runes
                (a page is never keyed by itself — p = c - c is degenerate)
  offsets     : `--offsets` positions sampled evenly across each key stream
  signs       : both
  mechanism   : the §4 key-skip beam, identical to the original

Control-validated via `controls.py`: each (key stream, offset) hypothesis is
planted and must be recovered — that is the detection floor — and the chance
ceiling is drawn from an independent length-matched null with the SAME search
freedom, since more freedom raises the ceiling (§33). A verdict is only issued
when coverage is adequate.

Usage: python3 attack_selfkey.py [--offsets 32] [--head 60]
"""

import argparse

import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext
from attack_keyskip import beam_decode
from no_repeat_model import enc_key_skip
from controls import detection_floor, matched_ceiling, verdict

N = g.N


def key_streams(segs):
    """name -> (source_section_or_None, rune list)."""
    ks = {"solved-plaintext": (None, english_plaintext(segs))}
    for s in segs:
        if not s.solved and len(s.indices) >= 50:
            ks[f"runes:{s.section[:16]}"] = (s.section, list(s.indices))
    return ks


def offsets_for(K, n):
    """n positions spread evenly across the key stream."""
    if n <= 1:
        return [0]
    step = max(1, len(K) // n)
    return [(i * step) % len(K) for i in range(n)]


def rotated(K, off, need):
    R = K[off:] + K[:off]
    while len(R) < need:
        R = R + R
    return R[:need]


def search(ix, ks, n_off, model, beam, max_skip, exclude=None):
    """Best (score, (keyname, offset, sign), decode) over streams x offsets."""
    need = len(ix) * (max_skip + 1) + 64
    best = None
    for kname, (ksrc, K) in ks.items():
        if exclude is not None and ksrc == exclude:
            continue
        for off in offsets_for(K, n_off):
            Kx = rotated(K, off, need)
            for sign in (-1, +1):
                sc, dec = beam_decode(ix, Kx, 0, sign, model, beam, max_skip)
                bl = sc / max(1, len(ix) - 1)
                if best is None or bl > best[0]:
                    best = (bl, (kname, off, sign), dec)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offsets", type=int, default=32)
    ap.add_argument("--head", type=int, default=60)
    ap.add_argument("--beam", type=int, default=100)
    ap.add_argument("--max-skip", type=int, default=2)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(3)
    ks = key_streams(segs)
    real = [s for s in segs if not s.solved and len(s.indices) >= 50]
    n_hyp = sum(len(offsets_for(K, args.offsets)) for _, (_, K) in ks.items()) * 2
    print(f"key streams {len(ks)} x {args.offsets} offsets x 2 signs "
          f"= {n_hyp} hypotheses per segment (was 26 at offset 0 only, §31)")
    print(f"head {args.head}, beam {args.beam}, key-skip <= {args.max_skip}\n")

    # --- detection floor: plant (stream, offset) pairs and recover them ------
    pt = english_plaintext(segs)[:args.head]
    need = len(pt) * (args.max_skip + 1) + 64
    plants = []
    for kname in list(ks)[:4]:
        K = ks[kname][1]
        for off in offsets_for(K, args.offsets)[:3]:
            plants.append((kname, off))

    def plant(name):
        kname, off = name
        Kx = rotated(ks[kname][1], off, need)
        return enc_key_skip(pt, Kx)

    def recover(ct):
        sc, mech, dec = search(ct, ks, args.offsets, model, args.beam,
                               args.max_skip)
        acc = sum(1 for a, b in zip(dec, pt) if a == b) / len(pt)
        return sc, (mech[0], mech[1]), acc

    floor, covered, uncovered, _ = detection_floor(
        plants, plant, recover, label="(stream, offset)")

    # --- matched ceiling with the SAME search freedom ------------------------
    ceil = matched_ceiling(
        lambda ct: search(ct, ks, args.offsets, model, args.beam,
                          args.max_skip)[0],
        args.head, trials=len(real), seed=8800)
    print(f"=== MATCHED CHANCE CEILING (independent null, same freedom, "
          f"{len(real)} trials): {ceil:.2f} ===\n")

    print("REAL unsolved segments (self-referential key + offset search):")
    overall = None
    for s in real:
        ix = s.indices[:args.head]
        sc, mech, dec = search(ix, ks, args.offsets, model, args.beam,
                               args.max_skip, exclude=s.section)
        kname, off, sign = mech
        print(f"  {s.section[:28]:28s} {kname[:22]:22s} @{off:5d} "
              f"{'c-k' if sign < 0 else 'c+k'} {sc:6.2f}")
        if overall is None or sc > overall[0]:
            overall = (sc, s.section, kname, off, dec)
    print(f"\nbest on {overall[1][:26]} (key {overall[2]} @{overall[3]})")
    print(f"      {g.indices_to_latin(overall[4])[:76]}")
    print(verdict(overall[0], floor, ceil, len(covered), len(plants),
                  label="(stream, offset) plants"))


if __name__ == "__main__":
    main()
