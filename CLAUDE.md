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
3.45% random — a ~17σ deficiency; first differences are otherwise uniform).
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
favoured, not proven.

## What has been ruled out (all control-validated)

- Substitution, shifts, atbash; repeating-key Vigenère up to period 40.
- Prime/totient keystreams, ± directions, with/without key-skip.
- Autokey (plaintext/ciphertext fed), short primers.
- Running key, every way testable without the actual key text: key-text-free
  joint-English (intrinsically underpowered), self-referential keys,
  common-word key-crib (false positives at exactly the random rate).
- **Candidate running-key texts** (control-validated): KJV, Crowley's *Liber
  AL vel Legis*, the *Mabinogion*, Blake's *Marriage of Heaven and Hell* — the
  texts Cicada is documented to have used/referenced — whole text, every
  offset, both directions. (REPORT §6, §9.)
- **Short word keys + key-skip** over Cicada vocab + top ~1200 English words.
- **Coined/mangled thematic word keys** + key-skip: single-transform variants
  (C↔F/K/Q & S/Z, U/V collapses; atbash; rune reversal; vowel rotation) of the
  Cicada vocabulary. Closes the FIRFUMFERENFE=CIRCUMFERENCE gap.
- **Very-short key brute + key-skip** is *underpowered*, not a clean negative:
  key-skip freedom makes L≤4 keys non-identifiable and L≥5 isn't brute-forceable
  (`probe_shortkey_id.py`, REPORT §10).
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

- **Statistics/modeling:** `analyze_unsolved.py`, `doublet_sim.py`, `no_repeat_model.py`, `model_norepeat_mechanisms.py` (collision-resolution + residual-doublet discrimination, §11)
- **Attacks:** `crib_drag.py`, `attack_autokey.py`, `attack_keyskip.py`, `attack_runningkey.py`, `attack_keycrib.py`, `attack_running_text.py` (book keys), `attack_vigenere_skip.py` (word key + skip; `--mangle` for coined keys), `attack_shortbrute.py` (very-short key brute + chance-ceiling control), `difference_space.py` (cumulative-cipher tests on `c[i]−c[i-1]`), `attack_prng.py` (seeded-PRNG / hash-pad brute vs chance ceiling), `attack_magicsquare.py` (page-16/32 squares as additive keys, §16), `attack_magicsquare_interrupter.py` (page-16 square as a stride/gated/reset interrupter schedule, §17), `attack_literal_f.py` (literal-ᚠ rule as a keystream interrupter — pointer HOLDS at a ciphertext ᚠ; §19/P1.1)
- **Gematria structure:** `verify_gp_sums.py` (reproduces the r/cicada 3301/1033 GP-sum runs on solved plaintext + a boundary-freedom base-rate control, §18), `analyze_fpositions.py` (ᚠ-position structural map vs Monte-Carlo null; §20/P1.2), `compare_transcriptions.py` (aligns our stream vs rtkd/iddqd's; the doublet-noise test, §23/P2.4), `analyze_squares.py` (squares read directly as a message vs a numerology ceiling, §24/P2.6), `gp_filter.py` (the §18 GP-sum signature detector + control — fails to discriminate, deflates §18, §25/P2.5), `attack_hints.py` (pre-LP2 "hints never used" numeric sequences as keys/primers via the key-skip beam, negative, §26/P3.7)
- **Image content (not in the transcription, §15):** `data/pages/` (75 scans, gitignored — `bash fetch_pages.sh`), `results/page_glyph_catalogue_2026-08-20.txt` (per-page non-rune inventory), `data/code_pages.txt` (pages 66/67/68 — 256 codes, verified from scans §21) + `analyze_codepage.py` (loads all three pages; natural decodes) + `attack_codepages.py` (pad / index / self-cipher / permutation-table attacks, all negative §22)
- **Probes/modeling:** `probe_shortkey_id.py` (short-key identifiability under key-skip)
- **Infra:** `gematria.py`, `parse_lp.py`, `ciphers.py`, `language_model.py` (wordfreq n-gram, cached), `keytexts.py` (candidate key texts; ASCII-folds non-English source text), `mangle.py` (coined/mangled key-word generator, self-checked), `solved_text.py` (**verified plaintexts + `full_plaintext()`** — use this, not `english_plaintext()`, for anything about ᚠ or Gematria sums; §28C)
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

### What is actually still open

1. **Per-page / per-line key resets** (REPORT §5.3) — genuinely never tested.
   Segments bundle several .jpg pages, so this needs page-level splits first.
   Highest-value remaining rune-side idea.
2. **Running-key / word-key on the DIFFERENCE stream** (§12 remainder).
3. **Composed manglings** (§8), Emerson / Rune-Poem key texts (low prior).
4. **External routes**: the code pages need a key or community context; the
   AN END deep-web hash (§27) is an OSINT hunt, not cryptanalysis.

Out of reach for the RUNIC stream: a **keyed CSPRNG re-roll pad** (`c = p + K`,
unbreakable without the seed, §13) — the likely wall. The numeric/code content is
the way *around* it, and it is behind its own keyed pad.

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