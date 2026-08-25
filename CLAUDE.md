# CLAUDE.md — Liber Primus cryptanalysis

Project memory for Claude Code. Read this first; it orients you to the state
of the investigation so you can continue without re-deriving anything. The
blow-by-blow history is in [LOG.md](LOG.md); the findings write-up is
[REPORT.md](REPORT.md).

## What this is

A toolkit attacking the **unsolved sections** of Cicada 3301's *Liber Primus*
(the "runes"), working from the transcription vendored at
`data/liber_primus.md` (from scream314/cicada3301). 25 parsed segments,
~15,750 runes; ~12,956 unsolved across 13 segments. The solved pages are all
reproduced by the toolkit (proof it's correct).

This started as a side-project inside a design-system repo and now lives on
its own at `github.com/jens-wedin/liber-primus`.

## Ground rules (do not violate)

- **Every claim is control-validated.** No attack result is trusted unless a
  *positive control* (encrypt known English with the hypothesised scheme, then
  recover it through the same pipeline) passes first. Several "results" were
  caught as pipeline bugs this way — always add/keep the control.
- **Be honest about negatives and coverage.** Most attacks return nothing;
  say so plainly, and state exactly what was and wasn't covered. Never dress
  up bigram-greedy gibberish (e.g. "YOU DYOUR AN") as a lead — a decoder that
  emits English-looking fragments from *random* input has no power.
- **Reproduce solved pages after any change to core code** (`python3
  validate_solved.py` → must print 9/9).
- **Run the tests: `python3 -m pytest` (from the repo root) → must be green.**
  See the Testing section below.

## Testing & TDD

`tests/` holds a pytest suite (`pip install pytest`, run `python3 -m pytest` from
the repo root). It is the robustness backbone in two layers:

- **Fast invariant suite (default, ~5s):** pins the invariants everything rests
  on — the 29-rune Gematria bijections, the cipher round-trips, the parse split
  (the canonical 12,947 unsolved runes), the null's independence in `controls`,
  the key-skip/soft-rule mechanics, English > random, the N14 code→byte map
  (256/256), and `validate_solved` 9/9 run as a subprocess. `python3 -m pytest`.
- **Slow control suite (`-m slow`, ~3min):** the plant-and-recover POSITIVE
  CONTROLS that back every power claim — `attack_keyskip`, `attack_derived_seed`,
  `attack_running_text`, `attack_vigenere_skip`, `attack_shortbrute`,
  `attack_prng`, `attack_autokey` and `difference_space` each recover a planted
  hypothesis through their own pipeline. `python3 -m pytest -m slow`.

**Run both before committing** (`python3 -m pytest -m ""` runs everything).

**Workflow going forward — TDD (RED → GREEN → REFACTOR):**
- New behaviour or a bug fix → write the failing test FIRST, watch it fail for
  the right reason, then write the minimal code to pass. No production code
  without a failing test first.
- Existing code → add characterisation/regression tests that lock in current
  behaviour (they pass now; their job is to fail loudly on a future regression).
- A bug becomes a test: reproduce it as a failing test, then fix. (This is how
  the `enc_key_skip` constant-key infinite-loop guard was added — the test
  witnessed the hang, the guard made it raise.)
- Keep the suite fast and green; run it before every commit alongside
  `validate_solved.py`.

## Verified cipher conventions (proven in `validate_solved.py`)

- Gematria Primus: 29 runes ↔ letters ↔ primes (`gematria.py`).
- Encryption is `c = (p + k) mod 29` in rune-index space.
- **Literal-ᚠ rule**: a plaintext F is written as an unencrypted ᚠ and consumes
  no key. But ordinary encryption can *also* yield ᚠ, so decryption of ᚠ is
  ambiguous — that's why solved pages are validated by forward *encryption*.
- Digraphs transliterate per word (TH, ING before NG, EA, AE, OE, IA/IO, EO);
  K→C, V→U, Q→CW.

## The central finding (REPORT.md §4)

The unsolved ciphertext is statistically a **uniform random stream with one
constraint: adjacent runes are almost never equal** (doublet rate 0.66% vs
3.45% random — a ~17σ deficiency, independently recomputed in §30; first
differences are otherwise uniform, though only to p≈0.04).
This is a *pure lag-1 effect*. It rules out substitution, every
periodic/independent keystream (Vigenère, running key, prime/totient), and
pure autokey/cumulative-sum. What survives: an output-stage **no-repeat
enforcement**, most likely a **key-skip** (the key pointer advances an extra
step to dodge a would-be doublet), which desynchronises the keystream ~3% and
is why fixed-position attacks fail. Modeled further (REPORT §11): the collision
resolution is **uniform** (deterministic bump/nudge ruled out) and the 86
residual doublets carry no key-period leak. §23 (P2.4) undercuts the old
"transcription noise" reading: a second transcription (rtkd/iddqd) reproduces all
86 doublets and disagrees with ours on only ~11 runes book-wide, so copy error is
too rare to explain them (→ real) OR the two share lineage (→ inconclusive) —
either way "transcription noise" is no longer supported; **real doublets** is
favoured, not proven. §44 (N7) gives the mechanism: the rule is **soft**, keeping
a would-be doublet with probability **p_keep≈0.19** (fitted 0.193, matching
Dukotah's 0.18), so the 86 doublets are the filter's acceptance leak — signal.
This is orthogonal to §11's uniform *resolution* (how a rejected doublet resolves);
§44 adds the acceptance *rate* on top.

## What has been ruled out (all control-validated)

- Substitution, shifts, atbash; repeating-key Vigenère up to period 40.
- Prime/totient keystreams, ± directions, with/without key-skip.
- Autokey (plaintext/ciphertext fed), short primers.
- Running key, every way testable without the actual key text: key-text-free
  joint-English (intrinsically underpowered — correctly self-diagnosed),
  self-referential keys *(§31: only at key offset 0 — ~0.1% of the hypothesis
  space; offsets 50/300 are provably invisible, so "exhausted" is NOT supported)*,
  common-word key-crib (false positives at exactly the random rate; §31 finds this
  arm near-powerless: 23-44% true-positive rate).
- **Candidate running-key texts** (control-validated): KJV, Crowley's *Liber
  AL vel Legis*, the *Mabinogion*, Blake's *Marriage of Heaven and Hell* — the
  texts Cicada is documented to have used/referenced — whole text, every
  offset, both SIGNS. (REPORT §6, §9.) **NB §31: "both directions" never meant a
  REVERSED key text — that is untested and high-prior (Cicada uses reversed
  gematria on solved pages 06-09); `attack_running_text.py --reverse` now exists.
  Also: only the first ~140 runes of each segment are scanned (~14% coverage).**
- **Short word keys + key-skip** over Cicada vocab + top ~1200 English words.
- **Coined/mangled thematic word keys** + key-skip: single-transform variants
  (C↔F/K/Q & S/Z, U/V collapses; atbash; rune reversal; vowel rotation) of the
  Cicada vocabulary. Closes the FIRFUMFERENFE=CIRCUMFERENCE gap.
- **Very-short key brute + key-skip** — **L=2 exhaustive is a clean negative;
  L=3 is NOT ruled out (no evidence).** The old "underpowered at L≤4" claim rested
  on a ranking bug (§30), but the L=3 brute (§33) shows only 1 of 10 planted keys
  survives against the full 24,389-key space — the search overfits any text to
  ≈−3.8 — so L≥3 is beyond this pipeline's resolving power. `probe_shortkey_id.py`
  samples 400 distractors and therefore OVERSTATES identifiability for a full
  brute; trust the brute's own coverage number, not the probe.
- **Deterministic collision-resolution** for the no-repeat rule (fixed bump /
  nearest-value nudge): the first-difference histogram is flat, so the
  resolution is uniform (REPORT §11).
- **Cumulative / chained cipher** (`c[i]=c[i-1]+m[i]`) via difference space:
  keyless, repeating-key Vigenère (≤40), and prime/totient — all negative; the
  difference stream `d=c[i]−c[i-1]` is as random as `c` (REPORT §12).
- **Seeded-PRNG / hash pad (naive)** via re-roll: 7 generators (glibc/NR/Java
  LCG, xorshift32, Mersenne, SHA256-of-counter) × seeds 0–20k + thematic, both
  signs — negative vs a random-text chance ceiling. A keyed CSPRNG pad is
  information-theoretically unbreakable without the seed (REPORT §13).

## Toolkit map

**Layout:** the modules live under `src/` — libraries in `src/core/`, every
`attack_*` in `src/attacks/`, diagnostics/probes in `src/analysis/`;
`validate_solved.py` stays at the repo root. **Run everything from the repo
root** (`python3 src/attacks/<name>.py`) so `data/` and `results/` paths resolve;
each script self-adds the `src/` subfolders to its path, so the flat imports
(`import gematria`, `from controls import …`) work unchanged. The names below are
bare — prefix the right subfolder.

- **Statistics/modeling:** `analyze_unsolved.py`, `doublet_sim.py`, `no_repeat_model.py` (mechanisms incl. `enc_soft` + `fit_p_keep` — soft-rejection fit p_keep≈0.19, §44/N7), `model_norepeat_mechanisms.py` (collision-resolution + residual-doublet discrimination, §11)
- **Attacks:** `crib_drag.py`, `attack_autokey.py`, `attack_keyskip.py`, `attack_runningkey.py`, `attack_keycrib.py`, `attack_running_text.py` (book keys), `attack_vigenere_skip.py` (word key + skip; `--mangle` for coined keys), `attack_shortbrute.py` (very-short key brute + chance-ceiling control), `difference_space.py` (cumulative-cipher tests on `c[i]−c[i-1]`), `attack_prng.py` (seeded-PRNG / hash-pad brute vs chance ceiling — RE-ROLL pads only), `attack_derived_seed.py` (derived hash-CTR seed + key-skip through the beam; reproduces Dukotah's control, §41/N6), `attack_gromark.py` (Gromark/chain-addition mod-29 primer brute + key-skip beam; L=2 is Fibonacci ⇒ covered by §3, L=3 negative, §42/N10), `attack_depth.py` (keyless depth detection by Smith-Waterman local alignment; power analysis — no power at LP scales, §43/N8), `attack_wordpos.py` (structural-position uniformity diagnostic; word/page clean negative, §45/N9), `analyze_readorder.py` (geometric reading-order diagnostic — the no-repeat deficiency is lowest in row-major order, so the "circumference peel"/Möbius transposes are refuted, §62/N23), `analyze_line_init.py` (the §45 line-initial anomaly vs an independent vision segmentation — resolved as a transcription artifact, §46/N19), `attack_padinvert.py` (LP2-as-pad inversion — U as running-key pad vs candidate texts + self-folds; negative, closed by uniformity, §47/N18), `attack_twovar.py` (non-additive AFFINE cipher c=a*p+k, all multipliers, key-skip beam; negative, §48/N12), `attack_hill.py` (digraphic 2×2 Hill cipher over GF(29); structural doublet-parity test refutes the "Hill explains doublets" claim + well-powered brute over all 682,080 invertible matrices, negative, §61/N22), `attack_repeats.py` (mine all exact ciphertext repeats vs a Smirnov null; coincidental, no Kasiski anchors, §49/N11), `attack_transpose.py` (ciphertext orientation fwd/rev/atbash/atbash-rev via the key-skip beam — mortlach's transform space; negative, §54/N3), `attack_oeis.py` (OEIS-mod-29 + arithmetic keystreams via the key-skip beam; refutes the no-output-rule doublet-suppressing keystream + negative, §50/N16), `attack_hintseeds.py` (unused-hint numerics — cookies 167/761, 2012 P.S. number — as keystreams/hash-CTR seeds/autokey primers; negative, §51/N15), `attack_magicsquare.py` (page-16/32 squares as additive keys, §16), `attack_magicsquare_interrupter.py` (page-16 square as a stride/gated/reset interrupter schedule, §17), `attack_literal_f.py` (literal-ᚠ rule as a keystream interrupter — pointer HOLDS at a ciphertext ᚠ; §19/P1.1)
- **Gematria structure:** `verify_gp_sums.py` (reproduces the r/cicada 3301/1033 GP-sum runs on solved plaintext + a boundary-freedom base-rate control, §18), `analyze_fpositions.py` (ᚠ-position structural map vs Monte-Carlo null; §20/P1.2), `compare_transcriptions.py` (aligns our stream vs rtkd/iddqd's; the doublet-noise test, §23/P2.4), `analyze_squares.py` (squares read directly as a message vs a numerology ceiling, §24/P2.6), `gp_filter.py` (the §18 GP-sum signature detector + control — fails to discriminate, deflates §18, §25/P2.5), `attack_hints.py` (pre-LP2 "hints never used" numeric sequences as keys/primers via the key-skip beam, negative, §26/P3.7)
- **Image content (not in the transcription, §15):** `data/pages/` (75 scans, gitignored — `bash fetch_pages.sh`), `results/page_glyph_catalogue_2026-08-20.txt` (per-page non-rune inventory), `data/code_pages.txt` (pages 66/67/68 — 256 codes, verified from scans §21) + `analyze_codepage.py` (loads all three pages; natural decodes) + `attack_codepages.py` (pad / index / self-cipher / permutation-table attacks, all negative §22) + `attack_steg.py` (JFIF-density provenance gate + appended-data scan; runic scans are 400-DPI re-saves / steg-dead, §52/N13) + `attack_codemap.py` (derives the code→byte map `byte = digit*60 + base62(0-9A-Za-z)`; reproduces rtkd's String 4 256/256, §53/N14 — the first POSITIVE; target vendored at `data/rtkd_string4.hex`)
- **Probes/modeling:** `probe_shortkey_id.py` (short-key identifiability under key-skip), `attack_interrupt29.py` (29-rune interrupter power analysis, §40/N1), `analyze_interruptdb.py` (verifies relikd's finished InterruptDB firsthand — the 29-rune interrupter §55/N1 and the modulo/alternating-alphabet sweep §56/N4, both negative)
- **Infra:** `gematria.py`, `parse_lp.py`, `ciphers.py`, `language_model.py` (wordfreq n-gram, cached), `keytexts.py` (candidate key texts; ASCII-folds non-English source text), `mangle.py` (coined/mangled key-word generator, self-checked), **`controls.py`** (detection floor + matched/shuffled ceilings + verdict renderer — route EVERY new attack through this; §29/R5), `solved_text.py` (**verified plaintexts + `full_plaintext()`** — use this, not `english_plaintext()`, for anything about ᚠ or Gematria sums; §28C)
- Runs archived under `results/`; candidate key texts + research briefing vendored under `download/` (PD); background research in `docs/cicada-3301-background.md`.

Deps: `pip install -r requirements.txt` (wordfreq, numpy). Caches
(`model_cache/`, `keytext_cache/`) are gitignored and rebuild on demand.

## State of play — the backlog is worked through (read this first)

The **rune-cipher** campaign is exhausted (all control-validated): substitution,
Vigenère, autokey, prime/totient (§3); running keys and 4 documented key texts
(§6, §9); word/coined keys (§7, §8); difference-space cumulative family (§12);
naive seeded-PRNG pad (§13); the literal-ᚠ interrupter (§19). The no-repeat
mechanism is modeled (§11, uniform resolution) and very-short brute is
underpowered (§10).

The **image/numeric front** opened by §15 is now also worked through:
- **Magic squares** — closed three ways: additive key (§16), interrupter
  schedule (§17), and standalone message (§24, page-32 marginal p≈8%).
- **Code pages 66/67/68** — transcription VERIFIED from the scans and page 66
  added (§21, 256 codes); pad / index / self-cipher / lookup-table all negative
  (§22). Only 161 of 256 codes are distinct, so it is a stream with repetition,
  not a table; byte encoding ruled out. Consistent with a **keyed** pad.
- **§18's literal-ᚠ GP-sum layer** — deflated to **numerology** (§25): the
  3301+1033 co-occurrence is exactly as common in shuffles of the same text
  (P=50%). No ciphertext fingerprint either (§20, on an underpowered test).
- **Doublets** — an independent transcription reproduces all 86 (§23), so
  "transcription noise" (§11) is out; real doublets favoured, not proven.
- **Pre-LP2 hints** — negative against a calibrated detection floor (§26).

**§28 is a self-audit that found and fixed real defects in §17–§27** (a verdict
rule that would have missed a break; a statistic that never implemented its own
test; vacuous controls; nulls that weren't the real battery). No headline
negative was overturned, but read §28 before trusting any margin quoted in
§17–§27.

### The RE-DO backlog (§28 self-audit) — ALL DONE (R1–R5)

The §28 audit found defect *classes* — e.g. a "near-English" verdict rule that
would report a real break as negative (`attack_magicsquare.py`'s own control
recovered below its own threshold), under-powered ceilings, and a null drawn from
the generator being brute-forced. The fix everywhere is an empirical **detection
floor** (plant → recover → use that score) plus trial- and length-matched
ceilings, implemented once in `controls.py`. **R1/R2/R3/R5 are done (§29)** and
every recalibrated negative held; **R4 is done too** — §30 (R4a, the statistical
core) and §31 (R4b, the attack scripts) audited the never-audited pre-session
work: three negatives were weakened, none overturned, and two coverage claims
were corrected. Read §28–§31 before trusting any margin quoted in §17–§27.

### What is actually still open (see BACKLOG.md, organised by status)

Through §51 the campaign closed eleven external-research items (N5–N12, N15, N16,
N18, N19) plus the older R/P backlogs — all control-validated negatives, no-power
findings, or resolved artifacts. `BACKLOG.md` is now organised by status; the
DONE table there lists each with its §. **Still open**, in rough priority:

- **N14 — deep-web-hash hunt.** The LOCAL halves are DONE: the code→byte map
  (§53: `byte = digit*60 + base62(0-9A-Za-z)`, page order 66,67,68 row-major,
  reproduces rtkd's String 4 256/256 after the 3l→3I fix); the hash battery on the
  verified bytes (§59: 132 renderings×algos, NEGATIVE vs the AN-END target); and
  all 6 of Dukotah's contested byte indices (§59: 25 via §53, plus 175/182/199/
  215/237 — all agree with rtkd). Only the **external OSINT preimage hunt** remains
  (find the page that hashes to the target; §27, out of scope for this toolkit).
- **N17 — publish the cryptodiagnosis** (write-up + post; Bean K4 precedent).
- **N10-ext — CLOSED (§60):** the per-segment (per-page primer) L=3 Gromark brute
  is negative (best real −4.17 vs floor −3.79); L≥4 set aside (compute-prohibitive,
  negligible prior). The primer brute is now parallelised (`brute_best workers=N`).
- **N20 — CLOSED (§58):** the 05.jpg appended blob is a scream314 corruption
  artifact; the independent krisyotam onion7 copy of the same page is a clean JPEG.

N13 (steg provenance gate) is done — §52: our runic scans are 400-DPI re-saves
(steg-dead); only the 9 intro pages keep the outguess fingerprint.

A second external-research sweep (2026-08-23) added N6–N17; condensed reports at
`results/external_research_2026-08-23_sweep2.md`.

Out of reach for the RUNIC stream: a **keyed CSPRNG re-roll pad** (`c = p + K`,
unbreakable without the seed, §13) — the likely wall. N6 (§41) sharpened it: a
SHORT-seed derived pad is finite and beam-attackable, so the wall is specifically
SEED ENTROPY and low-entropy thematic seeds are ruled out; only a high-entropy or
true external pad is out of reach. The numeric/code content (N13/N14) is the way
*around* the wall, and it sits behind its own keyed pad.

NB — two standing methodology lessons, learned the hard way this session:
- **Calibrate the decision threshold, don't assume it.** Plant the hypothesis,
  recover it, and use *that* score as the detection floor (§28A). An arbitrary
  "near English" cutoff silently rejected genuine breaks.
- **Nulls must match the real thing in length, composition and multiplicity**
  (§28B/D/E/H). Several "clean negatives" were resting on mismatched nulls.
- Also: `english_plaintext()` omits the keyed pages — use
  `solved_text.full_plaintext()` for anything about ᚠ or Gematria sums (§28C).

Sober note: every keystream family — on the raw stream AND the differences — the
naive seeded-PRNG family, every documented key text, and the numeric/image
content are now exhausted, all control-validated. The realistic value is the
narrowed hypothesis space, not a break.

## Working style that fits this project

Small, verifiable steps; commit each finding with a clear message and archive
the run under `results/`; update LOG.md (chronological) and REPORT.md
(findings) as you go. Scale effort to the task; prefer a clean negative with
a control over a flashy maybe.