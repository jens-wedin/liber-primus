# BACKLOG.md — experiments to run next

Grounded in the current state (REPORT.md). Each is framed the project way:
hypothesis → method → **control** → priority. Nothing here is trusted without a
positive control (encrypt known English with the scheme, recover it) and, where
relevant, a chance ceiling. Most will be negatives; a clean negative with a
control beats a flashy maybe.

Opened 2026-08-21 after: §17 (square-as-interrupter negative → both "square is a
key" readings closed), §18 (the literal-ᚠ GP-sum steganography layer on solved
pages), and the Uncovering-Cicada wiki sweep (independent replication of §4;
untried leads surfaced).

## P1 — do next

### 1. Literal-ᚠ as a keystream interrupter on the *unsolved* pages
- **DONE 2026-08-21 — NEGATIVE, control-validated** (`attack_literal_f.py`,
  REPORT §19). Best real decode below the chance ceiling; ᚠ is at chance
  frequency (3.53% ≈ 1/29). The hold-vs-advance branch at each ciphertext ᚠ is
  genuinely new coverage (the key-skip beam cannot express a pointer hold), and
  it reads no better than random.
- **Hypothesis.** The unsolved pages obey the same **literal-ᚠ rule** the solved
  pages do: a ciphertext ᚠ can be an unencrypted plaintext F that consumes **no
  key**. Every attack so far treated all runes uniformly; if some ᚠ mean "key
  pointer holds," the keystream re-aligns and fixed-position attacks were doomed
  for a reason we can now model.
- **Method.** Re-run the prime/totient/word-key + key-skip beams, but at each
  ciphertext ᚠ branch on {literal-F: pointer holds; ordinary rune: pointer
  advances}; beam over that ambiguity jointly with the skip.
- **Control.** Plant English encrypted with the literal-ᚠ rule + a known
  keystream; confirm the ᚠ-aware beam recovers it where the ᚠ-blind beam cannot.
- **Why now.** It is the exact convention the *solved* pages use (validate_solved
  proves it), yet it has never been applied inside an *unsolved*-page attack.
  Motivated directly by §18 (ᚠ is meaningful, not incidental).

### 2. ᚠ-position structural map of the unsolved pages
- **DONE 2026-08-21 — NEGATIVE / no fingerprint** (`analyze_fpositions.py`,
  REPORT §20). Gap-length prime/emirp and word-edge tests all consistent with
  random placement vs a Monte-Carlo null (the one borderline, prime-gap z ≈ +2.3
  corrected, is a doublet-suppression artifact within multiple-comparison noise).
  Confirms §18's caveat: the ᚠ layer is a plaintext property, invisible in
  ciphertext.
- **Hypothesis.** Literal-ᚠ runes mark **structural boundaries** — prime/emirp-
  length runs, GP-sum checksums — as §18 shows they do on solved pages.
- **Method.** Extract ᚠ positions/counts per unsolved segment; test inter-ᚠ gap
  lengths for prime/emirp enrichment and for alignment to word / line / period
  marks. Null = random ᚠ placement at the observed rate; positive reference =
  the solved pages (where the structure is known to exist).
- **Control.** The reference (solved) pages must light up; the random null must
  not. Report effect size, not just a yes/no.
- **Cheap** (uses data we already have; no decryption needed).

### 3. Code pages 66 / 67 / 68 (+ page-73 hex) — verified transcription & structure
- **PARTLY DONE 2026-08-21 (REPORT §21).** Transcription VERIFIED from the scans:
  67 (104) and 68 (72) exact, page 66 (80) newly transcribed; all 256 codes valid.
  Page-73 "hex" is the already-known AN END SHA-512, not new. First-pass analysis
  unchanged (high-entropy; no decode/key). NEW leads: total = 256 = 2⁸ (possible
  256-entry table/pad); leading digit non-uniform (4 rare, 6.6%).
- **DEEPER ATTACKS DONE 2026-08-21 (REPORT §22, `attack_codepages.py`) — all
  NEGATIVE.** Table/permutation ruled out (only 161 distinct of 256 → a
  repetition-bearing stream, not an S-box). Position-locked pad, index-into-runes
  (solved/unsolved/alphabet), and self-cipher (digit-as-shift) all read as
  gibberish vs their ceilings, control-validated. Consistent with a keyed
  pad/self-cipher (§13 wall). **Residual open (low prior):** a non-natural value
  map, a keyed reading, or external context that supplies the key.
- **Status.** The highest-prior *open* front (REPORT §16/§21); characterised as
  high-entropy, key-like, not a substituted message.
- **Method.** Re-transcribe from the page images non-OCR (two independent
  passes, reconcile) into `data/code_pages.txt`; then test the codes as (a) an
  **index** into the runic stream, (b) a **pad**, (c) a **self-enciphered**
  stream; correlate the 104 codes against page lengths / rune positions.
- **Control.** Any "decode" must beat the random n-gram ceiling and pass a
  planted round-trip; a verified transcription is the prerequisite, not optional.

## P2 — medium

### 4. Transcription cross-check: rtkd/iddqd vs the vendored scream314 stream
- **DONE 2026-08-21 — QUESTIONS §11 (REPORT §23, `compare_transcriptions.py`).**
  Full-file, the two transcriptions are near-identical (15938 vs 15933 runes,
  99.95%, only ~11 differing) and rtkd reproduces **all 86** unsolved doublets.
  So "transcription noise" is no longer supported: either copy error is ~10× too
  rare to explain the 0.66% doublet rate (→ real), or the two share lineage (→
  inconclusive). "Real doublets" favoured, not proven. Bonus: code pages
  corroborated (both 256 tokens, differ on ~6 case-ambiguous glyphs). NB an
  earlier draft's "~185 dropped runes" was a `parse()`-vs-full-file artifact —
  there is no dropped content.
- **Hypothesis.** Tests §4/§11's account that the 86 residual doublets are
  **transcription noise**: two independent transcriptions should disagree exactly
  where our anomalies sit.
- **Method.** Fetch rtkd/iddqd, align to our stream, diff; recompute doublet rate
  and the absent-bigram (B–B) on the alternate transcription; check whether
  disagreements concentrate on the 86 doublet positions.
- **Control.** n/a (a data-quality check) — report the disagreement rate and its
  location distribution honestly.

### 5. GP-sum / literal-ᚠ plausibility filter as a secondary decrypt scorer
- **Hypothesis (from §18).** A correct plaintext partitions at ᚠ/period into
  prime-length runs hitting themed GP totals (3301, 1033, anagrams).
- **Method.** Build a scorer that rewards that partitioning; fold in as a
  **tie-breaker** beside the n-gram English score in future attacks — never as
  the primary signal (§18's base-rate shows it is weak alone).
- **Control.** Must fire on solved pages and stay quiet on random plaintext.
- **Note.** Infrastructure — only pays off once an attack starts producing
  near-English candidates, which none currently do.

### 6. Magic squares decoded as a standalone message
- **Status.** Both "square is a *key*" readings are closed (additive §16,
  interrupter §17). What remains is the square as a puzzle in its own right.
- **Method.** Read the squares themselves — magic constants, the 3301−prime
  cells, the red-marked cell, the Möbius glyph, the palindromic prime centre —
  as a bespoke reading path, a per-page sub-square, or a coordinate/pointer set
  into the runes.

## P3 — low / opportunistic

### 7. Prime-indexed "hints never used" as key primers
- Low prior (2012–2015 artifacts, pre-LP2). Test the documented prime whitespace
  sequences (0,2,3,5,7,11,13,…) and the emirp cookie ids (167 / 761) as keystream
  primers / offsets on the unsolved pages, with the usual control + ceiling.

### 8. "AN END" deep-web hash page (non-cryptanalytic — logged only)
- The solved AN END page advertises a deep-web page that hashes to a specific
  SHA-512. That is an OSINT/hunt task, not a runic-cipher experiment; recorded
  for completeness, deprioritised.

---

## Out of reach (documented wall)
A **keyed CSPRNG re-roll pad** (`c = p + K`, one-time pad) is unbreakable without
the seed (§13) — the likely wall the runes sit behind. The numeric/image content
(P1.3, P2.6) is the way *around* it, not through it. Backlog items P1.1–P1.2 and
P2.5 attack the *structure* (ᚠ placement, GP sums) rather than the pad directly.
