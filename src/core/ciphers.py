"""Cipher operations in rune-index space (mod 29), matching the schemes used
in the solved Liber Primus pages, plus generic building blocks for attacks.

Conventions:
- `indices` are lists of ints 0..28 (see gematria.py).
- "atbash" = reversed Gematria: i -> 28 - i.
- Interrupters: in several solved pages, ciphertext ᚠ (index 0) is a literal
  plaintext F that must be passed through unchanged *without* advancing the
  key stream. `interrupt` is the set of ciphertext indices treated that way.
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import gematria as g

N = g.N  # 29


def atbash(indices):
    return [N - 1 - i for i in indices]


def shift(indices, s):
    return [(i + s) % N for i in indices]


def keystream_decrypt(indices, stream, sign=-1, interrupt=frozenset()):
    """Generic decrypt: p = (c + sign*k) mod 29 with a lazy keystream.
    `stream` is an iterator of key values; interrupted positions don't
    consume a key value."""
    out = []
    it = iter(stream)
    for c in indices:
        if c in interrupt:
            out.append(c)
        else:
            out.append((c + sign * next(it)) % N)
    return out


def keystream_encrypt(indices, stream, sign=+1, literal=frozenset({0})):
    """Encrypt: c = (p + sign*k) mod 29 — except plaintext indices in
    `literal` (normally ᚠ/F), which are emitted unencrypted and do not
    consume a key value. This mirrors the solved pages, where "every clear
    text F is an ᚠ and needs to be skipped"."""
    out = []
    it = iter(stream)
    for p in indices:
        if p in literal:
            out.append(p)
        else:
            out.append((p + sign * next(it)) % N)
    return out


def vigenere_encrypt(indices, key, literal=frozenset({0})):
    def stream():
        j = 0
        while True:
            yield key[j % len(key)]
            j += 1
    return keystream_encrypt(indices, stream(), sign=+1, literal=literal)


def vigenere_decrypt(indices, key, interrupt=frozenset()):
    def stream():
        j = 0
        while True:
            yield key[j % len(key)]
            j += 1
    return keystream_decrypt(indices, stream(), sign=-1, interrupt=interrupt)


def prime_stream():
    """2, 3, 5, 7, 11, ... (simple trial-division sieve; plenty fast for
    the few thousand primes these texts need)."""
    primes = []
    n = 2
    while True:
        if all(n % p for p in primes if p * p <= n):
            primes.append(n)
            yield n
        n += 1


def totient_stream():
    """phi(p_i) = p_i - 1 for the i-th prime (1, 2, 4, 6, 10, ...)."""
    for p in prime_stream():
        yield p - 1


# --- scoring -----------------------------------------------------------------

COMMON_WORDS = {
    "THE", "OF", "AND", "TO", "A", "AN", "IN", "IS", "IT", "YOU", "THAT",
    "ARE", "BE", "THIS", "ALL", "WE", "OR", "YOUR", "NOT", "FOR", "WITHIN",
    "END", "SELF", "WILL", "FIND", "WAY", "LIKE", "KNOW", "TRUTH", "SACRED",
    "PRIMES", "DIVINITY", "CIRCUMFERENCE", "SHADOWS", "INSTAR", "EMERGE",
}


def word_score(words_latin):
    """Fraction of words that are common English words — crude but effective
    for distinguishing a correct decrypt from noise."""
    if not words_latin:
        return 0.0
    hits = sum(1 for w in words_latin if w in COMMON_WORDS)
    return hits / len(words_latin)


def decrypt_words(words, fn):
    """Apply an index-level decrypt fn to a word-structured text, preserving
    word boundaries. fn takes the flat index list and returns same length."""
    flat = [i for w in words for i in w]
    dec = fn(flat)
    out, pos = [], 0
    for w in words:
        out.append(dec[pos:pos + len(w)])
        pos += len(w)
    return out
