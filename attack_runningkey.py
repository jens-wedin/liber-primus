"""Running-key attack that needs no key text, now with an n-gram model.

A running-key cipher is c = p + k (mod 29) where BOTH the plaintext p and the
key k are natural-language text. The correct decomposition makes both streams
look like English at once. We beam-search plaintext hypotheses p; each fixes
k[i] = c[i] - p[i]; the score rewards English n-grams in p AND in k
simultaneously. No candidate key text is needed.

The language model is now the frequency-weighted n-gram model from
language_model.py (order 2/3/4), which separates English from random far
better than the old LP-only bigram model — the power the earlier bigram
version lacked. Calibration (genuine running-key vs uniform-random, same
decoder) is printed so the verdict is self-checking.

Usage: python3 attack_runningkey.py [--order 3] [--beam 800] [--head 120]
"""

import argparse

import ciphers as c
import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import LCG, english_plaintext

N = g.N


def beam_running_key(cipher, model, beam_width):
    o = model.order
    ctx = o - 1
    # state: (score, p_hist tuple, k_hist tuple, path)
    beams = [(0.0, (), (), ())]
    for ci in cipher:
        nxt = []
        for score, ph, kh, path in beams:
            for pi in range(N):
                ki = (ci - pi) % N
                s = (score + model.logscore_next(ph, pi)
                     + model.logscore_next(kh, ki))
                nxt.append((s, (ph + (pi,))[-ctx:], (kh + (ki,))[-ctx:],
                            path + (pi,)))
        nxt.sort(key=lambda t: -t[0])
        beams = nxt[:beam_width]
    best = beams[0]
    return best[0] / max(1, len(cipher) - 1), list(best[3])


def make_running_key_sample(segs, length):
    pt = english_plaintext(segs)
    p = pt[:length]
    k = (pt[length:] + pt)[:length]
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
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--beam", type=int, default=800)
    ap.add_argument("--head", type=int, default=120)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(args.order)

    sample_ct, sample_pt = make_running_key_sample(segs, args.head)
    rk_score, rk_dec = beam_running_key(sample_ct, model, args.beam)
    acc = sum(1 for a, b in zip(rk_dec, sample_pt) if a == b) / len(sample_pt)
    rng = LCG(12345)
    rand_ct = [rng.randint(N) for _ in range(args.head)]
    rand_score, _ = beam_running_key(rand_ct, model, args.beam)

    sep = rk_score - rand_score
    powered = sep > 0.5
    print(f"CALIBRATION (order-{args.order} model, beam {args.beam}, "
          f"head {args.head}):")
    print(f"  uniform-random text : {rand_score:.2f}")
    print(f"  genuine running key : {rk_score:.2f}  "
          f"(recovered {acc*100:.0f}% of plaintext)")
    print(f"  separation {sep:.2f} -> test is "
          f"{'DISCRIMINATING' if powered else 'UNDERPOWERED'}")
    threshold = rand_score + 0.5 * sep
    if not powered:
        print("  !! still underpowered; treat below as inconclusive.\n")
    else:
        print(f"  decision threshold ~{threshold:.2f}\n")

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
        flag = "  <== ABOVE THRESHOLD" if powered and sc > threshold else ""
        print(f"  {s.section[:42]:42s} score {sc:.2f} words {ws:.2f}{flag}")
        print(f"      {text[:100]}")
        hits.append((sc, ws, s.section, text))

    best = max(hits)
    print(f"\nbest: score {best[0]:.2f}, words {best[1]:.2f} ({best[2][:36]})")
    print(f"genuine running key calibrated at {rk_score:.2f}")
    if powered:
        above = [h for h in hits if h[0] > threshold]
        if above:
            print(f"{len(above)} segment(s) above threshold — inspect decodes "
                  f"for real words (word-score should climb toward 0.3+).")
        else:
            print("No segment reaches the genuine-running-key band. With a "
                  "now-discriminating test, this is real evidence AGAINST a "
                  "simple running key on these pages.")
    else:
        print("Inconclusive: raise --order/--beam/--head, or crib a specific "
              "key text.")


if __name__ == "__main__":
    main()
