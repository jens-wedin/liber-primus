"""Exhaustive very-short key brute force, WITH the key-skip desync.

Gap this closes: `attack_vigenere_skip.py` (+ `--mangle`) covered *word* keys
and coined variants, but a real key could be a very short, meaningless run of
runes (Cicada's page-56 keystream is essentially that). Earlier work tested
short repeating keys only *without* the desync. This brutes every key of length
2..L over the 29-rune alphabet through the doublet-avoidance key-skip.

Length 1 is excluded on purpose: a constant keystream cannot advance to dodge a
doublet, so length-1 "key-skip" is degenerate (a plain shift, ruled out §3).

The catch (quantified in `probe_shortkey_id.py`): under key-skip a very short
key is barely *identifiable* — the desync gives the decoder so much per-position
freedom that many wrong short keys decode to English-looking text. A plant-and-
recover control therefore can't rank the true key #1 at L=2. So instead of
claiming a clean negative, this uses the honest test for an underpowered regime
(as `attack_keycrib.py` does for the running-key crib): brute the real segments
AND several matched-length RANDOM ciphertexts, and compare. If the real text's
best short-key decode is no better than the random "chance ceiling", the brute
has found nothing but chance — the verdict is *no signal*, not *ruled out*.

Key counts: len2 = 29^2 = 841 (cheap), len3 = 29^3 = 24,389 (large).

Usage: python3 attack_shortbrute.py [--max-len 2] [--head 30] [--draws 6]
"""

import argparse
import itertools

import gematria as g
from parse_lp import parse
from language_model import get_model
from attack_keyskip import beam_decode
from no_repeat_model import enc_key_skip
from doublet_sim import english_plaintext, LCG

N = g.N


def short_keys(min_len, max_len):
    for L in range(min_len, max_len + 1):
        for t in itertools.product(range(N), repeat=L):
            yield (g.indices_to_latin(t), list(t))


def confirm(cipher_head, key, model, sign, beam, max_skip):
    reps = len(cipher_head) * (max_skip + 1) // len(key) + 4
    sc, dec = beam_decode(cipher_head, key * reps, 0, sign, model, beam, max_skip)
    return sc / max(1, len(cipher_head) - 1), dec


def brute_best(cidx, min_len, max_len, model, head, beam, max_skip):
    """Best (trigram, key-name, sign, decode) over all short keys, both signs."""
    chead = cidx[:head]
    best = None
    for name, key in short_keys(min_len, max_len):
        for sign in (-1, +1):
            bl, dec = confirm(chead, key, model, sign, beam, max_skip)
            if best is None or bl > best[0]:
                best = (bl, name, sign, dec, key)
    return best


def chance_ceiling(min_len, max_len, model, head, beam, max_skip, draws):
    """Best short-key trigram achievable on RANDOM ciphertext — the score any
    brute reaches by pure chance at this key length and head."""
    scores = []
    for d in range(draws):
        rng = LCG(1000 + d)
        ct = [rng.randint(N) for _ in range(head)]
        bl = brute_best(ct, min_len, max_len, model, head, beam, max_skip)[0]
        scores.append(bl)
    return max(scores), sum(scores) / len(scores)


def power_note(min_len, max_len, model, head, beam, max_skip):
    """Informational: plant a random short key and see if the brute recovers it
    (it will not rank #1 at L=2 — that is the point; see probe_shortkey_id.py)."""
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:head]
    rng = LCG(20260820)
    key = [rng.randint(N) for _ in range(max_len)]
    while len(set(key)) < 2:
        key = [rng.randint(N) for _ in range(max_len)]
    reps = len(pt) * (max_skip + 1) // len(key) + 4
    ct = enc_key_skip(pt, key * reps)
    bl, name, sign, dec, rkey = brute_best(ct, min_len, max_len, model, head,
                                           beam, max_skip)
    acc = sum(1 for a, b in zip(dec, pt) if a == b) / len(pt)
    print(f"  power note: planted {g.indices_to_latin(key)}, brute's best was "
          f"{g.indices_to_latin(rkey)} ({'recovered' if rkey == key else 'a DIFFERENT key'}), "
          f"acc {acc*100:.0f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-len", type=int, default=2)
    ap.add_argument("--max-len", type=int, default=2)
    ap.add_argument("--head", type=int, default=30)
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--beam", type=int, default=100)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--draws", type=int, default=6,
                    help="random ciphertexts for the chance ceiling")
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(args.order)
    nkeys = sum(N ** L for L in range(args.min_len, args.max_len + 1))
    eng_ref = model.score_sequence(english_plaintext(segs)[:400])
    print(f"key space: {nkeys} short keys (len {args.min_len}-{args.max_len}), "
          f"both signs, key-skip max {args.max_skip}, head {args.head}")

    print("=== CHANCE CEILING (brute on random ciphertext) ===")
    power_note(args.min_len, args.max_len, model, args.head, args.beam,
               args.max_skip)
    ceil_max, ceil_avg = chance_ceiling(args.min_len, args.max_len, model,
                                        args.head, args.beam, args.max_skip,
                                        args.draws)
    print(f"  best short-key trigram on RANDOM text: max {ceil_max:.2f}, "
          f"avg {ceil_avg:.2f} over {args.draws} draws")
    print(f"  (English decode ~{eng_ref:.2f}; a real short key would beat the "
          f"ceiling clearly)\n")

    print("REAL unsolved segments (very-short key + key-skip):")
    overall = None
    for s in segs:
        if s.solved or len(s.indices) < 50:
            continue
        bl, name, sign, dec, _ = brute_best(s.indices, args.min_len,
                                            args.max_len, model, args.head,
                                            args.beam, args.max_skip)
        flag = "  <-- ABOVE CEILING" if bl > ceil_max else ""
        print(f"  {s.section[:38]:38s} key '{name}' "
              f"{('c-k' if sign < 0 else 'c+k')} trigram {bl:.2f}{flag}")
        if overall is None or bl > overall[0]:
            overall = (bl, s.section, name)
    verdict = ("SIGNAL — a segment beats the chance ceiling"
               if overall[0] > ceil_max else
               "NO SIGNAL — real best sits at the chance ceiling (underpowered)")
    print(f"\nbest real: trigram {overall[0]:.2f} on {overall[1][:30]} "
          f"(key '{overall[2]}') vs ceiling {ceil_max:.2f} -> {verdict}")


if __name__ == "__main__":
    main()
