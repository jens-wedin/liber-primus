"""Beam-search attack on the key-skip hypothesis.

If the unsolved cipher is a fixed keystream K (primes or totients, mod 29)
whose pointer advances an extra step to avoid emitting a doublet (the
mechanism whose statistical signature matches the data — see
no_repeat_model.py), then a naive Vigenere decode desynchronises at every
hidden skip. But the skips are ~3% of positions, so a beam search over
{0,1,2 skips} per position, scored by an English n-gram model, can resync
and recover the plaintext IF this is the real scheme.

This directly tests "known prime-family keystream + doublet-avoidance
interrupter". A negative result rules that family out; a positive one breaks
the page. Either way it is a real, decisive test rather than blind search.

Usage: python3 attack_keyskip.py [--beam 200] [--max-skip 2]
"""

import argparse
import math

import ciphers as c
import gematria as g
from parse_lp import parse
from language_model import get_model

N = g.N


def keystreams(length):
    out = {}
    for name, gen in [("prime", c.prime_stream), ("totient", c.totient_stream)]:
        vals, it = [], gen()
        for _ in range(length + 64):
            vals.append(next(it) % N)
        out[name] = vals
    return out


def beam_decode(cipher, K, start, sign, model, beam_width, max_skip):
    """Return (best_score, plaintext_indices). sign=-1: p=c-K; +1: p=c+K.
    Plaintext is scored with the n-gram model (limited search freedom — only
    the per-position skip count is chosen — so the model discriminates well)."""
    SKIP_PEN = math.log(0.03)  # skips are rare; penalise choosing them
    ctx = model.order - 1
    # state: (score, pointer, hist_tuple, path_tuple)
    beams = [(0.0, start, (), ())]
    for ci in cipher:
        nxt = []
        for score, j, hist, path in beams:
            for sk in range(max_skip + 1):
                used = j + sk
                p = (ci + sign * K[used]) % N
                s = score + (SKIP_PEN * sk) + model.logscore_next(hist, p)
                nxt.append((s, used + 1, (hist + (p,))[-ctx:], path + (p,)))
        nxt.sort(key=lambda t: -t[0])
        beams = nxt[:beam_width]
    best = beams[0]
    return best[0], list(best[3])


def score_words(cipher_words, plaintext_flat):
    out, pos = [], 0
    for w in cipher_words:
        out.append(g.indices_to_latin(plaintext_flat[pos:pos + len(w)]))
        pos += len(w)
    return c.word_score(out), " ".join(out)


def selftest(model):
    """Encrypt known English with prime key-skip, then confirm the beam
    decoder recovers it — proving the attack works when the hypothesis holds."""
    from no_repeat_model import enc_key_skip
    from doublet_sim import english_plaintext
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:120]
    K = keystreams(len(pt) * 2)["prime"]
    ct = enc_key_skip(pt, K)
    _, dec = beam_decode(ct, K, 0, -1, model, beam_width=400, max_skip=2)
    n = min(len(dec), len(pt))
    acc = sum(1 for a, b in zip(dec[:n], pt[:n]) if a == b) / n
    print(f"selftest: prime key-skip round-trip, beam recovered {acc*100:.0f}% "
          f"of {n} runes")
    return acc > 0.9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--beam", type=int, default=300)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--head", type=int, default=200,
                    help="analyze only the first N runes of each segment "
                         "(enough to detect English; 0 = whole segment)")
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--max-start", type=int, default=200,
                    help="how far into the keystream to try starting. The "
                         "original code looped `range(N)` — using the ALPHABET "
                         "SIZE (29) as a keystream-offset bound, which is a "
                         "category error. An audit planted prime-index starts "
                         "0/10/28/40 (all found) and 120 (MISSED), so the old "
                         "negative covered starts ~0-50 only.")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(args.order)

    if args.selftest:
        raise SystemExit(0 if selftest(model) else 1)

    print(f"selftest first: ", end="")
    ok = selftest(model)
    if not ok:
        raise SystemExit("selftest FAILED — the beam cannot recover a planted "
                         "key-skip stream, so any negative below would be "
                         "meaningless. Aborting (audit: controls must GATE).")
    print()

    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]
    from doublet_sim import LCG, english_plaintext
    rng = LCG(7)
    rand_ref = model.score_sequence([rng.randint(N) for _ in range(400)])
    eng_ref = model.score_sequence(english_plaintext(segs)[:400])
    print(f"order-{args.order} model refs: English decode ~{eng_ref:.2f}, "
          f"random ~{rand_ref:.2f} (a real break lands near English)\n")
    best_overall = None
    for s in unsolved:
        ix = s.indices if not args.head else s.indices[:args.head]
        # word list truncated to the same head length, for word-scoring
        hwords, n = [], 0
        for w in s.words:
            if n + len(w) <= len(ix):
                hwords.append(w)
                n += len(w)
            else:
                break
        Ks = keystreams(len(ix) * (args.max_skip + 1) + 128)
        best = None
        for kname, K in Ks.items():
            for sign in (-1, +1):
                for start in range(args.max_start):
                    sc, dec = beam_decode(ix, K, start, sign, model,
                                          args.beam, args.max_skip)
                    bl = sc / max(1, len(ix) - 1)
                    if best is None or bl > best[0]:
                        ws, text = score_words(hwords, dec)
                        best = (bl, kname, sign, start, ws, text)
        bl, kname, sign, start, ws, text = best
        print(f"{s.section[:44]:44s} best {kname}{'+' if sign>0 else '-'} "
              f"start {start:2d}: score {bl:.2f} words {ws:.2f}")
        print(f"    {text[:110]}")
        if best_overall is None or ws > best_overall[0]:
            best_overall = (ws, s.section)
    print(f"\nbest word-score across all segments: {best_overall[0]:.2f} "
          f"({best_overall[1][:40]}) — English decode would be >0.3")


if __name__ == "__main__":
    main()
