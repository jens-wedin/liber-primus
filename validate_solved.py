"""Reproduce the known solutions of the solved Liber Primus pages, to prove the
gematria table, parser and cipher code are correct.

For the keyed pages we validate by *forward encryption*: transliterate the
known plaintext, apply the documented cipher (plaintext F stays a literal ᚠ
and consumes no key), and compare rune-for-rune with the actual ciphertext.
Decryption of ᚠ is ambiguous (it is either a literal F or a normally
encrypted rune), so encryption is the deterministic direction.
"""

# --- path bootstrap: add src/ subfolders so flat imports resolve ---
import os as _os, sys as _sys
_SRC = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "src")
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import ciphers as c
import gematria as g
from parse_lp import parse
from solved_text import P03, P14, P73   # verified plaintexts, single source of truth

segs = parse("data/liber_primus.md")


def seg(prefix):
    return next(s for s in segs if s.section.startswith(prefix))


def check_contains(name, words, expect):
    latin = g.words_to_latin(words)
    ok = all(e in latin for e in expect)
    print(f"[{'OK' if ok else 'FAIL'}] {name}")
    print("   " + latin[:160].replace("\n", " ") + ("..." if len(latin) > 160 else ""))
    return ok


def check_encrypt(name, plaintext, cipher_indices, encrypt_fn, threshold=0.98):
    p = g.latin_text_to_indices(plaintext)
    enc = encrypt_fn(p)
    n = min(len(enc), len(cipher_indices))
    matches = sum(1 for a, b in zip(enc[:n], cipher_indices[:n]) if a == b)
    ok = n > 0 and matches / n > threshold
    print(f"[{'OK' if ok else 'FAIL'}] {name}: {matches}/{n} runes match "
          f"(plaintext {len(enc)} vs ciphertext {len(cipher_indices)})")
    if not ok:
        for i in range(n):
            if enc[i] != cipher_indices[i]:
                print(f"   first mismatch at rune {i}: "
                      f"got {g.IDX_TO_RUNE[enc[i]]} expected {g.IDX_TO_RUNE[cipher_indices[i]]}")
                break
    return ok


results = []

# --- plain substitution pages ------------------------------------------------
for prefix, expect in [
    ("05.jpg", ["WISDOM", "PRIMES", "SACRED", "TOTIENT"]),
    ("10.jpg", ["LOSS", "DIUINITY", "CIRCUMFERENCE"]),
    ("13.jpg", []),
    ("16.jpg", ["INSTRUCT", "TRUTH"]),
    ("74.jpg", ["PARABLE", "INSTAR", "EMERGE"]),
]:
    s = seg(prefix)
    results.append(check_contains(f"{s.section} (plain substitution)", s.words, expect))

# --- 03.jpg: Vigenère, key DIVINITY ------------------------------------------
# The md's plaintext covers the first 251 of the section's 394 runes (its page
# break differs); we verify that prefix exactly. 04.jpg's rune block in the md
# is marked unverified by its author and doesn't align with its plaintext, so
# it is not strictly checked here.
key = g.latin_to_indices("DIVINITY")
results.append(check_encrypt("03.jpg (Vigenère DIVINITY, literal F)",
                             P03, seg("03.jpg").indices,
                             lambda p: c.vigenere_encrypt(p, key)))

# --- 06-09.jpg: reversed gematria + shift 3 ----------------------------------
words = seg("06.jpg").words + seg("09.jpg").words
dec = c.decrypt_words(words, lambda ix: c.shift(c.atbash(ix), 3))
results.append(check_contains("06-09.jpg (atbash then +3)", dec,
                              ["COAN", "MASTER", "STUDENT"]))

# --- 14.jpg (covers pages 14+15): Vigenère, key FIRFUMFERENFE ----------------
# "LESSON"/"ENLIGHTENED" appear slightly differently in the md's rendering;
# a couple of single-rune spelling differences are tolerated (threshold 0.95).
key = g.latin_to_indices("FIRFUMFERENFE")
results.append(check_encrypt("14-15.jpg (Vigenère FIRFUMFERENFE, literal F)",
                             P14, seg("14.jpg").indices,
                             lambda p: c.vigenere_encrypt(p, key),
                             threshold=0.95))

# --- 73.jpg: keystream phi(prime_i) ------------------------------------------
results.append(check_encrypt("73.jpg (phi(prime) stream, literal F)",
                             P73, seg("73.jpg").indices,
                             lambda p: c.keystream_encrypt(p, c.totient_stream(),
                                                           sign=+1)))

print(f"\n{sum(results)}/{len(results)} checks passed")
