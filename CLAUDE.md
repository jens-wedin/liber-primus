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

## Toolkit map

- **Statistics/modeling:** `analyze_unsolved.py`, `doublet_sim.py`, `no_repeat_model.py`, `model_norepeat_mechanisms.py` (collision-resolution + residual-doublet discrimination, §11)
- **Attacks:** `crib_drag.py`, `attack_autokey.py`, `attack_keyskip.py`, `attack_runningkey.py`, `attack_keycrib.py`, `attack_running_text.py` (book keys), `attack_vigenere_skip.py` (word key + skip; `--mangle` for coined keys), `attack_shortbrute.py` (very-short key brute + chance-ceiling control), `difference_space.py` (cumulative-cipher tests on `c[i]−c[i-1]`)
- **Probes/modeling:** `probe_shortkey_id.py` (short-key identifiability under key-skip)
- **Infra:** `gematria.py`, `parse_lp.py`, `ciphers.py`, `language_model.py` (wordfreq n-gram, cached), `keytexts.py` (candidate key texts; ASCII-folds non-English source text), `mangle.py` (coined/mangled key-word generator, self-checked)
- Runs archived under `results/`; candidate key texts + research briefing vendored under `download/` (PD); background research in `docs/cicada-3301-background.md`.

Deps: `pip install -r requirements.txt` (wordfreq, numpy). Caches
(`model_cache/`, `keytext_cache/`) are gitignored and rebuild on demand.

## The active lead — try this next

Closed negative this round: coined/mangled word keys (§8), the documented
running-key texts (§9, joining KJV §6), and the cumulative-cipher family in
difference space (§12); the no-repeat mechanism is modeled (§11, uniform
resolution) and very-short brute is underpowered (§10). What remains, in rough
priority:

1. **The re-roll no-repeat variant as a seeded PRNG/hash pad** — the main live
   thread. §11 says the resolution is uniform, which fits a free pad; if that
   pad is a seeded PRNG or hash, the break is non-linguistic — search for the
   generator/seed, not English. No language model helps here.
2. **The page images** — interrupter positions the transcription may flatten;
   the only source of *new* information beyond the transcription.
3. **Widen the mangling** (lower prior after §8): *composed* transforms
   (atbash∘C→F), mangled *common* words. Keep both controls. NB very-short
   brute is out — underpowered (§10).
4. **Difference-space leftovers** (lower prior): a running-key *text* or a
   word-key-with-skip on `c[i]−c[i-1]` (§12 covered the periodic/prime families).
5. **Lower-prior key texts**: Emerson's *Self-Reliance*, the Old English Rune
   Poem (wikisource) via `keytexts.py --add-textfile`.

Sober note: every keystream family — on the raw stream AND the differences — and
every documented key text is now exhausted, all control-validated. The realistic
value is the narrowed hypothesis space, not a break.

## Working style that fits this project

Small, verifiable steps; commit each finding with a clear message and archive
the run under `results/`; update LOG.md (chronological) and REPORT.md
(findings) as you go. Scale effort to the task; prefer a clean negative with
a control over a flashy maybe.