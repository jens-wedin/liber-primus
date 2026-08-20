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
is why fixed-position attacks fail.

## What has been ruled out (all control-validated)

- Substitution, shifts, atbash; repeating-key Vigenère up to period 40.
- Prime/totient keystreams, ± directions, with/without key-skip.
- Autokey (plaintext/ciphertext fed), short primers.
- Running key, every way testable without the actual key text: key-text-free
  joint-English (intrinsically underpowered), self-referential keys,
  common-word key-crib (false positives at exactly the random rate).
- **KJV** as a running key (whole book, every offset, both directions).
- **Short word keys + key-skip** over Cicada vocab + top ~1200 English words.
- **Coined/mangled thematic word keys** + key-skip: single-transform variants
  (C↔F/K/Q & S/Z, U/V collapses; atbash; rune reversal; vowel rotation) of the
  Cicada vocabulary. Closes the FIRFUMFERENFE=CIRCUMFERENCE gap.

## Toolkit map

- **Statistics/modeling:** `analyze_unsolved.py`, `doublet_sim.py`, `no_repeat_model.py`
- **Attacks:** `crib_drag.py`, `attack_autokey.py`, `attack_keyskip.py`, `attack_runningkey.py`, `attack_keycrib.py`, `attack_running_text.py` (book keys), `attack_vigenere_skip.py` (word key + skip; `--mangle` for coined keys)
- **Infra:** `gematria.py`, `parse_lp.py`, `ciphers.py`, `language_model.py` (wordfreq n-gram, cached), `keytexts.py` (candidate key texts), `mangle.py` (coined/mangled key-word generator, self-checked)
- Runs archived under `results/`.

Deps: `pip install -r requirements.txt` (wordfreq, numpy). Caches
(`model_cache/`, `keytext_cache/`) are gitignored and rebuild on demand.

## The active lead — try this next

The mangled-key lead is **closed, negative** (REPORT.md §8): single-transform
coined variants of the thematic words + key-skip are ruled out. What that
result leaves open, in rough priority:

1. **Widen the mangling** in `attack_vigenere_skip.py --mangle` / `mangle.py`:
   *composed* transforms (e.g. atbash∘C→F), mangled *common* words (not just
   thematic), and a genuine very-short (<4 rune) brute force. Keep both
   controls (CIRCUMFERENCE and the coined PRESERVATION~atbash).
2. **More running-key texts** if reachable (Crowley's *Liber AL*, Blake,
   Milton) via `keytexts.py --add-textfile` + `attack_running_text.py`.
3. **Difference-space** (`c[i]-c[i-1]`) attacks; the re-roll no-repeat variant
   as a seeded PRNG/hash pad (non-linguistic — needs the seed/algorithm); the
   page images (interrupter positions the transcription may flatten). See
   REPORT.md §5.

Sober note: every keystream family testable without the actual key text is now
exhausted. The realistic value is the narrowed hypothesis space, not a break.

## Working style that fits this project

Small, verifiable steps; commit each finding with a clear message and archive
the run under `results/`; update LOG.md (chronological) and REPORT.md
(findings) as you go. Scale effort to the task; prefer a clean negative with
a control over a flashy maybe.