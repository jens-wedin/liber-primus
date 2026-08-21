"""P3.7 — the "possible hints never used" numeric sequences as keys/primers.

Uncovering-Cicada's "Possible hints never used" collects numeric sequences from
the 2012-2015 puzzles that were never applied to Liber Primus:
  - 2012 OutGuess (vjuNp.jpg) whitespace: 0,2,3,5,7,11,13,1,1,2,11,0,7,0,5,0,3,2
  - 2014 message.txt.asc whitespace:     2,3,5,7,11,13,17,23,29,31,37 (skips 19)
  - cookies of p7amjopgric7dfdi.onion:   167, 761 (an emirp pair; both are in the
    "missing primes" list below)
  - "missing primes on telnet": the primes between 71 and 1229 absent from the
    printed list — 73,79,...,1223.

Low prior (these are pre-LP2 artifacts), but bounded and testable: run each as a
repeating key, and 167/761 as start-offsets into the prime/totient keystream,
through the SAME validated key-skip beam as the word-key and magic-square attacks
(CIRCUMFERENCE positive control + a random-text chance ceiling).

Usage: python3 attack_hints.py [--head 30] [--beam 100]
"""

import argparse

import gematria as g
import ciphers as c
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from attack_vigenere_skip import attack_segment, positive_control

N = g.N


def primes_between(lo, hi):
    out, n = [], lo + 1
    while n < hi:
        if all(n % d for d in range(2, int(n ** 0.5) + 1)) and n > 1:
            out.append(n)
        n += 1
    return out


def materialize(gen, length):
    vals, it = [], gen()
    for _ in range(length):
        vals.append(next(it) % N)
    return vals


def build_keys(head, max_skip):
    keys = []

    def add(name, vals):
        ix = [v % N for v in vals]
        if len(ix) >= 2:
            keys.append((name, ix))

    add("ws2012", [0, 2, 3, 5, 7, 11, 13, 1, 1, 2, 11, 0, 7, 0, 5, 0, 3, 2])
    add("ws2014", [2, 3, 5, 7, 11, 13, 17, 23, 29, 31, 37])
    add("cookie_digits", [1, 6, 7, 7, 6, 1])
    add("cookies_mod29", [167, 761])
    add("missing_primes", primes_between(71, 1229))

    # 167/761 as START OFFSETS into the prime/totient keystreams
    span = (max_skip + 1) * head + 64
    for sname, gen in [("prime", c.prime_stream), ("tot", c.totient_stream)]:
        full = materialize(gen, 800 + span)
        for off in (167, 761):
            add(f"{sname}@{off}", full[off:off + span])
    return keys


def chance_ceiling(keys, model, head, beam, max_skip, draws):
    best = None
    for d in range(draws):
        rng = LCG(1300 + d)
        ct = [rng.randint(N) for _ in range(head + 4)]
        sc = attack_segment(ct, keys, model, head, beam, max_skip)[0]
        best = sc if best is None else max(best, sc)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", type=int, default=30)
    ap.add_argument("--beam", type=int, default=100)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--draws", type=int, default=6)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(3)
    keys = build_keys(args.head, args.max_skip)
    eng = model.score_sequence(english_plaintext(segs)[:400])

    print(f"hint-derived keys ({len(keys)}):")
    for name, k in keys:
        print(f"  {name:16s} len {len(k):3d}: {g.indices_to_latin(k)[:34]}")
    print(f"\nEnglish trigram ref {eng:.2f}\n")

    ctrl = keys + [("CIRCUMFERENCE", g.latin_to_indices("CIRCUMFERENCE"))]
    if not positive_control(ctrl, model, args.head, args.beam, args.max_skip):
        print("control FAILED — not trusting the run.")
        return

    ceil = chance_ceiling(keys, model, args.head, args.beam, args.max_skip,
                          args.draws)
    print(f"=== CHANCE CEILING (these keys on random text): {ceil:.2f} ===\n")

    print("REAL unsolved segments (hint keys + key-skip):")
    overall = None
    for s in segs:
        if s.solved or len(s.indices) < 50:
            continue
        bl, name, sign, dec, _ = attack_segment(
            s.indices, keys, model, args.head, args.beam, args.max_skip)
        flag = "  <-- ABOVE CEILING" if bl > ceil else ""
        print(f"  {s.section[:30]:30s} key '{name}' "
              f"{('c-k' if sign < 0 else 'c+k')} trigram {bl:.2f}{flag}")
        if overall is None or bl > overall[0]:
            overall = (bl, s.section, name)
    signal = overall[0] > eng - 0.5 and overall[0] > ceil + 0.5
    verdict = ("SIGNAL — inspect" if signal else
               "NO SIGNAL — gibberish, no better than chance")
    print(f"\nbest: trigram {overall[0]:.2f} on {overall[1][:26]} "
          f"(key '{overall[2]}') vs ceiling {ceil:.2f}, English {eng:.2f} "
          f"-> {verdict}")


if __name__ == "__main__":
    main()
