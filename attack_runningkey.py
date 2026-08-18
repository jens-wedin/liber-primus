"""Running-key attack that needs no key text.

A running-key cipher is c = p + k (mod 29) where BOTH the plaintext p and the
key k are drawn from natural-language text. So the correct decomposition is
the one that makes *both* streams look like English at once. We beam-search
over plaintext hypotheses p; each fixes k[i] = c[i] - p[i]; the score rewards
English bigrams in p AND in k simultaneously (same model, since the key is
also English-in-runes). No candidate key text is required — this tests the
running-key hypothesis against every possible English key at once.

Because the no-repeat mechanism may desync the key by ~3% (see
no_repeat_model.py), an optional skip lets the key pointer jump; but for a
running key the desync only mildly breaks key-side bigram continuity, so the
skip mostly matters for the key term and we keep the model simple.

Calibration is the point: we run the identical decoder on (a) a genuine
running-key ciphertext built from English, and (b) the real unsolved
segments, and compare the achieved joint-bigram scores. If the real text is
running-key, its score sits near the genuine sample's; if it is a uniform
pad, its score sits near the random floor.

Usage: python3 attack_runningkey.py [--beam 800] [--head 120]
"""

import argparse
import math

import ciphers as c
import gematria as g
from parse_lp import parse
from crib_drag import build_bigram_model

N = g.N


def beam_running_key(cipher, model, beam_width):
    """Beam search maximizing bigram(p) + bigram(k), k[i]=c[i]-p[i]."""
    # state: (score, prev_p, prev_k, path)
    beams = [(0.0, None, None, ())]
    for ci in cipher:
        nxt = []
        for score, pp, pk, path in beams:
            for pi in range(N):
                ki = (ci - pi) % N
                s = score
                if pp is not None:
                    s += model[(pp, pi)] + model[(pk, ki)]
                nxt.append((s, pi, ki, path + (pi,)))
        nxt.sort(key=lambda t: -t[0])
        beams = nxt[:beam_width]
    best = beams[0]
    return best[0] / max(1, len(cipher) - 1), list(best[3])


def make_running_key_sample(segs, length):
    """Build a genuine running-key ciphertext from two disjoint slices of the
    solved English-in-runes plaintext (calibration positive control)."""
    from doublet_sim import english_plaintext
    pt = english_plaintext(segs)
    p = pt[:length]
    k = pt[length:length + length]
    while len(k) < length:  # wrap if short
        k += pt
    k = k[:length]
    ct = [(pi + ki) % N for pi, ki in zip(p, k)]
    return ct, p


def word_score_from(words, flat):
    out, pos = [], 0
    for w in words:
        out.append(g.indices_to_latin(flat[pos:pos + len(w)]))
        pos += len(w)
    return c.word_score(out), " ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--beam", type=int, default=800)
    ap.add_argument("--head", type=int, default=120)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = build_bigram_model(segs)
    rnd = -math.log(N)

    # --- calibration: genuine running-key + a uniform-random control --------
    sample_ct, sample_pt = make_running_key_sample(segs, args.head)
    rk_score, rk_dec = beam_running_key(sample_ct, model, args.beam)
    acc = sum(1 for a, b in zip(rk_dec, sample_pt) if a == b) / len(sample_pt)
    from doublet_sim import LCG
    rng = LCG(12345)
    rand_ct = [rng.randint(N) for _ in range(args.head)]
    rand_score, _ = beam_running_key(rand_ct, model, args.beam)

    print("CALIBRATION (same decoder, known inputs):")
    print(f"  random floor        : joint-bigram {rnd*2:.2f} (2x unigram)")
    print(f"  uniform-random text : joint-bigram {rand_score:.2f}")
    print(f"  genuine running key : joint-bigram {rk_score:.2f}  "
          f"(recovered {acc*100:.0f}% of plaintext)")
    threshold = (rand_score + rk_score) / 2
    separation = rk_score - rand_score
    powered = separation > 0.25
    print(f"  => genuine-vs-random separation {separation:.2f} — "
          f"test is {'DISCRIMINATING' if powered else 'UNDERPOWERED'}")
    if not powered:
        print("  !! WARNING: the decoder produces English-looking bigrams from")
        print("     random input too, so scores near the genuine-running-key")
        print("     value are NOT evidence of running key. Treat results below")
        print("     as inconclusive, not positive.\n")
    else:
        print()

    print("REAL unsolved segments:")
    hits = []
    for s in segs:
        if s.solved or len(s.indices) < 50:
            continue
        ix = s.indices[:args.head]
        hwords, n = [], 0
        for w in s.words:
            if n + len(w) <= len(ix):
                hwords.append(w); n += len(w)
            else:
                break
        sc, dec = beam_running_key(ix, model, args.beam)
        ws, text = word_score_from(hwords, dec)
        flag = "  <== above threshold" if sc > threshold else ""
        print(f"  {s.section[:42]:42s} joint-bigram {sc:.2f} words {ws:.2f}{flag}")
        print(f"      {text[:100]}")
        hits.append((sc, ws, s.section))

    best = max(hits)
    print(f"\nbest: joint-bigram {best[0]:.2f}, words {best[1]:.2f} "
          f"({best[2][:36]})")
    print(f"genuine running key scored {rk_score:.2f}; "
          f"real segments top out at {best[0]:.2f}")
    if not powered:
        print("\nCONCLUSION: inconclusive. With genuine-vs-random separation "
              f"only {separation:.2f}, this method cannot confirm or exclude a "
              "running key at these lengths. A real running-key attack needs a "
              "specific candidate key text (crib the key), trigram+ models over "
              "full-length pages, or a known-plaintext anchor.")


if __name__ == "__main__":
    main()
