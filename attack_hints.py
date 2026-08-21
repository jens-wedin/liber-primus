"""P3.7 — the "possible hints never used" numeric sequences as keys/primers.

Uncovering-Cicada's "Possible hints never used" collects numeric sequences from
the 2012-2015 puzzles that were never applied to Liber Primus:
  - 2012 OutGuess (vjuNp.jpg) whitespace: 0,2,3,5,7,11,13,1,1,2,11,0,7,0,5,0,3,2
  - 2014 message.txt.asc whitespace:     2,3,5,7,11,13,17,23,29,31,37 (skips 19)
  - cookies of p7amjopgric7dfdi.onion:   167, 761 (an emirp pair)
  - "missing primes on telnet": the primes the printed list skips between 71 and
    1229, i.e. 73..1223. NB this set is *mathematically* the standard prime
    keystream offset by 20 (prime_stream[20:200]), so it is NOT independent
    evidence — §3 already covers the prime stream. It is kept for completeness
    and labelled accordingly.

METHOD NOTE (added after an audit found the original verdict rule broken).
The first version declared a break only if the best score beat `English - 0.5`.
That rule is wrong for this pipeline: planting these very keys into English and
recovering them at 97-100% accuracy yields scores as low as -4.00, *below* that
threshold — i.e. the script would have printed "NO SIGNAL" on a total break. The
score is not comparable to a plain English trigram because `beam_decode`
normalises by len-1 and adds a per-skip penalty.

So the decision threshold is now CALIBRATED EMPIRICALLY: we plant each candidate
key into English (+ key-skip), recover it through the identical pipeline, and
record the score. The minimum score over keys that genuinely self-recover is the
**detection floor** — the score a real break with these keys would produce. The
real run is negative only if it lands clearly BELOW that floor. Keys that do not
rank first when planted are reported as NOT COVERED (non-identifiable), not as
negatives. Identifiability (does the true key rank first?) is the criterion —
decode accuracy is reported separately, since an imperfect decode of the correct
key still produces the score we would observe.

Usage: python3 attack_hints.py [--head 30] [--beam 100]
"""

import argparse

import gematria as g
import ciphers as c
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from no_repeat_model import enc_key_skip
from attack_vigenere_skip import attack_segment
from controls import detection_floor, matched_ceiling, verdict

N = g.N


def primes_between(lo, hi):
    out, n = [], lo + 1
    while n < hi:
        if n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1)):
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
    # == prime_stream[20:200]; kept for completeness, not independent of §3
    add("missing_primes(=primes@20)", primes_between(71, 1229))

    span = (max_skip + 1) * head + 64
    for sname, gen in [("prime", c.prime_stream), ("tot", c.totient_stream)]:
        full = materialize(gen, 800 + span)
        for off in (167, 761):
            add(f"{sname}@{off}", full[off:off + span])
    return keys


def hints_floor(keys, model, head, beam, max_skip):
    """Detection floor via the shared `controls` helper.

    NB an earlier version of this function required BOTH a name match and >90%
    plaintext accuracy, which wrongly demoted keys that were correctly ranked
    first but decoded imperfectly (e.g. ws2012 at 70%). Identifiability — does
    the true key rank first? — is what decides whether we would see a break, so
    that alone defines the floor; accuracy is reported separately.
    """
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:head]
    kmap = dict(keys)

    def plant(name):
        k = kmap[name]
        reps = len(pt) * (max_skip + 1) // len(k) + 4
        return enc_key_skip(pt, k * reps)

    def recover(ct):
        sc, nm, sign, dec, _ = attack_segment(ct, keys, model, head, beam, max_skip)
        acc = sum(1 for a, b in zip(dec, pt) if a == b) / len(pt)
        return sc, nm, acc

    return detection_floor([n for n, _ in keys], plant, recover, label="hint key")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", type=int, default=30)
    ap.add_argument("--beam", type=int, default=100)
    ap.add_argument("--max-skip", type=int, default=2)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(3)
    keys = build_keys(args.head, args.max_skip)
    real_segs = [s for s in segs if not s.solved and len(s.indices) >= 50]

    print(f"hint-derived keys ({len(keys)}):")
    for name, k in keys:
        print(f"  {name:26s} len {len(k):3d}: {g.indices_to_latin(k)[:30]}")
    print()

    floor, covered, uncovered, _ = hints_floor(
        keys, model, args.head, args.beam, args.max_skip)

    score_fn = lambda ct: attack_segment(ct, keys, model, args.head,
                                         args.beam, args.max_skip)[0]
    ceil = matched_ceiling(score_fn, args.head, trials=len(real_segs),
                           seed=1300, extra=4)
    print(f"=== CHANCE CEILING (max over {len(real_segs)} random texts, matched "
          f"to the {len(real_segs)} real segments): {ceil:.2f} ===\n")

    print("REAL unsolved segments (hint keys + key-skip):")
    overall = None
    for s in real_segs:
        bl, name, sign, dec, _ = attack_segment(
            s.indices, keys, model, args.head, args.beam, args.max_skip)
        flag = "  <-- above ceiling" if bl > ceil else ""
        print(f"  {s.section[:30]:30s} key '{name:26s}' "
              f"{('c-k' if sign < 0 else 'c+k')} {bl:6.2f}{flag}")
        if overall is None or bl > overall[0]:
            overall = (bl, s.section, name)

    print(f"\nbest on {overall[1][:26]} (key '{overall[2]}')")
    print(verdict(overall[0], floor, ceil, len(covered), len(keys),
                  label="hint keys"))


if __name__ == "__main__":
    main()
