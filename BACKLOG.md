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

## N — FROM EXTERNAL RESEARCH (2026-08-23)

A deep-research sweep of the solver community. **Caveat: the run was cut short by
a session limit — 30 of 98 agents failed, including the synthesis step — so this
is a partial harvest, not an exhaustive survey.** Five claims came back
adversarially verified; I re-verified N2's artifact myself. Everything here is
outside the project's existing ruled-out list.

### N1. Interrupter over ALL 29 runes, not just ᚠ  — HIGH PRIORITY
§19 tested the literal-ᚠ interrupter and §17 tested square-driven schedules. Both
assumed the interrupter is **ᚠ**. relikd's *LiberPrayground* (InterruptDB)
generalises it: precompute best-interrupt sets and IoC for **all 29 candidate
interrupt runes**, all pages, key lengths ≤32, using the first 20 interrupt
occurrences (~1.4e10 ops, ~38 h, shipped as a database). It makes a 2^66
interrupt space tractable with a sequential look-ahead and a genetic search that
flips up to 3 interrupt bits at once.
- **Why it matters here:** this is a direct generalisation of the key-skip /
  desynchronisation model that §4 says the data demands, and the assumption it
  drops (interrupter = ᚠ) is exactly the one this project never questioned.
- **STARTED 2026-08-23 (§40, `attack_interrupt29.py`) — power analysis done, the
  attack itself still to build.** Measured: with an interrupt **oracle** the mean
  per-slot IoC is **1.886** (English ≈1.74) versus ~1.0 for noise, so the
  hypothesis is cleanly detectable in principle. The obstacle is quantified:
  **63% of ciphertext runes equal to the interrupt rune are coincidental**, not
  real interrupts, and each false skip desynchronises everything after it —
  collapsing 1.886 to 1.201. The naive all-occurrences version therefore has NO
  power and its control fails (0/6 planted pairs recovered), so it reports NO
  EVIDENCE rather than a negative.
- **Do next:** the interrupt **SUBSET** search (relikd's sequential look-ahead +
  genetic bit-flipping, first ~20 occurrences per page, ~1.4e10 ops / ~38 h).
  Score by per-slot IoC with the >=25-rune slot minimum in `attack_interrupt29.py`,
  and route through `controls.py` so the coverage and margin gates apply. The
  pay-off is unusually well defined: an oracle scores 1.886 against a ~1.0 floor,
  one of the widest separations any hypothesis here offers.
- Source: github.com/relikd/LiberPrayground (verified 3-0 by the research pass;
  repo not independently inspected by me).
- **UPDATE 2026-08-23 (sweep 2, verified from the raw db files):** relikd's
  `db/` directory ships the FINISHED search — ~20,100 rows of IoC per (section,
  interrupt rune, key length 1–32), objectives `db_high` and `db_norm`. The
  unsolved sections top out at db_norm 0.55–0.63 (English = 1.0). The solved
  control pages score 0.99–1.00. So the full 29-rune interrupter × polyalphabetic
  sweep is ALREADY a large independent negative. **Download `db/` and query it
  before building our ~38 h search.** Our remaining edge is the `controls.py`
  gating and any search past their first-20-occurrences bound.

### N2. The code pages are a 256-BYTE STRING, not a cipher object — HIGH PRIORITY
**Artifact verified firsthand.** `rtkd/iddqd`'s `byte-strings/byte-strings`
contains FOUR hex strings of **exactly 256 bytes each**. Strings 1–3 are the known
3301 byte strings, each annotated with the Tor hidden service it corresponds to.
**String 4 is "Matrix from pages 49-51 converted to hexadecimal"** — and pages
49–51 in unsolved-image numbering are full-set pages **66–68**, i.e. precisely our
code pages (§21).
- This gives §21's "256 = 2⁸" observation a *purpose*: the code pages are a
  256-byte object of the same class as byte strings that yielded hidden services —
  not a key or pad, which §22 ruled out independently.
- **Open problem (bounded and concrete):** our `d*62+b62` map does NOT reproduce
  their bytes — only 2–5 of 256 positions agree under any page ordering tried. So
  either our value map, the reading order, or one of the two transcriptions
  differs. **Deriving the correct code→byte map is a finite, checkable task**, and
  a second independent rendering of the same pages exists to check against.
- Already tested and negative: SHA-512 of String 4 (and of Strings 1–3) does not
  equal the "AN END" target hash, in raw, lower-hex-ascii and upper-hex-ascii
  forms; SHA-256 likewise.
- Source: github.com/rtkd/iddqd `byte-strings/byte-strings` (fetched and counted
  by me, 2026-08-23).
- **UPDATE 2026-08-23 (sweep 2):** provenance re-confirmed — the file labels
  String 4 "Matrix from pages 49-51 converted to hexadecimal" beside the three
  hidden-service hashes. Dukotah flags **6 contested bytes** at indices 25, 175,
  182, 199, 215, 237 (their ledger A-04) — resolve them from our scans (see
  N14). Their B-05 ran a 6-statistic battery on a SHA-256-CTR keystream seeded
  by this block and could NOT separate it from the real stream. The derived-pad
  reading of the code pages stays live (see N6).

### N3. mortlach's enumerable key-transform space — MEDIUM
Defines an interrupter *operationally*: any rune whose every plaintext occurrence
coincides with the same rune at the same ciphertext position (the literal-ᚠ rule
generalised), strips those positions, then searches **28×28 gematria rotation
pairs** with an atbash direction flag plus **L2R/R2L plaintext transposition** —
order 10³–10⁴ combinations per cipher function, i.e. enumerable rather than a key
brute force.
- **Not in our ruled-out list:** we have never tested rune-order transposition, nor
  systematic gematria rotation pairs.
- Source: github.com/mortlach/Liber-Primus-Rune-Decrypting (verified 3-0).

### N4. Alternating coprime alphabets ("modulo cipher") — LOW
Alphabet of length 3 alternating with one of length 4 → effective period 24.
relikd tested this under **both** interrupt semantics (interrupt pauses the
alternation vs pauses key rotation within an alphabet), mod 2 and mod 3, over 2²⁰
interrupt combinations, and reports a clean negative (no subgroup with notable
IoC). Worth only cheap independent confirmation. (Verified 2-1.)

### N5. Community consensus — no one else has broken it either
DEF CON 31 (2023), CicadaSolvers: LP1 = **17 solved rune pages**; LP2 = **58 pages
released May 2014, of which 2 were solved immediately** and the rest resist. No
claimed or verified partial break of any other page. This matches our own ledger
and is useful mainly as a negative datapoint: a decade of collective effort has
produced no partial break either. (Verified 2-1.)
- **UPDATE 2026-08-23 (sweep 2):** still true through Aug 2026. The
  CicadaSolvers quickstart (Apr 2025) confirms LP2 = 2 of 58 solved. No DEF CON
  32/33 talk exists. The 2025 solve claims (a "Full Translation" repo,
  "Anarchy = 0", an "outguess everywhere" wiki entry) are creative writing,
  philosophy, or contradicted by the wiki's own JFIF analysis.

### Second sweep, 2026-08-23 (N6–N17)

A second four-lane sweep ran to completion: status 2023–2026, steganography and
hashes, solver tooling, academic methods. The condensed reports with all URLs
are archived at `results/external_research_2026-08-23_sweep2.md`. The first
sweep's "not yet harvested" list is now covered. Everything below is deduped
against N1–N5 and the ruled-out ledger.

One critique from outside was checked against our code and does NOT apply to
the key-text battery: Dukotah claims rigid decoders score correct keys as
noise, but `attack_running_text.py` confirms hits with the key-skip beam and
its planted-skip control passes. The critique DOES apply to `attack_prng.py`
(§13, direct-decode) — see N6.

### N6. Derived-seed keystream through a skip-aware beam — DONE, NEGATIVE (§41)
**DONE 2026-08-23 (`attack_derived_seed.py`, REPORT §41).** Reproduction PASSES:
a SHA-256-CTR keystream from `CICADA3301` under key-skip is beam-recovered at
100% where rigid decode gets 56% — Dukotah's claim confirmed in our pipeline
(class, not byte). Real run NEGATIVE and well-powered: 116 thematic passphrases ×
4 hash framings × 2 signs, floor −3.73 (5/5 recover), ceiling −4.18, best real
−4.26 (0.53 below the floor, at the ceiling). Audit (step b) resolved:
`attack_prng.py` is scoped to re-roll pads, not buggy; the key-skip cell was
genuinely untested and is now closed for LOW-entropy thematic seeds. The §13
wall is sharpened to SEED ENTROPY. Extensions remain open: wider passphrases,
word+number combos, and the pencil-and-paper PRNG family (see N10).

Original entry:
Dukotah planted a SHA-256 counter-mode keystream (seed `CICADA3301`) under an
anti-repeat filter. Rigid decoding scored the correct seed at −6.835 — noise. A
skip-aware beam recovered it at −4.170 with 98.9% character recovery. So the
derived-seed lane is inside resolving power, but only with a beam. Our §13
battery is direct-decode, integer seeds 0–20k, re-roll semantics. The untested
cell: **thematic passphrase seeds × hash counter-mode generators × beam
decode**. Steps: (a) reproduce Dukotah's planted control first; (b) audit
`attack_prng.py`'s decode for the re-roll desync ambiguity (folds into R4);
(c) run the passphrase dictionary (Cicada vocab + mangles) through the beam
with `controls.py` floors. This is the concrete bridge across the §13 wall.
- Source: github.com/Dukotah/cicada3301 (README-verified; not yet reproduced).

### N7. Dukotah ledger cross-diff + soft-rejection model — DONE (§44)
**DONE 2026-08-23 (REPORT §44, `results/dukotah_ledger_diff_2026-08-23.md`).**
Same object to 0.07% (first 24 indices + first 10 page lengths match; 12,947 vs
12,956, hashes differ — the §23 delta). Ledger diff: B-21/R12-C1/R12-D2
independently confirm §13/§12/§28; imported negatives B-05 (pp49-51 as PRF/RC4
seed → keystream) and R12-A1 (CicadaOS pad); B-16 shows OUR beam-validated keytext
negatives stand where theirs don't; their B-04 = our N6. **Soft-rejection
reconciled:** fitted p_keep = 86/(12934/29) = 0.193 ≈ their 0.18, orthogonal to
§11's uniform resolution, reframing the 86 doublets as the filter's acceptance
LEAK (signal, per §23). New lane surfaced: **N18 / F-01 (below)**. Neither-ran
lanes map to our N9 (C-02), N12 (D-04), N6 extensions (B-08/B-02), D-03 (Z340
homophonic).

### N18. F-01 — LP2-as-pad inversion (from Dukotah's ledger) — MEDIUM
The unsolved 12,956-rune stream may be KEY MATERIAL, not a message. Use it (fwd /
rev, ±, atbash) as a running key against candidate plaintexts and the solved
pages. Neither project has run it. Genuinely new: every attack so far treats the
stream as ciphertext to decrypt, not as a pad to apply. Control: plant a known
text enciphered under the stream-as-key, recover it; route through `controls.py`.
Source: Dukotah ledger F-01.

### N7 (original note). Dukotah ledger cross-diff + soft-rejection model — HIGH, CHEAP
Dukotah ships `LEDGER.json` (57 hypotheses: 21 never-run, 18 open),
`PROBLEM.json` (ciphertext pinned by SHA-256), `verify_solution.py`, and
plant-and-recover benchmarks. Do: confirm we attack the same ciphertext object;
diff their ledger against our coverage; import anything neither project ran.
Also reconcile mechanisms: they model the no-repeat as SOFT rejection sampling
(p_keep≈0.18, 86 doublets = leak-through). Our §11 found uniform collision
resolution. Fit both on our stream in `model_norepeat_mechanisms.py` — the two
models predict different key-consumption rates, which sets beam width for every
skip attack.

### N8. Keyless depth detection via local alignment — DONE, NO POWER (§43)
**DONE 2026-08-23 (`attack_depth.py`, REPORT §43) — a power analysis, not a
scan.** The scorer works (positive control: rigid depth separates at L≥600), but
the method has NO POWER at LP scales, blocked two independent ways:
- The kappa signal is weak (English 0.062 vs 0.034), so even a desync-free test
  needs ~600 aligned runes; the key-skip desync caps a coherent aligned run near
  ~17 runes, so SW local alignment of planted depth OVERLAPS independent pairs at
  every length and gap.
- The real units are too short regardless: 54 pages 66–277 (median 263), 586
  lines 3–26 — none ≥600.
The real pairwise scan is NOT run (a null from a powerless instrument is not a
negative, §28). Keyless depth / key reuse is UNTESTABLE with this method, not
disproven. A longer-unit or stacked-depth variant would need external data.

Original idea:
Smith-Waterman-style local alignment between candidate depth pairs (page and
line splits): match when c1[i] == c2[j], gap penalty calibrated to the ~3% skip
rate. This detects a shared keystream DESPITE desync — Banburismus updated for
an irregular pointer, per the Lorenz/Tunny lesson. It is keyless, so it
complements §34, which tested specific reset schedules rather than pairwise
depth. Control: plant two segments sharing a key with 3% skips; null from
shuffled pairs via `controls.py`.

### N9. Word-position IoC diagnostic + word-synchronized keys — DONE (§45)
**DONE 2026-08-23 (`attack_wordpos.py`, REPORT §45; = Dukotah C-02).** Controls
pass (word-reset lights word-initials z 105; continuous key flat). PRIMARY CLEAN
NEGATIVE: word-initial (n=2898), all within-word positions, word-final, page-
initial UNIFORM — no word/page-synchronised key (ACA Interrupted-Key) and no
word/page acrostic. ANOMALY (not a break): line-initial non-uniform (z 7.19,
localised to position 1) but does not replicate (split-half 2.25/5.53), per-page
underpowered, weak corr with solved line-init — source unresolved → N19.

### N19. Line-initial anomaly — confirm with an independent line segmentation — DONE, ARTIFACT (§46)
**DONE 2026-08-23 (`analyze_line_init.py`, REPORT §46).** Tested §45's line-initial
skew against Dukotah's read4.json — a from-image VISION segmentation independent
of rtkd's `/` marks. Does NOT survive as a cipher signal: the vision interior is
flat, but BOTH edges are skewed toward the default class cls 0 (edge-
misclassification), and the two sources disagree on the pattern (rtkd asymmetric
initial-only; vision symmetric both-edge). With §45's weak split-half, the
line-initial skew is a segmentation/transcription ARTIFACT. §4 uniformity stands.

### N9 (original note). Word-position IoC diagnostic + word-synchronized keys — MEDIUM
The ACA "Interrupted Key" cipher restarts the keyword at word divisions, and LP
marks word divisions. Diagnostic first (an afternoon): IoC of runes grouped by
position-within-word, also within line and page. Any word-synchronized periodic
scheme spikes it; flat closes the family cleanly. On a spike: dictionary search
with restart semantics — a small change to `attack_vigenere_skip.py`.
- Source: CryptoCrack "Interrupted Key" solver documentation.

### N10. Gromark / lagged-Fibonacci mod-29 primer brute — DONE, NEGATIVE (§42)
**DONE 2026-08-23 (`attack_gromark.py`, REPORT §42).** Chain addition
k[i]=k[i-L]+k[i-L+1] mod 29 through the key-skip beam. Two results:
- **L=2 is Fibonacci mod 29, Pisano period 14** — all 841 primers period ≤14,
  already covered by §3. Not new coverage (analytic, no run needed).
- **L=3 (period 871, 24,388 primers) NEGATIVE.** Global stream, all primers ×
  both signs: floor −3.79 (3/5 identifiable), ceiling −4.29, best real −4.20 —
  0.41 below the floor, gibberish. Identifiability is partial and beam-invariant
  (a probe at beams 40/80/150 gave the same result): low-entropy primers are not
  identifiable at head 44, an intrinsic degeneracy.
**Still open (both compute-driven, low prior):** per-segment (per-page primer)
brute — only the global one-primer hypothesis was scored; and L≥4 primers / other
lags. Each 24k-primer brute is ~5 min; the run uses checkpointed foreground
slices because plain background jobs were reaped mid-run.

Original entry:
§13 covered machine PRNGs (LCG, xorshift, Mersenne, SHA-256). The
pencil-and-paper family is untested: mod-29 lagged-Fibonacci chains from short
primers — the ACA Gromark mechanism. 29⁵ ≈ 20.5M primers, cheap decrypt. Add as
one more generator in `attack_prng.py`, decoded per N6.

### N11. Long-repeat mining vs a Smirnov null — MEDIUM, HOURS
The wiki lists 5 repeated multi-rune ciphertext sequences book-wide (ᛞᛄᚢᛒᛖᛁ at
6555 & 12950; ᛒᛗᚱᚾᛗ at 5448 & 12001; gaps 1031–6533). A true 7-rune repeat in
a uniform stream has p≈0.5%. Mine ALL maximal repeats in our transcription and
test the count against a length-matched no-doublet (Smirnov) null. If
significant, the offsets are Kasiski anchors and key-reuse loci — feed N8.
- Source: uncovering-cicada.fandom.com/wiki/Frequency_Analysis_Unsolved_Pages.

### N12. Non-additive two-variable cipher functions — MEDIUM
mortlach's `key-drag` and `lp-decrypter` search arbitrary f(p, k): XOR-style,
multiplicative (p·k) mod 29, and lookup tables, each × interrupters × gematria
rotations × transpositions. Our whole campaign is additive-only. Dukotah's D-04
(non-additive ciphertext-feedback sweep) ran on 3 of 55 pages. Extends N3.
- Sources: github.com/mortlach/key-drag, github.com/cicada-solvers/lp-decrypter.

### N13. Close the steg front with our own controls — MEDIUM, CHEAP
Verified externally (sweep 2, first-hand): rtkd's outguess run over all 75
pages yields only known 2014 clues on the intro pages and null garbage on the
runic pages. Recompression destroys outguess payloads, so only original onion7
JPGs are valid targets. Do locally: (a) provenance gate — hash our 75 scans and
parse the JFIF density fields (outguess fingerprint: unit unknown, density
1×1), cross-check `krisyotam/cicada3301` `original-onion7/`; (b) reproduce the
outguess negative with a planted-embed control; (c) post-EOI tail scan +
DCT-χ² test. Also settles the low-credibility 2025 "outguess everywhere" claim.
- Sources: github.com/rtkd/iddqd `lp_outguessed/`;
  uncovering-cicada.fandom.com/wiki/Outguess_detection_visual_analysis;
  github.com/krisyotam/cicada3301.

### N14. String 4 → deep-web-hash battery; fix the 6 contested bytes — LOW-MED
Run our verified pages-66-68 codes and String 4 through the community harness
`cicada-solvers/Cicada-DWH-HashcatAttempts` (SHA-512, Streebog, more); check
their `results/` first for prior coverage. Separately, resolve Dukotah's 6
contested byte indices (25, 175, 182, 199, 215, 237) from our scans — direct
input to N2's code→byte map problem.

### N15. Least-tried unused-hints numerics as seeds — LOW
The two `p7amjopgric7dfdi.onion` cookie values (167=6941f7…, 761=7bc1e7…) and
the 128-digit 2012 P.S. number, used as (a) PRNG seeds in the N6 pipeline,
(b) autokey primers, (c) index streams mod 29. §26 covered the prime and
whitespace hints; these three are the least-tried items on the wiki list.
- Source: uncovering-cicada.fandom.com/wiki/Possible_hints_never_used.

### N16. Doublet-suppressing keystream families — LOW
Old wiki lead: integer sequences with near-constant first differences (e.g.
OEIS A061474) suppress doublets when used as stream keys. Systematize: search
keystreams whose first differences mod 29 avoid doublet-producing residues,
gated on reproducing ~86 residual doublets. `cadrypt` ships
`mod29_oeis_sequences` as ready candidate keystreams.
- Sources: oeis.org/A061474; github.com/localavaster/cadrypt.

### N17. Publish the cryptodiagnosis — HIGH EXTERNAL VALUE, not an attack
No peer-reviewed cryptanalysis of the Liber Primus exists. Bean's
"Cryptodiagnosis of Kryptos K4" (HistoCrypt) is the exact precedent: a
publishable diagnosis of an unsolved cipher. Our doublet/key-skip model plus
the control-validated elimination ledger fits Cryptologia or HistoCrypt.
Publication recruits the community that could supply the external key material
the code pages appear to need.

### Reusable external assets (sweep 2)
- relikd `LiberPrayground/db/` — the finished interrupter sweep (see N1).
- mortlach `runeglish-language-model-transition-probabilty-matrices` — an
  independent scoring model to cross-check our wordfreq LM.
- Dukotah `LEDGER.json` + `PROBLEM.json` + `benchmark/` (see N7).
- `krisyotam/cicada3301` `original-onion7/` — 61 raw files, provenance-cleanest
  image set (see N13).
- `cadrypt` `mod29_oeis_sequences` (see N16).
- Watch: `mortlach/RuneDecrypterPrime` (pushed 2026-08-23, README stub, assets
  in GitHub Releases — recheck periodically).

---

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
~~running-key & word-key on the difference stream (§12 remainder)~~ **done §38 —
word keys + Rune Poem/Liber AL/KJV on d, all negative, closing the cumulative
variant of both key families**; composed
manglings (§8); ~~Emerson / Rune-Poem key texts~~ **done §37 — both negative;
the Rune Poem is the strongest book-key negative (highest power, 0.50 below its
floor)**; ~~extend `attack_keycrib` beyond key
offset 0~~ **done §35 (`attack_selfkey.py`, 832 hyp/segment, negative)**; ~~re-run
`attack_keyskip` with `--max-start 200`~~ **done §35 (still negative; winners now
at starts 31/104, beyond the old bound)**; ~~restore `keytext_cache/kjv.u8`~~
**done 2026-08-22 (Gutenberg #10, 3,007,380 runes; §6's exact numbers are not
byte-reproducible — different edition — but the attack runs again, incl.
reversed)**.

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
