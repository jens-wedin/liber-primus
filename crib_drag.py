"""Crib-dragging against the unsolved Liber Primus sections.

Exploits two constraints that survive encryption:

1. Word boundaries (the • separators) are preserved, so a multi-word crib
   only fits where the ciphertext's word-length pattern matches exactly.
2. The literal-ᚠ rule: wherever the crib has a plaintext F, the ciphertext
   must show ᚠ, and that position consumes no key. This makes F-bearing
   cribs strong filters.

For every legal (crib, word-offset) placement we derive the implied
keystream k = (c − p) mod 29 and test it for structure:

- constant (local shift cipher) or arithmetic progression;
- short repeating period → candidate Vigenère key, which is then extended
  over the whole segment and scored for English;
- contiguous match inside prime-family sequences (pⱼ mod 29, φ(pⱼ) mod 29,
  starting at any prime index) — the page-56 scheme generalized;
- English-ness of the keystream itself read as runes (running key drawn
  from an English text), ranked by a bigram model built from the solved
  pages' plaintext.

Usage: python3 crib_drag.py [--top N]
"""

import argparse
import itertools
import math
from collections import Counter

import ciphers as c
import gematria as g
from parse_lp import parse

N = g.N

# Cicada vocabulary and Liber Primus phraseology. Multi-word cribs give the
# word-length filter teeth; F-bearing words add the literal-ᚠ filter.
CRIBS = [
    "A KOAN",
    "A PARABLE",
    "AN INSTRUCTION",
    "SOME WISDOM",
    "KNOW THIS",
    "AN END",
    "THE LOSS OF DIVINITY",
    "THE PRIMES ARE SACRED",
    "THE TOTIENT FUNCTION IS SACRED",
    "ALL THINGS SHOULD BE ENCRYPTED",
    "WELCOME PILGRIM TO THE",
    "THE CIRCUMFERENCE",
    "CIRCUMFERENCE",
    "CIRCUMFERENCES",
    "ENLIGHTENMENT",
    "INTELLIGENCE",
    "SUFFERING",
    "STRUGGLE AND SUFFERING",
    "YOUR OWN SELF",
    "WITHIN THE DEEP WEB",
    "COMMAND YOUR OWN SELF",
    "DISCOVER TRUTH INSIDE YOURSELF",
    "THE MASTER",
    "THE STUDENT",
    "IMPOSE NOTHING ON OTHERS",
    "PROGRAM YOUR MIND",
    "PROGRAM REALITY",
    "THE INSTAR",
    "EMERGENCE",
    "PRESERVATION",
    "ADHERENCE",
    "SHED OUR OWN CIRCUMFERENCES",
]


def build_bigram_model(segs):
    """log P(b|a) with add-half smoothing, from solved plaintext streams."""
    stream = []
    for s in segs:
        if not s.solved:
            continue
        if "Substitution with default" in s.key or s.key.startswith("-"):
            stream.extend(s.indices)
        elif "reversed Gematria" in s.key and "Shift 3" in s.key:
            stream.extend(c.shift(c.atbash(s.indices), 3))
    counts = Counter(zip(stream, stream[1:]))
    uni = Counter(stream)
    model = {}
    for a in range(N):
        denom = uni.get(a, 0) + 0.5 * N
        for b in range(N):
            model[(a, b)] = math.log((counts.get((a, b), 0) + 0.5) / denom)
    return model


def bigram_logprob(ix, model):
    if len(ix) < 2:
        return 0.0
    return sum(model[(a, b)] for a, b in zip(ix, ix[1:])) / (len(ix) - 1)


def prime_family_tables(limit=3000):
    ps = []
    gen = c.prime_stream()
    for _ in range(limit):
        ps.append(next(gen))
    return {
        "prime mod 29": [p % N for p in ps],
        "phi(prime) mod 29": [(p - 1) % N for p in ps],
    }


def find_subsequence(hay, needle):
    L = len(needle)
    for i in range(len(hay) - L + 1):
        if hay[i:i + L] == needle:
            return i
    return -1


def short_period(ks, max_period=13):
    for p in range(1, min(max_period, len(ks) // 2) + 1):
        if all(ks[i] == ks[i % p] for i in range(len(ks))):
            return p
    return None


def is_ap(ks):
    if len(ks) < 3:
        return False
    d = (ks[1] - ks[0]) % N
    return all((b - a) % N == d for a, b in zip(ks, ks[1:]))


def derive_keystream(crib_flat, cipher_flat):
    """Return implied keystream (None if the literal-ᚠ rule is violated).
    Positions where the crib has F must be ᚠ and yield no key value."""
    ks = []
    for p, ci in zip(crib_flat, cipher_flat):
        if p == 0:
            if ci != 0:
                return None
            continue
        ks.append((ci - p) % N)
    return ks


def extend_vigenere(seg, key, phase, model):
    """Score decrypting the whole segment with a candidate repeating key.
    phase = key offset at the segment's first rune."""
    ix = seg.indices
    dec = [(ci - key[(phase + i) % len(key)]) % N for i, ci in enumerate(ix)]
    latin_words = [g.indices_to_latin(w) for w in
                   c.decrypt_words(seg.words, lambda flat: [
                       (ci - key[(phase + i) % len(key)]) % N
                       for i, ci in enumerate(flat)])]
    return bigram_logprob(dec, model), c.word_score(latin_words)


def selftest():
    """Prove the dragger works: drag known cribs over SOLVED ciphertexts and
    require the documented keys to fall out."""
    segs = parse("data/liber_primus.md")
    ok = True

    # Page 03: "WELCOME PILGRIM TO THE" must yield a period-8 rotation of
    # DIVINITY (phase 7: the 7-rune header consumed key positions 0-6).
    s = next(x for x in segs if x.section.startswith("03.jpg"))
    cwords = [g.latin_to_indices(w) for w in "WELCOME PILGRIM TO THE".split()]
    wl = [len(w) for w in s.words]
    cl = [len(w) for w in cwords]
    start = next(i for i in range(len(wl)) if wl[i:i + len(cl)] == cl)
    cflat = [i for w in cwords for i in w]
    cipher_flat = [i for w in s.words[start:start + len(cl)] for i in w]
    ks = derive_keystream(cflat, cipher_flat)
    p = short_period(ks)
    key = g.indices_to_latin(ks[:p]) if p else None
    expect = g.indices_to_latin(g.latin_to_indices("YDIVINIT"))
    print(f"selftest 03.jpg: crib at word {start}, period {p}, key {key} "
          f"(expect {expect})")
    ok &= key == expect

    # Page 73/56: "WITHIN THE DEEP WEB" must match phi(prime) mod 29 at
    # prime index 5 (the five runes of "AN END" consumed the first five phi values).
    s = next(x for x in segs if x.section.startswith("73.jpg"))
    cwords = [g.latin_to_indices(w) for w in "WITHIN THE DEEP WEB".split()]
    wl = [len(w) for w in s.words]
    cl = [len(w) for w in cwords]
    start = next(i for i in range(len(wl)) if wl[i:i + len(cl)] == cl)
    cflat = [i for w in cwords for i in w]
    cipher_flat = [i for w in s.words[start:start + len(cl)] for i in w]
    # page-56 encrypts c = p + phi, so the implied key here is (c-p) = +phi
    ks = derive_keystream(cflat, cipher_flat)
    j = find_subsequence(prime_family_tables()["phi(prime) mod 29"], ks)
    print(f"selftest 73.jpg: crib at word {start}, phi(prime) match at "
          f"prime index {j} (expect 5)")
    ok &= j == 5

    print("selftest:", "PASS" if ok else "FAIL")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=15,
                    help="how many English-key candidates to print")
    ap.add_argument("--min-runes", type=int, default=8,
                    help="minimum derived-keystream length to consider")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        raise SystemExit(0 if selftest() else 1)

    segs = parse("data/liber_primus.md")
    model = build_bigram_model(segs)
    tables = prime_family_tables()
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]

    crib_words = {crib: [g.latin_to_indices(w) for w in crib.split()]
                  for crib in CRIBS}

    placements = 0
    structural_hits = []
    english_candidates = []

    for s in unsolved:
        words = s.words
        wl = [len(w) for w in words]
        for crib, cwords in crib_words.items():
            cl = [len(w) for w in cwords]
            cflat = [i for w in cwords for i in w]
            if sum(cl) - cflat.count(0) < args.min_runes:
                continue
            for start in range(len(words) - len(cwords) + 1):
                if wl[start:start + len(cl)] != cl:
                    continue
                cipher_flat = [i for w in words[start:start + len(cl)] for i in w]
                ks = derive_keystream(cflat, cipher_flat)
                if ks is None:
                    continue
                placements += 1
                where = f"{s.section[:36]} @word {start}"

                if len(set(ks)) == 1:
                    structural_hits.append(
                        (f"CONSTANT shift {ks[0]}", crib, where, ks))
                elif is_ap(ks):
                    structural_hits.append(
                        (f"ARITH.PROG. step {(ks[1]-ks[0]) % N}", crib, where, ks))
                p = short_period(ks)
                if p and p <= len(ks) // 2:
                    key = ks[:p]
                    phase_guess = 0  # unknown true phase; test all
                    best = max(
                        (extend_vigenere(s, key, ph, model), ph)
                        for ph in range(p))
                    (bl, ws), ph = best
                    structural_hits.append(
                        (f"PERIOD {p} key={g.indices_to_latin(key)} "
                         f"ext(bigram {bl:.2f}, words {ws:.2f})",
                         crib, where, ks))
                for tname, table in tables.items():
                    j = find_subsequence(table, ks)
                    if j >= 0:
                        structural_hits.append(
                            (f"MATCHES {tname} at prime index {j}",
                             crib, where, ks))
                english_candidates.append(
                    (bigram_logprob(ks, model), crib, where, ks))

    print(f"legal placements examined: {placements}")
    print(f"\n=== structural hits ({len(structural_hits)}) ===")
    for tag, crib, where, ks in structural_hits:
        print(f"  [{tag}] crib '{crib}' at {where}")
        print(f"     key: {g.indices_to_latin(ks)}")

    english_candidates.sort(reverse=True)
    rnd = -math.log(N)
    print(f"\n=== top English-looking keystreams "
          f"(bigram logprob; random baseline {rnd:.2f}) ===")
    for lp, crib, where, ks in english_candidates[:args.top]:
        print(f"  {lp:6.2f}  '{crib}' at {where}")
        print(f"          key reads: {g.indices_to_latin(ks)}")


if __name__ == "__main__":
    main()
