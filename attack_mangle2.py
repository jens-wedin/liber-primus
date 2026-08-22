"""§8 remainder: COMPOSED (two-transform) coined key words.

§8 tested single-transform coined keys — one consonant collapse (the
FIRFUMFERENFE = CIRCUMFERENCE family), atbash, rune reversal, or vowel rotation —
and left composed manglings untested. A setter who coined FIRFUMFERENFE went one
substitution deep; nothing says they stopped there.

`mangle.mangle2()` composes a letter-level transform with a second letter- or
index-level one, deduped against the base words and the single-transform set:
250 variants of the Cicada vocabulary.

Honest expectation, from §31's audit of this exact pipeline: the §7/§8 word-key
search has a **detection floor of about -4.00 against a matched chance ceiling of
about -4.01** — the score a genuine break produces and the level pure noise
reaches are the same number. So this test has almost no operating margin, and a
"negative" from it is weak by construction. We compute both numbers and say so
rather than quoting a bare verdict.

Usage: python3 attack_mangle2.py [--head 30]
"""

import argparse

import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext
from no_repeat_model import enc_key_skip
from attack_vigenere_skip import attack_segment, CICADA_WORDS
from mangle import mangle2_words
from controls import detection_floor, matched_ceiling, verdict

N = g.N


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", type=int, default=30)
    ap.add_argument("--beam", type=int, default=100)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--plants", type=int, default=12)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(3)
    keys = [(n, ix) for n, ix in mangle2_words(CICADA_WORDS)
            if 4 <= len(ix) <= 16]
    real = [s for s in segs if not s.solved and len(s.indices) >= 50]
    print(f"composed (two-transform) coined keys: {len(keys)}")
    print(f"  e.g. {', '.join(n for n, _ in keys[:4])}\n")

    pt = english_plaintext(segs)[:args.head]
    kmap = dict(keys)
    plants = [n for n, _ in keys[:args.plants]]

    def plant(name):
        k = kmap[name]
        reps = len(pt) * (args.max_skip + 1) // len(k) + 4
        return enc_key_skip(pt, k * reps)

    def recover(ct):
        sc, nm, sign, dec, _ = attack_segment(ct, keys, model, args.head,
                                              args.beam, args.max_skip)
        acc = sum(1 for a, b in zip(dec, pt) if a == b) / len(pt)
        return sc, nm, acc

    floor, covered, uncovered, _ = detection_floor(
        plants, plant, recover, label="composed key")

    ceil = matched_ceiling(
        lambda ct: attack_segment(ct, keys, model, args.head, args.beam,
                                  args.max_skip)[0],
        args.head, trials=len(real), seed=9900, extra=4)
    print(f"=== MATCHED CHANCE CEILING ({len(real)} trials): {ceil:.2f} ===")
    if floor is not None:
        print(f"  operating margin (floor - ceiling): {floor - ceil:+.2f} nats "
              f"— §31 measured ~0.01 for this pipeline, i.e. almost none\n")

    overall = None
    for s in real:
        sc, nm, sign, dec, _ = attack_segment(s.indices, keys, model,
                                              args.head, args.beam,
                                              args.max_skip)
        print(f"  {s.section[:30]:30s} '{nm[:26]:26s}' "
              f"{'c-k' if sign < 0 else 'c+k'} {sc:6.2f}")
        if overall is None or sc > overall[0]:
            overall = (sc, s.section, nm, dec)
    print(f"\nbest on {overall[1][:26]} ('{overall[2]}')")
    print(f"      {g.indices_to_latin(overall[3])[:76]}")
    print(verdict(overall[0], floor, ceil, len(covered), len(plants),
                  label="composed keys"))


if __name__ == "__main__":
    main()
