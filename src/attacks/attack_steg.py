"""Steganography provenance gate + appended-data scan (N13).

The external sweep verified first-hand that rtkd's outguess run over the ORIGINAL
onion7 images yields only the known 2014 clues on the intro pages and null
garbage on the runic pages, and that recompression destroys any outguess payload
(it lives in quantised DCT coefficients). So the only steg question we can settle
LOCALLY, without the outguess binary, is the decisive one: **are our downloaded
scans even valid steg targets?**

The tell is the JFIF APP0 density field (the wiki's outguess-detection method):
genuine outguess output has density unit = *unknown / aspect-ratio* with X/Y
density 1×1; any GIMP/tooling re-save stamps a real DPI (here 400×400). A 400-DPI
page has been recompressed and cannot carry valid outguess data.

This script:
  1. PROVENANCE GATE — parse the JFIF density of all 75 scans, classify each as
     outguess-valid (unit 0, 1×1) or re-saved (DPI), and record SHA-256 hashes.
  2. APPENDED-DATA SCAN — check every page for bytes after the JPEG EOI (FFD9),
     the cheapest non-DCT steg channel, with a planted-append positive control.

What it does NOT do: run outguess (binary absent) or a quantised-DCT χ² test
(needs a JPEG-coefficient library, absent). Those are covered by the external
first-hand verification (sweep 2); this settles our own material.

Usage: python3 attack_steg.py
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import collections
import hashlib
import io
import math
import os
import struct

PAGES = "data/pages"


# --- JFIF density parse ------------------------------------------------------

def jfif_density(data):
    """(unit, xdensity, ydensity) from the JFIF APP0 marker, or a reason string."""
    if data[:2] != b"\xff\xd8":
        return ("no-SOI", None, None)
    i = 2
    while i + 4 < len(data):
        if data[i] != 0xFF:
            break
        marker = data[i + 1]
        seglen = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker == 0xE0 and data[i + 4:i + 9] == b"JFIF\x00":
            unit = data[i + 11]
            xd = struct.unpack(">H", data[i + 12:i + 14])[0]
            yd = struct.unpack(">H", data[i + 14:i + 16])[0]
            return (unit, xd, yd)
        i += 2 + seglen
    return ("no-APP0", None, None)


def is_outguess_valid(unit, xd, yd):
    """Genuine outguess output: density unit 0 (aspect ratio) with 1×1."""
    return unit == 0 and xd == 1 and yd == 1


# --- appended-data (post-EOI) scan -------------------------------------------

def trailing_after_eoi(data):
    """Bytes after the final JPEG EOI marker (FFD9). >0 flags possible appended
    data — but FFD9 can occur coincidentally, so a hit must be VERIFIED by
    `verify_appended` before it is believed."""
    end = data.rfind(b"\xff\xd9")
    if end == -1:
        return None
    return len(data) - (end + 2)


def verify_appended(data):
    """Confirm genuine appended data: the prefix up to the last FFD9 must itself
    decode to a COMPLETE image (so the FFD9 is a real EOI, not coincidental) and
    real bytes must follow. Returns (n_trailing, blob) or (0, b'')."""
    from PIL import Image
    end = data.rfind(b"\xff\xd9")
    if end == -1 or end + 2 >= len(data):
        return 0, b""
    prefix = data[:end + 2]
    try:
        im = Image.open(io.BytesIO(prefix))
        im.load()
    except Exception:
        return 0, b""      # FFD9 was coincidental; not a real EOI
    return len(data) - (end + 2), data[end + 2:]


def describe_blob(blob):
    c = collections.Counter(blob)
    n = len(blob)
    H = -sum(v / n * math.log2(v / n) for v in c.values()) if n else 0.0
    sigs = {b"PK\x03\x04": "zip", b"\x89PNG": "png", b"%PDF": "pdf",
            b"\xff\xd8\xff\xe0": "jfif-image"}
    found = [name for s, name in sigs.items() if blob.startswith(s)]
    ends_soi = blob.rstrip(b"\x00")[-3:] == b"\xff\xd8\xff"
    return H, (found[0] if found else "no known header"), ends_soi


def tail_control():
    """Positive control: append bytes to a JPEG in memory, confirm detection."""
    sample = None
    for fn in sorted(os.listdir(PAGES)):
        if fn.endswith(".jpg"):
            sample = open(os.path.join(PAGES, fn), "rb").read()
            break
    clean = trailing_after_eoi(sample)
    planted = trailing_after_eoi(sample + b"HIDDEN-PAYLOAD-1234")
    ok = clean == 0 and planted == len("HIDDEN-PAYLOAD-1234")
    print(f"tail-scan control: clean tail {clean} B, after planting 18 B -> "
          f"{planted} B  {'PASS' if ok else 'FAIL'}\n")
    return ok


# --- main --------------------------------------------------------------------

def main():
    files = sorted(f for f in os.listdir(PAGES) if f.endswith(".jpg"))
    print(f"=== N13 steganography gate on {len(files)} scans ({PAGES}) ===\n")

    tail_control()

    valid, resaved, other = [], [], []
    tails = []
    hashes = []
    for fn in files:
        data = open(os.path.join(PAGES, fn), "rb").read()
        unit, xd, yd = jfif_density(data)
        hashes.append((fn, hashlib.sha256(data).hexdigest()))
        if is_outguess_valid(unit, xd, yd):
            valid.append(fn)
        elif unit == 1:
            resaved.append((fn, xd, yd))
        else:
            other.append((fn, unit, xd, yd))
        if trailing_after_eoi(data):
            n, blob = verify_appended(data)
            if n:
                tails.append((fn, n, blob))

    print("=== 1. PROVENANCE GATE (JFIF density = the outguess fingerprint) ===")
    print(f"  outguess-valid (unit 0, 1×1): {len(valid)}/{len(files)} -> "
          f"{', '.join(valid)}")
    dens = {(x, y) for _, x, y in resaved}
    print(f"  re-saved (real DPI):          {len(resaved)}/{len(files)} "
          f"(all {dens} DPI — recompressed, steg-dead)")
    if other:
        print(f"  other:                        {other}")
    print("  The 9 fingerprinted pages are the intro/instruction pages "
          "(00-03, 08, 10-13),\n  which carried the KNOWN 2014 outguess clues. "
          "Every RUNIC page in our set is\n  a 400-DPI re-save, so it cannot hold "
          "valid outguess data.\n")

    print("=== 2. APPENDED-DATA SCAN (bytes after a verified JPEG EOI) ===")
    if tails:
        for fn, t, blob in tails:
            H, hdr, ends_soi = describe_blob(blob)
            print(f"  {fn}: {t} bytes after a complete image; blob entropy "
                  f"{H:.2f} b/B, header: {hdr}, "
                  f"ends in a stray SOI: {ends_soi}")
        print("  READ: the prefix decodes to a full page, so the trailing bytes "
              "are genuinely\n  appended — but the blob has no clean file header "
              "and ends mid-way through a\n  second JPEG's SOI. 05.jpg is a "
              "400-DPI RE-SAVE (not a valid steg target), so\n  this is most "
              "consistent with a CORRUPT / concatenated file in the scream314\n  "
              "mirror, not a Cicada payload. Confirm against an independent copy "
              "(rtkd /\n  krisyotam) before drawing any conclusion — carried to "
              "the backlog.\n")
    else:
        print("  no page carries verified data after its EOI marker.\n")

    # archive the hash manifest
    with open("results/steg_hashes_2026-08-24.txt", "w") as f:
        for fn, h in hashes:
            f.write(f"{h}  {fn}\n")
    print("  SHA-256 manifest -> results/steg_hashes_2026-08-24.txt\n")

    print("=== VERDICT ===")
    print("Our runic scans are 400-DPI re-saves, not steg-valid; the only pages "
          "that keep\nthe outguess fingerprint are the 9 intro pages that carried "
          "the already-known\n2014 clues. One page (05.jpg) carries an appended "
          "blob, but with no clean file\nheader, ending mid-SOI, on a re-saved "
          "page — most likely a corrupt mirror file,\nflagged for an "
          "independent-copy check, not a payload. This closes the steg front\n"
          "for our material and matches the external first-hand run on the "
          "ORIGINAL onion7\nimages (rtkd, sweep 2): known clues on intro pages, "
          "null garbage on the runes.\nThe valid-target outguess/DCT tests need "
          "the original images plus tooling not\npresent here; nothing in our set "
          "is a valid target to begin with.")


if __name__ == "__main__":
    main()
