"""Matched chance ceiling for the book-key (running-text) attack.

§31 established that this attack's noise ceiling is not a constant: it SCALES
with key-text length, because the coarse scan keeps the top-N most
English-looking offsets out of a pool that grows with the text. Blake (33k runes)
ceils at -4.01, Mabinogion (425k) at -3.92. So a raw score is meaningless until
compared with the ceiling for THAT text — which is exactly the mistake §9 made
("every real decode sits at the ~-3.95 gibberish noise floor" was never computed).

This computes it: run the identical pipeline on `--trials` random ciphertexts of
the same length, and report the max — the level pure chance reaches with this key
text and this much search freedom. Nulls come from `controls.random_runes`, a
domain-separated SHA-256 stream (never the project LCG — see §30's contaminated
ceiling).

Usage: python3 ceiling_running_text.py --key kjv [--trials 13]
"""

import argparse

import numpy as np

import keytexts
from parse_lp import parse
from language_model import get_model
from attack_running_text import trigram_table, best_over_windows
from controls import random_runes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default="kjv")
    ap.add_argument("--reverse", action="store_true")
    ap.add_argument("--trials", type=int, default=13)
    ap.add_argument("--scan-head", type=int, default=28)
    ap.add_argument("--step", type=int, default=24)
    ap.add_argument("--conf-len", type=int, default=44)
    ap.add_argument("--top", type=int, default=200)
    ap.add_argument("--beam", type=int, default=200)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--length", type=int, default=200,
                    help="ciphertext length per trial (match the real segments)")
    args = ap.parse_args()

    model = get_model(3)
    T = trigram_table(model)
    K = np.array(keytexts.get(args.key), dtype=np.int16)
    if args.reverse:
        K = K[::-1].copy()
    label = args.key + ("-reversed" if args.reverse else "")
    print(f"matched ceiling for {label} ({len(K):,} runes), "
          f"{args.trials} random ciphertexts of {args.length} runes")

    scores = []
    for t in range(args.trials):
        ct = random_runes(args.length, 9100 + t)
        bl, sign, off, w, dec = best_over_windows(
            ct, K, T, model, args.scan_head, args.step, args.conf_len,
            args.top, args.beam, args.max_skip)
        scores.append(bl)
        print(f"  trial {t + 1:2d}: {bl:.2f}")
    scores.sort()
    print(f"\n  MATCHED CEILING (max of {args.trials}): {scores[-1]:.2f}")
    print(f"  median {scores[len(scores) // 2]:.2f}, min {scores[0]:.2f}")


if __name__ == "__main__":
    main()
