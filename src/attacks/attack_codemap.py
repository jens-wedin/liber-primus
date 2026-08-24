"""Derive the pages-66-68 code->byte map and reproduce rtkd's String 4 (N14).

rtkd/iddqd's `byte-strings` file carries "String 4 - Matrix from pages 49-51
converted to hexadecimal" — 256 bytes, and full-set pages 49-51 are our code
pages 66-68 (§21/N2). Our old `d*62+b62` map matched only 4/256, so the code->byte
map was unknown. This derives it.

Two facts settle it:

  1. SAME OBJECT, natural order. Our 256 codes (pages 66, 67, 68, each read
     row-major — the obvious reading order) have the EXACT same repetition
     pattern as String 4: both are 161 distinct values with an identical
     frequency-of-frequency multiset (92 singletons, 49 twice, 14 thrice, 6
     four times). That is not chance; a bijective code->byte map exists.

  2. THE MAP is `byte = digit * 60 + base62(char)` with the base-62 alphabet
     `0-9 A-Z a-z` (digits, then UPPER, then lower — note this differs from the
     lowercase-first ordering `analyze_codepage.py` used for its rune probes).
     The digit is the high part: digit d owns byte band [60d, 60d+59].

This map reproduces String 4 at **253/256**. All three misses are the SAME code,
`3l` (lowercase L), which should be `3I` (capital I): 3*60 + index('I') = 198,
exactly String 4's byte, versus 3*60 + index('l') = 227. That is the l/I
transcription ambiguity `data/code_pages.txt` flagged, and one of the three (the
first, at global position 25) is one of Dukotah's six independently-flagged
contested bytes. With `3l -> 3I` corrected in the transcription, our codes
reproduce String 4 **256/256** — so the code pages are verified byte-for-byte
against an independent rendering, and the map is closed.

Usage: python3 attack_codemap.py
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import string

import analyze_codepage as A

ALPHA = string.digits + string.ascii_uppercase + string.ascii_lowercase  # 0-9A-Za-z
PAGE_ORDER = ("66", "67", "68")
FIX = {"3l": "3I"}          # the l/I transcription correction derived below


def code_value(code, fix=False):
    c = FIX.get(code, code) if fix else code
    return (int(c[0]) * 60 + ALPHA.index(c[1])) % 256


def load_target(path="data/rtkd_string4.hex"):
    hexs = "".join(l.strip() for l in open(path) if not l.startswith("#"))
    return list(bytes.fromhex(hexs))


def canon(seq):
    m, out = {}, []
    for x in seq:
        m.setdefault(x, len(m))
        out.append(m[x])
    return out


def main():
    pages = A.load_pages()
    codes = [c for p in PAGE_ORDER for c in pages[p]]
    s4 = load_target()
    print(f"our codes: {len(codes)}  |  String 4: {len(s4)} bytes\n")

    print("1. SAME OBJECT — repetition pattern (order 66,67,68 row-major):")
    print(f"   codes canonical == String4 canonical: {canon(codes) == canon(s4)}")
    print(f"   distinct: codes {len(set(codes))}, bytes {len(set(s4))}\n")

    for fix, label in ((False, "as transcribed"), (True, "with 3l -> 3I")):
        hits = sum(1 for c, b in zip(codes, s4) if code_value(c, fix) == b)
        print(f"2. MAP byte = digit*60 + base62(0-9A-Za-z), {label}: "
              f"{hits}/{len(s4)} exact")
        if not fix:
            miss = [(i, c) for i, (c, b) in enumerate(zip(codes, s4))
                    if code_value(c) != b]
            print(f"   mismatches: {miss}  (all '3l'; want '3I' = byte 198)")
    print()
    ok = all(code_value(c, True) == b for c, b in zip(codes, s4))
    print("VERDICT: with the l/I correction the code pages reproduce rtkd's "
          "String 4\nbyte-for-byte "
          f"({'256/256 CONFIRMED' if ok else 'MISMATCH'}). The code->byte map is "
          "closed and the\ntranscription is verified against an independent "
          "rendering. §22 already ruled\nout pad/index/table for these bytes; "
          "the derived-pad reading stays the §13 wall.")


if __name__ == "__main__":
    main()
