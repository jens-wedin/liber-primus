"""Coined/mangled key-word generator.

Gap this closes: the word-key attack (`attack_vigenere_skip.py`) only covered
*dictionary* words, but Cicada's own solved-page keys include non-dictionary
**manglings** — most famously FIRFUMFERENFE, which is CIRCUMFERENCE with every
C rewritten as F. A coined key like that is unreachable from any word list, so
this module expands a base word into the coined variants Cicada is attested to
use, letting `attack_vigenere_skip.py --mangle` beam them like any other key.

Every transform is motivated by something Cicada actually did on a solved page:

  - consonant collapse   C->F (the FIRFUMFERENFE trick) and its neighbours
                         (the futhorc collapses K->C, Q->C, S/Z, U/V ...)
  - atbash               reversed gematria, i -> 28-i (used on page 06-09)
  - reversal             the word read backwards in rune space
  - vowel rotation       A->E->I->O->U->A, a light coinage

Each variant is returned as ``(label, indices)``; the base word itself and any
transform that is a no-op or collides with an already-emitted variant drop out.
``mangle("CIRCUMFERENCE")`` contains FIRFUMFERENFE — the generator's ground
truth, asserted in ``selfcheck()``.
"""

import gematria as g

N = g.N

# Letter-level substitution pairs, each applied to EVERY occurrence. The first
# is the one Cicada is proven to have used (C->F => FIRFUMFERENFE); the rest are
# the futhorc's own letter collapses and their inverses.
SUBS = [
    ("C", "F"), ("F", "C"),
    ("C", "K"), ("K", "C"),
    ("C", "Q"), ("Q", "C"),
    ("S", "Z"), ("Z", "S"),
    ("U", "V"), ("V", "U"),
    ("C", "S"), ("S", "C"),
]

VOWELS = "AEIOU"


def _rotate_vowels(word):
    out = []
    for ch in word:
        if ch in VOWELS:
            out.append(VOWELS[(VOWELS.index(ch) + 1) % len(VOWELS)])
        else:
            out.append(ch)
    return "".join(out)


def mangle(word):
    """Yield ``(label, indices)`` coined variants of an uppercase A-Z word.

    Deduplicated on the index sequence; the base word and no-op transforms are
    excluded, so a variant is only emitted when it genuinely differs.
    """
    word = "".join(ch for ch in word.upper() if ch.isalpha())
    base = tuple(g.latin_to_indices(word))
    seen = {base}
    out = []

    def add(label, indices):
        t = tuple(indices)
        if t and t not in seen:
            seen.add(t)
            out.append((label, list(t)))

    # 1. consonant collapse / expansion (letter level)
    for a, b in SUBS:
        if a in word:
            add(f"{word}~{a}>{b}", g.latin_to_indices(word.replace(a, b)))

    # 2. atbash — reversed gematria in index space
    add(f"{word}~atbash", [N - 1 - i for i in base])

    # 3. reversal in rune space
    add(f"{word}~rev", list(reversed(base)))

    # 4. vowel rotation (letter level)
    add(f"{word}~vowrot", g.latin_to_indices(_rotate_vowels(word)))

    return out


def mangle_words(words):
    """All coined variants of a base word list, deduped across the whole set."""
    seen, out = set(), []
    for w in words:
        for label, ix in mangle(w):
            t = tuple(ix)
            if t not in seen:
                seen.add(t)
                out.append((label, ix))
    return out


def selfcheck():
    """The generator must reproduce the one attested Cicada mangling:
    CIRCUMFERENCE --(C>F)--> FIRFUMFERENFE."""
    want = tuple(g.latin_to_indices("FIRFUMFERENFE"))
    got = {tuple(ix) for _, ix in mangle("CIRCUMFERENCE")}
    return want in got


if __name__ == "__main__":
    ok = selfcheck()
    print(f"selfcheck (CIRCUMFERENCE -> FIRFUMFERENFE via C>F): "
          f"{'PASS' if ok else 'FAIL'}")
    ex = mangle_words(["CIRCUMFERENCE", "DIVINITY", "PRIMES", "SACRED"])
    print(f"\n{len(ex)} coined variants from 4 base words, e.g.:")
    for label, ix in ex[:14]:
        print(f"  {label:26s} {g.indices_to_latin(ix)}")
