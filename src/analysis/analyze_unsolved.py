"""Statistical analysis + simple-attack battery for the unsolved Liber Primus
sections.

What this measures and why:

- Index of coincidence (IoC, normalized so random=1.0): English written in
  runes lands around 1.7-1.8; a flat ~1.0 means every simple substitution
  (incl. any single fixed rune mapping) is ruled out.
- Periodic IoC: if a repeating key of period p were used (Vigenère-style),
  taking every p-th rune would restore high IoC at that period.
- Doublet rate: fraction of adjacent identical runes. Random expects 1/29.
- Attack battery: every shift x direction x atbash combination, prime and
  totient keystreams (both signs, with and without treating ᚠ as a literal),
  scored against an English model built from the *solved* pages' plaintext.
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

from collections import Counter

import ciphers as c
import gematria as g
from parse_lp import parse


def ioc(indices):
    n = len(indices)
    if n < 2:
        return 0.0
    counts = Counter(indices)
    return g.N * sum(v * (v - 1) for v in counts.values()) / (n * (n - 1))


def periodic_ioc(indices, period):
    cols = [indices[i::period] for i in range(period)]
    vals = [ioc(col) for col in cols if len(col) > 1]
    return sum(vals) / len(vals) if vals else 0.0


def doublet_rate(indices):
    n = len(indices)
    return sum(1 for a, b in zip(indices, indices[1:]) if a == b) / (n - 1)


def english_rune_distribution(segs):
    """Unigram distribution of rune indices in the solved pages' plaintext."""
    counts = Counter()
    for s in segs:
        if not s.solved:
            continue
        if "Substitution with default" in s.key or s.key.startswith("-"):
            counts.update(s.indices)
        elif "reversed Gematria" in s.key and "Shift 3" in s.key:
            counts.update(c.shift(c.atbash(s.indices), 3))
    total = sum(counts.values())
    return [counts.get(i, 0.5) / total for i in range(g.N)]


def chi2(indices, dist):
    n = len(indices)
    counts = Counter(indices)
    return sum((counts.get(i, 0) - n * dist[i]) ** 2 / (n * dist[i])
               for i in range(g.N))


def attack_battery(seg, dist):
    """Try every simple decryption; return candidates sorted by fit."""
    ix = seg.indices
    words = seg.words
    cands = []

    def consider(name, fn):
        dec = c.decrypt_words(words, fn)
        flat = [i for w in dec for i in w]
        latin_words = [g.indices_to_latin(w) for w in dec]
        cands.append((chi2(flat, dist), c.word_score(latin_words), name,
                      " ".join(latin_words)[:90]))

    for s in range(g.N):
        consider(f"shift+{s}", lambda ix, s=s: c.shift(ix, s))
        consider(f"atbash,shift+{s}", lambda ix, s=s: c.shift(c.atbash(ix), s))
        consider(f"shift+{s},atbash", lambda ix, s=s: c.atbash(c.shift(ix, s)))
    for name, stream in [("prime", c.prime_stream), ("totient", c.totient_stream)]:
        for sign in (+1, -1):
            for interrupt in (frozenset(), frozenset({0})):
                tag = f"{name}{'+' if sign > 0 else '-'}{'F-skip' if interrupt else ''}"
                consider(tag, lambda ix, st=stream, sg=sign, itr=interrupt:
                         c.keystream_decrypt(ix, st(), sign=sg, interrupt=itr))
    cands.sort(key=lambda t: t[0])
    return cands


def vigenere_period_scan(indices, max_period=40):
    return [(p, periodic_ioc(indices, p)) for p in range(1, max_period + 1)]


def main():
    segs = parse("data/liber_primus.md")
    dist = english_rune_distribution(segs)
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]

    # Reference numbers from solved material
    plain = []
    for s in segs:
        if s.solved and ("Substitution with default" in s.key):
            plain.extend(s.indices)
    print("=== reference (plaintext of solved pages) ===")
    print(f"IoC {ioc(plain):.3f}  doublets {doublet_rate(plain)*100:.2f}%  n={len(plain)}")

    allun = [i for s in unsolved for i in s.indices]
    print("\n=== all unsolved combined ===")
    print(f"IoC {ioc(allun):.3f}  doublets {doublet_rate(allun)*100:.2f}% "
          f"(random expects {100/g.N:.2f}%)  n={len(allun)}")
    scan = vigenere_period_scan(allun)
    top = sorted(scan, key=lambda t: -t[1])[:5]
    print("top periodic IoC (period, value):",
          ", ".join(f"({p}, {v:.3f})" for p, v in top))

    print("\n=== per unsolved segment ===")
    for s in unsolved:
        ix = s.indices
        scan = vigenere_period_scan(ix, 30)
        best_p, best_v = max(scan, key=lambda t: t[1])
        print(f"\n-- {s.section[:52]}  n={len(ix)}")
        print(f"   IoC {ioc(ix):.3f}  doublets {doublet_rate(ix)*100:.2f}%  "
              f"best periodic IoC: period {best_p} -> {best_v:.3f}")
        cands = attack_battery(s, dist)
        best = cands[0]
        print(f"   best simple attack: {best[2]}  chi2={best[0]:.0f} "
              f"word-score={best[1]:.2f}")
        print(f"   -> {best[3]}")
        hits = [cd for cd in cands if cd[1] > 0.15]
        for cd in hits[:3]:
            print(f"   CANDIDATE {cd[2]} word-score={cd[1]:.2f}: {cd[3]}")


if __name__ == "__main__":
    main()
