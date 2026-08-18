"""Autokey attack on the unsolved sections.

Motivation: the unsolved ciphertext shows a strong doublet deficiency
(adjacent identical runes at ~0.66% vs 3.45% expected for a flat stream, a
~17-sigma anomaly). A keystream *derived from the text itself* (autokey) is
one of the few simple schemes that couples adjacent ciphertext runes and can
push the doublet rate away from 1/29 — so it's worth brute-forcing short
primers even though the community has covered much of this ground.

Tries plaintext-autokey and ciphertext-autokey, both signs, primer lengths
1-2 everywhere (and 3 on small segments). Scores by chi-square against the
English rune distribution learned from the solved pages, with a common-word
check on survivors.
"""

import itertools

import ciphers as c
import gematria as g
from analyze_unsolved import chi2, english_rune_distribution
from parse_lp import parse

N = g.N


def decrypt_ciphertext_autokey(ix, primer, sign):
    L = len(primer)
    out = []
    for i, ci in enumerate(ix):
        k = primer[i] if i < L else ix[i - L]
        out.append((ci + sign * k) % N)
    return out


def decrypt_plaintext_autokey(ix, primer, sign):
    L = len(primer)
    out = []
    for i, ci in enumerate(ix):
        k = primer[i] if i < L else out[i - L]
        out.append((ci + sign * k) % N)
    return out


def main():
    segs = parse("data/liber_primus.md")
    dist = english_rune_distribution(segs)
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]

    for s in unsolved:
        ix = s.indices
        head = ix[:150]
        results = []
        max_len = 3 if len(ix) <= 400 else 2
        for L in range(1, max_len + 1):
            for primer in itertools.product(range(N), repeat=L):
                for fn in (decrypt_ciphertext_autokey, decrypt_plaintext_autokey):
                    for sign in (+1, -1):
                        dec = fn(head, primer, sign)
                        results.append((chi2(dec, dist), fn.__name__, primer, sign))
        results.sort(key=lambda t: t[0])
        print(f"-- {s.section[:50]} n={len(ix)} "
              f"(random-head chi2 baseline ~{chi2(head, dist):.0f})")
        for sc, name, primer, sign in results[:3]:
            fn = (decrypt_ciphertext_autokey if name.startswith("decrypt_c")
                  else decrypt_plaintext_autokey)
            dec_words = c.decrypt_words(s.words, lambda i: fn(i, primer, sign))
            latin = [g.indices_to_latin(w) for w in dec_words]
            ws = c.word_score(latin)
            print(f"   chi2={sc:6.0f} {name.replace('decrypt_', ''):18s} "
                  f"primer={primer} sign={sign:+d} word-score={ws:.2f}")
            if ws > 0.15:
                print("   CANDIDATE:", " ".join(latin)[:200])


if __name__ == "__main__":
    main()
