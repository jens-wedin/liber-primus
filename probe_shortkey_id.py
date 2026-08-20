"""Identifiability probe: can a very-short key be recovered under key-skip?

Before brute-forcing short keys (`attack_shortbrute.py`) it is worth asking
whether a short key is even *identifiable* once the doublet-avoidance key-skip
is in play. The key-skip lets the decoder choose 0..max_skip extra key
advances per position, which is a lot of freedom relative to a 2- or 3-rune
key — so many wrong short keys can be bent to look English.

This measures it directly: plant a random length-L key, encrypt English with
key-skip, then score the TRUE key and `nrand` random length-L keys through the
same key-skip beam. The true key's rank among the random ones (rank 1 = it
beats them all) is the identifiability. A rank far above 1 means a full brute
would surface chance keys, i.e. the brute is underpowered at that length.

Result (see results/shortkey_id_2026-08-20.txt): at head 30 the true key ranks
~6/1500 at L=2 (NOT identifiable), ~2 at L=3-4, ~1 at L=5; a longer head (60)
pulls L=3-4 to rank ~1 but leaves L=2 at ~6. Since brute force is only feasible
at L=2-3 and identifiability only arrives at L>=5, short-key brute + key-skip
cannot decisively test very-short keys — the same intrinsic underpowerment the
running-key attack hit (REPORT.md §4).

Usage: python3 probe_shortkey_id.py [--nrand 800] [--trials 3]
"""

import argparse
import random

import gematria as g
from parse_lp import parse
from language_model import get_model
from attack_keyskip import beam_decode
from no_repeat_model import enc_key_skip
from doublet_sim import english_plaintext

N = g.N


def score_key(model, ct, key, head, beam, max_skip=2):
    """Best trigram (over both signs) for decoding ct[:head] with `key`."""
    reps = head * (max_skip + 1) // len(key) + 4
    best = None
    for sign in (-1, +1):
        sc, dec = beam_decode(ct[:head], key * reps, 0, sign, model, beam, max_skip)
        bl = sc / max(1, head - 1)
        if best is None or bl > best[0]:
            best = (bl, sign, dec)
    return best


def probe(model, pt_full, L, head, beam, nrand, trials, rng):
    pt = pt_full[:head]
    ranks, accs = [], []
    for _ in range(trials):
        key = [rng.randint(0, N - 1) for _ in range(L)]
        while len(set(key)) < 2:                 # constant key can't key-skip
            key = [rng.randint(0, N - 1) for _ in range(L)]
        reps = head * 3 // len(key) + 4
        ct = enc_key_skip(pt, key * reps)
        tb = score_key(model, ct, key, head, beam)
        accs.append(sum(1 for a, b in zip(tb[2], pt) if a == b) / len(pt))
        beaten = sum(1 for _ in range(nrand)
                     if score_key(model, ct,
                                  [rng.randint(0, N - 1) for _ in range(L)],
                                  head, beam)[0] >= tb[0])
        ranks.append(beaten + 1)
    return ranks, accs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nrand", type=int, default=800,
                    help="random distractor keys per trial")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--beam", type=int, default=100)
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    model = get_model(args.order)
    pt = english_plaintext(parse("data/liber_primus.md"))
    rng = random.Random(args.seed)

    def line(L, head):
        ranks, accs = probe(model, pt, L, head, args.beam, args.nrand,
                            args.trials, rng)
        import statistics as st
        print(f"L={L} head={head} beam={args.beam}: true-key rank "
              f"~{st.mean(ranks):.0f}/{args.nrand} (want 1), acc "
              f"~{st.mean(accs)*100:.0f}% | trials {ranks}")

    print(f"identifiability of length-L keys under key-skip "
          f"({args.nrand} distractors x {args.trials} trials):")
    for L in (2, 3, 4, 5, 6):
        line(L, 30)
    print("--- longer head (more constraint per key value) ---")
    for L in (2, 3, 4):
        line(L, 60)


if __name__ == "__main__":
    main()
