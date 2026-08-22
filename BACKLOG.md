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

## R — RE-DO BACKLOG (opened 2026-08-21 by the §28 self-audit)

**STATUS 2026-08-21: R1, R2, R3 and R5 are DONE (§29). R4 in progress.**
Every recalibrated negative HELD — see §29 for the calibrated numbers. The
scripts now share `controls.py`, so a detection floor and matched nulls are the
default rather than a per-script choice.

The audit of §17–§27 found defect *classes*, not one-off slips. This section
lists work that must be **re-done** because the stated evidence does not support
the stated conclusion. Expectation: most of these will CONFIRM their negative —
the real scores sit far below even a corrected threshold — but as they stand they
are not established. Order is by risk (could the conclusion be wrong?).

### R1. Beam attacks whose verdict rule would report a REAL BREAK as negative — **DONE (§29)**
**Evidence (not speculation):** the beam adds a per-skip penalty and normalises by
len−1, so a genuine break scores ~−4.0, not ~−3.4. Any script that judges a beam
score by "near English" (`eng − 0.5` = −3.88) therefore rejects real breaks. This
was proven in §26 (planted keys recovered at 97–100% scored −4.00) — and:
- **`attack_magicsquare.py` (§16) — CONFIRMED BROKEN.** Its own planted
  CIRCUMFERENCE control recovers at **−3.90, below its own −3.88 threshold**: the
  script would call its own successful control "NO SIGNAL".
- **`analyze_codepage.py` (§21)** — same beam, same rule; its key test also
  reported the real best (−4.33) *above* its own ceiling (−4.40).
- **`attack_literal_f.py` (§19)** — same rule; never re-run with a floor.

**Fix:** replace the "near English" rule with an empirical **detection floor** —
plant each hypothesis, recover it, use the minimum recovered score as the
threshold (the pattern now in `attack_hints.py` / `attack_codepages.py`).
**Also report which hypotheses are non-identifiable** (fail to self-recover) as
NOT COVERED rather than negative.
NB `attack_magicsquare_interrupter.py` (§17) and `attack_prng.py` (§13) are
direct-decode, not beam — their thresholds are sound. Do not "fix" them.

### R2. Under-powered / mismatched chance ceilings — **DONE (§29)**
Ceilings took a max over 6 random draws while the real result is a max over 13
segments, and some were computed at a fixed length while short segments were
scored on 91–121 symbols (shorter sequences score higher).
- `attack_magicsquare.py` (§16), `analyze_codepage.py` (§21),
  `attack_shortbrute.py` (§10), `attack_literal_f.py` (§19).
- `attack_magicsquare_interrupter.py` (§17) — length mismatch only; the audit's
  matched ceiling puts the best real **0.37 BELOW** it, i.e. a *stronger*
  negative than published. Re-run to correct the record.
**Fix:** draws = number of real trials; compute the null at each segment's own
length.

### R3. An attack with no positive control at all — **DONE (§29): control added and it PASSES**
- **`attack_autokey.py` (§3)** has only a random-head chi² baseline — no planted
  autokey that must be recovered. That violates the project's own ground rule, so
  the autokey negative is currently unvalidated. (Checked: `attack_runningkey.py`
  and `attack_keycrib.py` DO calibrate — leave them.)
**Fix:** plant a known autokey encryption, confirm recovery, then re-run.

### R4. The pre-session work (§3–§16) has never been adversarially audited — **IN PROGRESS**
The two audits covered only this session. Everything older shares the same
patterns: `crib_drag.py`, `attack_keyskip.py`, `attack_vigenere_skip.py`,
`attack_running_text.py`, `attack_keycrib.py`, `attack_runningkey.py`,
`difference_space.py`, `probe_shortkey_id.py`, `model_norepeat_mechanisms.py`,
`analyze_unsolved.py`.
**Do:** run the same two adversarial passes (controls & power; null models) over
them, and check every "ruled out" claim in CLAUDE.md against its script.

### R5. Systemic fix — stop re-introducing these defects — **DONE (§29): `controls.py`**
Extract a shared `controls.py` providing `detection_floor(hypotheses, ...)` and
`matched_ceiling(length, trials, ...)`, and route every attack through it so
calibrated thresholds and matched nulls are the default rather than per-script
choices. Then re-run the whole suite and **diff the conclusions** against the
current REPORT.

### Not redos — genuinely open experiments (carried forward)
~~Per-page / per-line key resets~~ **done, §34 — decisive negative.** Remaining:
running-key & word-key on the difference stream (§12 remainder); composed
manglings (§8); Emerson / Rune-Poem key texts; extend `attack_keycrib` beyond key
offset 0 (§31 — currently ~0.1% coverage); re-run `attack_keyskip` with the
widened `--max-start 200` (§31: the old negative covered starts ~0-50 only);
restore `keytext_cache/kjv.u8` so §6 is reproducible at all.

---

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
- **DONE 2026-08-21 — NO EVIDENCE (downgraded by audit §28F)** (`analyze_fpositions.py`,
  REPORT §20). The positive reference was underpowered and never fired (~41 ᚠ),
  and the prime-gap row breaches the script's own band (Bonferroni p≈0.13). Not a
  clean negative. Gap-length emirp and word-edge tests sit flat vs a Monte-Carlo
  null; the prime-gap row (z≈+2.3) is the one that does not, and survives only
  multiplicity correction. Consistent with §18's caveat (the ᚠ layer is a
  plaintext property), but it does not prove no fingerprint exists.
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
  So "transcription noise" is no longer supported: either copy error is ~17× too
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
- **DONE 2026-08-21 — UNUSABLE, and it deflates §18 (REPORT §25, `gp_filter.py`).**
  *(Audit §28B: the first detector could not represent the signature at all — the
  3301 run is 74 runes, not prime. Re-implemented: 31 real vs shuffle-null 30.6,
  P=50.2%. Conclusion survives on valid evidence.)*
  The §18 signature does not discriminate: the real arrangement's 31 signatures
  vs a shuffle-null mean of 30.6 (P=50%). The co-occurrence is exactly as common
  in shuffles of the same runes; §18 is numerology. No tie-breaker worth folding in.
- **Hypothesis (from §18).** A correct plaintext partitions at ᚠ/period into
  prime-length runs hitting themed GP totals (3301, 1033, anagrams).
- **Method.** Build a scorer that rewards that partitioning; fold in as a
  **tie-breaker** beside the n-gram English score in future attacks — never as
  the primary signal (§18's base-rate shows it is weak alone).
- **Control.** Must fire on solved pages and stay quiet on random plaintext.
- **Note.** Infrastructure — only pays off once an attack starts producing
  near-English candidates, which none currently do.

### 6. Magic squares decoded as a standalone message
- **DONE 2026-08-21 — no message, but page-32 MARGINAL (REPORT §24, audit §28E).**
  Under a corrected permutation null: page-16 p=72% (sound), page-32 p≈8%. Values read
  directly (row/col/spiral/boustro → runes; page-32 prime structure; ASCII); the
  ASCII path only reproduces the known `rl)lr`
  numerology. At 16-25 symbols the test can't be decisive → "no evidence", not a
  strong negative. The squares' meaning stays their 3301/prime structure.
- **Status.** Both "square is a *key*" readings are closed (additive §16,
  interrupter §17). What remains is the square as a puzzle in its own right.
- **Method.** Read the squares themselves — magic constants, the 3301−prime
  cells, the red-marked cell, the Möbius glyph, the palindromic prime centre —
  as a bespoke reading path, a per-page sub-square, or a coordinate/pointer set
  into the runes.

### 9. Per-page / per-line key resets — **DONE 2026-08-22, decisive negative (§34)**
- `attack_pagekey.py`. The page/line structure came from rtkd's transcription
  (`%` page, `/` line), vendored for §23 — the blocker was solvable all along.
  32 schedules (reset0 / reset_i / none x prime,totient,DIVINITY,FIRFUMFERENFE x
  both signs x ±key-skip). **32/32 identifiable, floor −3.38 at 100% accuracy;
  best real −6.46 (page) / −6.49 (line), ~3.1 BELOW the floor**, and the winning
  mechanism on real text is the continuous baseline — resetting helps not at all.
  Closes the last structural explanation for §3's failure that did not require an
  unbreakable pad.

## P3 — low / opportunistic

### 7. Prime-indexed "hints never used" as key primers
- **DONE 2026-08-21 — NEGATIVE, with demonstrated power (REPORT §26, audit §28A).**
  The original verdict rule would have missed a real break; re-run against an
  empirical detection floor (−4.00) — real best −4.38 sits 0.38 below it. 3 of 9
  keys are NOT COVERED (non-identifiable even when planted). The 2012/2014
  whitespace prime sequences, cookie emirps 167/761 (digits, mod 29, and as
  start-offsets into prime/totient), and the "missing primes" 73…1223, all through
  the key-skip beam: control PASS, ceiling −4.65, best −4.38 (~1 below English) —
  gibberish. Pre-LP2 hints don't key the unsolved pages.

### 8. "AN END" deep-web hash page (non-cryptanalytic — logged only)
- **DOCUMENTED 2026-08-21 (REPORT §27).** The AN END SHA-512 = page 73's hex
  (confirmed §21). Finding the page that hashes to it is a Tor OSINT hunt, not
  runic cryptanalysis — not actionable with this toolkit, recorded only.

---

## Out of reach (documented wall)
A **keyed CSPRNG re-roll pad** (`c = p + K`, one-time pad) is unbreakable without
the seed (§13) — the likely wall the runes sit behind. The numeric/image content
(P1.3, P2.6) is the way *around* it, not through it. Backlog items P1.1–P1.2 and
P2.5 attack the *structure* (ᚠ placement, GP sums) rather than the pad directly.
