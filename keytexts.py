"""Candidate running-key texts, transliterated to Gematria Primus rune indices.

The doublet analysis (REPORT.md §4) rules out a *plain* running key, so a
running key is only viable combined with the no-repeat enforcement (key-skip).
`attack_running_text.py` tests these key streams with the key-skip decoder.

Sources (kept out of the repo; rebuilt/cached on demand under keytext_cache/):
- KJV: the `bible-kjv` npm package's verse JSON (Genesis→Revelation in
  canonical order), markup tags stripped. Build once with
  `python3 keytexts.py --build-kjv <path-to-bible-kjv/dist>`; the rune stream
  is cached as keytext_cache/kjv.u8 (one byte per rune).
- Any plain-text file can be added as a key via `load_textfile(path)`.

We deliberately do NOT vendor third-party scripture into the repo; only the
rune-index cache (gitignored) is materialised locally.
"""

import argparse
import json
import os
import re

import gematria as g

CACHE = os.path.join(os.path.dirname(__file__), "keytext_cache")
TAG_RE = re.compile(r"<[^>]+>")  # KJV markup: <FI>..<Fi>, <CM>, <RF>..<Rf>, etc.


def _cache_path(name):
    return os.path.join(CACHE, f"{name}.u8")


def save_stream(name, indices):
    os.makedirs(CACHE, exist_ok=True)
    with open(_cache_path(name), "wb") as f:
        f.write(bytes(indices))


def load_stream(name):
    with open(_cache_path(name), "rb") as f:
        return list(f.read())


def has(name):
    return os.path.exists(_cache_path(name))


def build_kjv(dist_dir):
    """Concatenate all verses in canonical order, strip markup, transliterate."""
    books = json.load(open(os.path.join(dist_dir, "content", "books.json")))
    text_parts = []
    for bi, book in enumerate(books, start=1):
        for ch in range(1, book["chapters"] + 1):
            path = os.path.join(dist_dir, "resources", str(bi), f"{ch}.json")
            verses = json.load(open(path))
            for v in verses:
                text_parts.append(TAG_RE.sub(" ", v))
    text = " ".join(text_parts)
    idx = g.latin_text_to_indices(text)
    save_stream("kjv", idx)
    return idx


def load_textfile(path, name):
    text = open(path, encoding="utf-8", errors="ignore").read()
    idx = g.latin_text_to_indices(text)
    save_stream(name, idx)
    return idx


def get(name):
    if has(name):
        return load_stream(name)
    raise FileNotFoundError(
        f"key text '{name}' not cached; build it first (see keytexts.py --help)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-kjv", metavar="DIST_DIR",
                    help="path to bible-kjv/dist (with content/ and resources/)")
    ap.add_argument("--add-textfile", nargs=2, metavar=("PATH", "NAME"),
                    help="transliterate a plain-text file into a named key")
    args = ap.parse_args()
    if args.build_kjv:
        idx = build_kjv(args.build_kjv)
        print(f"KJV: {len(idx):,} runes cached -> {_cache_path('kjv')}")
    if args.add_textfile:
        path, name = args.add_textfile
        idx = load_textfile(path, name)
        print(f"{name}: {len(idx):,} runes cached -> {_cache_path(name)}")
