"""The solved pages' PLAINTEXT — single source of truth.

Why this exists (audit finding, 2026-08-21): `doublet_sim.english_plaintext`
only concatenates the pages whose stored rune indices ARE already plaintext
(plain-substitution pages, plus atbash+3 which is a trivial map). It silently
skips every KEYED page — 03/04 (Vigenère DIVINITY), 14-15 (FIRFUMFERENFE) and
73 (φ(prime)) — because for those the stored indices are ciphertext. That drops
919 of 2794 solved runes (33%), including page 73 "AN END", which is exactly the
page carrying the §18 "…PILGRIM TO SEEK OUT THIS PAGE" run.

Using the short stream as "the solved plaintext" is fine as a generic English
n-gram reference, but it is WRONG for anything about ᚠ placement or Gematria
sums: it under-represents ᚠ (1.65% vs the 3.45% chance rate), and it omits the
very text the §18 claim is about.

`full_plaintext()` returns the complete solved plaintext, keyed pages included,
by transliterating the known plaintexts (the same constants `validate_solved.py`
proves by forward encryption — so they are verified, not assumed).
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import ciphers as c
import gematria as g
from parse_lp import parse

# --- known plaintexts of the keyed pages (verified in validate_solved.py) ----

P03 = ("WELCOME WELCOME PILGRIM TO THE GREAT JOURNEY TOWARD THE END OF ALL "
       "THINGS IT IS NOT AN EASY TRIP BUT FOR THOSE WHO FIND THEIR WAY HERE "
       "IT IS A NECESSARY ONE ALONG THE WAY YOU WILL FIND AN END TO ALL "
       "STRUGGLE AND SUFFERING YOUR INNOCENCE YOUR ILLUSIONS YOUR CERTAINTY "
       "AND YOUR REALITY ULTIMATELY YOU WILL DISCOVER AN END TO SELF")

P14 = ("A KOAN DURING A LESSON THE MASTER EXPLAINED THE I THE I IS THE "
       "VOICE OF THE CIRCUMFERENCE HE SAID WHEN ASKED BY A STUDENT TO "
       "EXPLAIN WHAT THAT MEANT THE MASTER SAID IT IS A VOICE INSIDE YOUR "
       "HEAD I DONT HAVE A VOICE IN MY HEAD THOUGHT THE STUDENT AND HE "
       "RAISED HIS HAND TO TELL THE MASTER THE MASTER "
       "STOPPED THE STUDENT AND SAID THE VOICE THAT JUST SAID YOU HAVE NO "
       "VOICE IN YOUR HEAD IS THE I AND THE STUDENTS WERE ENLIGHTENED")

P73 = ("AN END WITHIN THE DEEP WEB THERE EXISTS A PAGE THAT HASHES TO "
       "IT IS THE DUTY OF EUERY PILGRIM TO SEEK OUT THIS PAGE")


def full_plaintext(segs=None):
    """Complete solved plaintext as rune indices, in book order.

    Plain-substitution pages contribute their indices directly; the atbash+3
    pages are mapped back; the keyed pages contribute their verified plaintext.
    """
    if segs is None:
        segs = parse("data/liber_primus.md")
    known = {"03.jpg": P03, "14.jpg": P14, "73.jpg": P73}
    stream = []
    for s in segs:
        if not s.solved:
            continue
        hit = next((v for k, v in known.items() if s.section.startswith(k)), None)
        if hit is not None:
            stream.extend(g.latin_text_to_indices(hit))
        elif "Substitution with default" in s.key or s.key.startswith("-"):
            stream.extend(s.indices)
        elif "reversed Gematria" in s.key and "Shift 3" in s.key:
            stream.extend(c.shift(c.atbash(s.indices), 3))
        # 04.jpg ("Continuation of key") has no separately verified plaintext
        # in the md and is left out rather than guessed.
    return stream


def coverage_report():
    segs = parse("data/liber_primus.md")
    from doublet_sim import english_plaintext
    short, full = english_plaintext(segs), full_plaintext(segs)
    F = 0
    tot = sum(len(s.indices) for s in segs if s.solved)
    print(f"solved runes in book: {tot}")
    print(f"  english_plaintext(): {len(short)} runes, "
          f"ᚠ {short.count(F)/len(short)*100:.2f}%")
    print(f"  full_plaintext()   : {len(full)} runes, "
          f"ᚠ {full.count(F)/len(full)*100:.2f}%  (chance 3.45%)")
    lat = g.indices_to_latin(full)
    for probe in ("PILGRIMTOSEEC", "SEECOVTTHISPAGE", "CIRCUMFERENCE"):
        print(f"  contains {probe!r}: {probe in lat}")


if __name__ == "__main__":
    coverage_report()
