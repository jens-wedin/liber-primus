# Work log

Chronological record of what was tried, why, and what came of it. Newest at
the bottom. Summary-level conclusions live in [REPORT.md](REPORT.md).

## 2026-08-18 — Session 1: toolkit + baseline statistics

- Downloaded the scream314/cicada3301 transcription to `data/liber_primus.md`
  (137,957 bytes) and wrote `parse_lp.py`. Inventory: 25 segments, 15,750
  runes; 12,956 unsolved across 14 segments (Key: `?`).
- Wrote `gematria.py` (Gematria Primus, 29 runes) and `ciphers.py`.
- **Validation strategy**: forward-encrypt known plaintexts instead of
  decrypting, because ciphertext ᚠ is ambiguous (literal F or an encrypted
  collision such as M+I ≡ 0). Result 9/9 checks pass, three of them exact:
  03.jpg 251/251 runes (Vigenère DIVINITY), 14-15.jpg 319/319
  (FIRFUMFERENFE), 73.jpg/56 85/85 (φ(prime) stream).
- Debugging notes worth remembering:
  - Digraphs must be transliterated **per word** — joining text first lets
    EA/TH/… form across word boundaries and desyncs everything.
  - Page 14's "LESSION" in the transcription only encrypts correctly as
    "LESSON".
  - The md's rune block for 04.jpg is inconsistent with its own plaintext
    (author marks it unverified); excluded from strict validation.
  - The md's plaintext for 03.jpg covers only 251 of the section's 394 runes.
- Statistics on the unsolved stream: IoC 1.000 (English-in-runes reference:
  1.735), no periodic IoC above noise for periods ≤ 40, doublet rate 0.66%
  vs 3.45% expected — a ~17σ deficiency.
- Attack battery, all negative: 87 fixed-mapping variants per segment,
  prime/totient keystreams ± with/without literal-ᚠ, autokey (both feeds,
  both signs, primers ≤ 3 on small segments, ≤ 2 elsewhere). Noted that
  plaintext-autokey chi² "wins" are a feedback artifact, not signal.
- Committed as cd39b3c + 82474cd on `claude/liber-primus-runes-w8jabk`.

## 2026-08-18 — Session 2: crib-dragging

Plan: exploit two constraints the simple attacks ignored —

1. **Word boundaries survive encryption** (the • separators). A multi-word
   crib must match the ciphertext's word-length pattern exactly, which
   collapses the number of legal offsets.
2. **The literal-ᚠ rule survives too**: wherever a crib has F, the
   ciphertext must show ᚠ (and that position consumes no key). Cribs
   containing F ("CIRCUMFERENCE", "SUFFERING", "SELF", …) are therefore
   strong filters.

For every legal (crib, offset) pair, derive the implied keystream
k = (c − p) mod 29 and test it for structure: constant, arithmetic
progression, short repeating period (→ Vigenère key candidate, extended and
scored over the whole segment), match against prime-family sequences
(pⱼ mod 29, φ(pⱼ) mod 29 at any starting index), and English-ness of the
key spelled as runes (running-key-from-English-text hypothesis, ranked by a
bigram model built from the solved pages' plaintext).

**Built `crib_drag.py`.** Self-test against solved pages passes and matters:
dragging "WELCOME PILGRIM TO THE" over page 03 recovers period-8 key
`YDIUINIT` (DIVINITY rotated by the 7-rune header — phase and all), and
"WITHIN THE DEEP WEB" over page 56 pins the φ(prime) stream at prime index
5 (exactly the five values "AN END" consumed). The tool provably finds the
known keys, so its result on the unsolved text is a real negative, not a
bug.

**Result on the unsolved segments: negative.** 32 cribs, 422 legal
placements after the word-length and literal-ᚠ filters. Zero structural
hits — no placement anywhere implies a constant shift, arithmetic
progression, short-period Vigenère key, or any window of pⱼ/φ(pⱼ) mod 29
(first 3000 primes). The most "English-looking" implied keystream scores
−2.76 bigram logprob vs a −3.37 random baseline — with 422 draws that's
exactly where the best-of-noise order statistic lands, and the keys read as
garbage ("XOMEPTIAIA", "MYOREBDTW"). Full output archived in
`results/crib_drag_2026-08-18.txt`.

Interpretation: if any of these 32 stock phrases appears word-aligned in
the unsolved text, its local keystream has no simple structure — killing
"same trick as the solved pages, just further in" for every crib position
tested. Consistent with per-page unique keys or a keystream with no short
description.

Next candidates for the crib list: reversed text, crib placement ignoring
word boundaries (if the • separators are decoys in unsolved pages), and
doublet-signature simulation to pre-filter cipher families.
