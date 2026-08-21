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
residual doublets are transcription-noise-consistent (no key-period leak).

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
- **Gematria structure:** `verify_gp_sums.py` (reproduces the r/cicada 3301/1033 GP-sum runs on solved plaintext + a boundary-freedom base-rate control, §18), `analyze_fpositions.py` (ᚠ-position structural map vs Monte-Carlo null; §20/P1.2)
- **Image content (not in the transcription, §15):** `data/pages/` (75 scans, gitignored — `bash fetch_pages.sh`), `results/page_glyph_catalogue_2026-08-20.txt` (per-page non-rune inventory), `data/code_pages.txt` + `analyze_codepage.py` (the page 66-68 two-char code)
- **Probes/modeling:** `probe_shortkey_id.py` (short-key identifiability under key-skip)
- **Infra:** `gematria.py`, `parse_lp.py`, `ciphers.py`, `language_model.py` (wordfreq n-gram, cached), `keytexts.py` (candidate key texts; ASCII-folds non-English source text), `mangle.py` (coined/mangled key-word generator, self-checked)
- Runs archived under `results/`; candidate key texts + research briefing vendored under `download/` (PD); background research in `docs/cicada-3301-background.md`.

Deps: `pip install -r requirements.txt` (wordfreq, numpy). Caches
(`model_cache/`, `keytext_cache/`) are gitignored and rebuild on demand.

## The active lead — try this next

The **rune-cipher** campaign is exhausted (all control-validated): substitution,
Vigenère, autokey, prime/totient (§3); running keys and 4 documented key texts
(§6, §9); word/coined keys (§7, §8); difference-space cumulative family (§12);
naive seeded-PRNG pad (§13). The no-repeat mechanism is modeled (§11, uniform
resolution) and very-short brute is underpowered (§10). Colour/punctuation the
transcription flattens are cosmetic (§14).

BUT the investigation is **NOT** complete: a full page-image catalogue (§15)
found the transcription silently omits substantial **numeric/code content** the
rune-only toolkit never saw. That is the live front now:

1. **The two magic squares** (page 16 = 5×5 const 3301; page 32 = 4×4, cells =
   3301 − prime). Tested as *repeating keys* — negative (§16, `attack_magicsquare.py`)
   AND as an *interrupter/skip schedule* — negative (§17,
   `attack_magicsquare_interrupter.py`: stride/gated/reset over primes/totients/
   self/DIVINITY, both signs, control-validated, best at the chance ceiling). Both
   "square is a key" readings are now closed. STILL UNTESTED: a bespoke reading
   path, a per-page sub-square, or decoding the squares as a puzzle in their own
   right.
2. **The code pages** (66/67/68). Transcribed → `data/code_pages.txt`; §16
   (`analyze_codepage.py`) shows they are HIGH-ENTROPY (key-like, not a
   substituted message) — no natural decode reads English or keys the runes.
   Open: a verified (non-OCR) transcription of all three pages, page 73's hex,
   and community context; then treat as a pad / index / self-enciphered stream.
   **This is now the highest-prior live front.**
3. **Recurring marks**: the cuneiform cluster (50–56, likely a section motif),
   red pixel-blocks (line-ends), red verse numerals — probably structural.
4. **The literal-ᚠ steganography layer (§18, `verify_gp_sums.py`).** The r/cicada
   "56-57.jpg" observation reproduces exactly: on *solved* plaintext, deliberately
   placed/skipped ᚠ runes (GP value 2, the ±2 knob) make adjacent emirp-length
   rune-runs sum to 3301 and 1033 (a digit-anagram of 3301). This is a
   PLAINTEXT-side layer, **not a decryption lever** (GP sums aren't preserved
   through mod-29 addition, so uncheckable on ciphertext). Follow-ups run: the
   literal-ᚠ **interrupter** (P1.1, §19, `attack_literal_f.py`) and the ᚠ-position
   **structural map** (P1.2, §20, `analyze_fpositions.py`) are BOTH negative — no
   ᚠ fingerprint survives into the ciphertext, empirically confirming the caveat.
   Still live: (a) the GP-sum **plausibility filter** (BACKLOG P2.5) as a
   tie-breaker on any future candidate decrypt.

Lower-prior rune-cipher leftovers: composed manglings (§8), running-key/word-key
on the difference stream (§12), Emerson/Rune-Poem key texts.

Out of reach for the RUNIC stream: a **keyed CSPRNG re-roll pad** (`c = p + K` a
one-time pad, unbreakable without the seed, §13) — the likely wall the runes sit
behind. The numeric/code content above is the way *around* it, not through it.

NB — lesson (§14→§15): don't conclude "the images add nothing" from a handful of
pages; a full sweep found magic squares and a code page. Scale the evidence to
the claim.

Sober note: every keystream family — on the raw stream AND the differences — the
naive seeded-PRNG family, and every documented key text is now exhausted, all
control-validated. The realistic value is the narrowed hypothesis space, not a
break.

## Working style that fits this project

Small, verifiable steps; commit each finding with a clear message and archive
the run under `results/`; update LOG.md (chronological) and REPORT.md
(findings) as you go. Scale effort to the task; prefer a clean negative with
a control over a flashy maybe.