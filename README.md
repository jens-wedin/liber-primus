# Liber Primus toolkit

A control-validated cryptanalysis toolkit for the **unsolved sections** of
Cicada 3301's *Liber Primus* — the runic pages that a decade of community effort
has not broken. It works from the rune transcription in
[scream314/cicada3301](https://github.com/scream314/cicada3301/blob/master/liber_primus.md)
(vendored at `data/liber_primus.md`): 25 parsed segments, ~15,750 runes, of which
~12,956 are unsolved across 13 segments. Every solved page is reproduced by the
toolkit, which is the proof the cipher model is correct.

- **Findings:** [REPORT.md](REPORT.md) (numbered §1–§52).
- **Blow-by-blow log:** [LOG.md](LOG.md).
- **What to run next:** [BACKLOG.md](BACKLOG.md) (organised by status).
- **One-page visual overview:** <https://jens-wedin.github.io/liber-primus/>
  (source in `index.html`).
- **Orientation for contributors (human or model):** [CLAUDE.md](CLAUDE.md).

## Purpose

Attack the unsolved runes, honestly. Two rules govern everything here:

1. **Every claim is control-validated.** No result is trusted until a *positive
   control* passes first — encrypt known English with the hypothesised scheme,
   then recover it through the same pipeline. Several early "results" were caught
   as pipeline bugs this way. Detection floors and matched chance ceilings
   (`controls.py`) are the default, not an afterthought.
2. **Be honest about negatives and coverage.** Most attacks return nothing; the
   value is a *narrowed hypothesis space*, not a break. A clean negative with a
   control beats a flashy maybe, and "no evidence" (an underpowered test) is
   reported as distinct from "ruled out".

## Status — unsolved, but sharply characterised

The unsolved ciphertext is, statistically, a **uniform random stream with one
constraint: adjacent runes are almost never equal** (doublet rate 0.66% vs 3.45%
at random — a ~17σ deficiency). This is a pure lag-1 effect. It rules out
substitution and every periodic or independent keystream, and points to an
output-stage **no-repeat rule** — a key-skip that advances the key pointer to
dodge a would-be doublet, desynchronising the stream ~3% and defeating every
fixed-position attack. The rule is **soft**: it keeps a would-be doublet about
one time in five (p_keep ≈ 0.19), which reproduces the exact 0.66% rate.

Ruled out, all control-validated: substitution/shifts/atbash; repeating-key
Vigenère; prime/totient keystreams; autokey; running keys (KJV, Crowley's *Liber
AL*, the *Mabinogion*, Blake, Emerson, the Anglo-Saxon Rune Poem); short and
coined/mangled word keys; affine (non-additive) ciphers; the difference-space
cumulative family; seeded-PRNG, derived-seed hash, Gromark and OEIS keystreams;
magic squares as key/interrupter/message; the code pages as pad/index/table;
per-page and per-line key resets; the literal-ᚠ interrupter; LP2-as-pad
inversion; and the pre-2014 hint numerics. The residual doublets are real
(reproduced by a second transcription), not copy-noise.

The likely wall is a **high-entropy or external keyed pad** (`c = p + K`),
unbreakable without the key — sharpened to *seed entropy*, since a short-seed
derived pad is finite and beam-recoverable but low-entropy thematic seeds are
ruled out. The numeric/image content (code pages 66–68) is the way *around* the
wall, and it sits behind its own keyed pad.

## History — Cicada 3301

*Cicada 3301* is the signature on three sets of public cryptographic puzzles,
each posted on or around **4 January** of **2012, 2013, and 2014**, plus a
handful of later signed messages. The stated aim was to *"recruit intelligent
individuals."* The group's identity and purpose have never been verified;
guesses range from an intelligence-agency recruiting tool to a cypherpunk
collective, an alternate-reality game, or a hoax — none confirmed. What follows
is the verified skeleton (see [docs/cicada-3301-background.md](docs/cicada-3301-background.md)
for sources).

- **2012** — The first puzzle appears on 4chan's /x/ board: *"We are looking for
  highly intelligent individuals."* The chain runs OutGuess steganography → a
  Caesar cipher → Reddit → **book ciphers** (the *Mabinogion*; Gibson's
  *Agrippa*) → a prime-number image → a phone number → `845145127.com` →
  **physical QR-code posters in ~14 cities worldwide** → a Tor site that
  collected email addresses. It ended with *"we have found the individuals we
  sought."*
- **2013** — A new, **PGP-signed** image opens the second round (signature
  verification becomes the anti-hoax rule). The chain uses a book cipher keyed to
  **Crowley's *Liber AL vel Legis***, an MP3 — *"The Instar Emergence"* — that
  XORs with Twitter data to yield the **Gematria Primus** rune table, and a
  bootable **"CicadaOS"** Linux image.
- **2014** — The third round leads to the **Liber Primus**, a ~74-page codex
  written entirely in Gematria Primus runes; the pages are released as JPEGs in
  a May 2014 file dump. This is the book this toolkit attacks.
- **2015–2017** — No new puzzle in 2015. Later Twitter messages follow (the
  6 Jan 2016 *"Liber Primus is the way"*). The **last verified PGP-signed
  message is ~29 April 2017**: *"Beware false paths…"* Nothing has been verified
  since.

**The Liber Primus is mostly unsolved.** Community summaries split it into **LP1
(17 pages, all solved)** and **LP2 (58 pages, only 2 solved — `56.jpg` and
`57.jpg`)**, leaving **56 pages unsolved** — the target here. The alphabet,
Gematria Primus, is a 29-rune Anglo-Saxon futhorc where each rune carries an
English letter or digraph and an ascending prime. A decade of collective effort,
this toolkit included, has broken no page beyond the two solved in 2014.

## Tests

A pytest suite in `tests/` pins the invariants the whole toolkit rests on — the
Gematria bijections, cipher round-trips, the canonical parse counts, the null's
independence in `controls`, the key-skip / soft-rule mechanics, English > random,
the N14 code→byte map, and `validate_solved` 9/9. Run it from the repo root:

```bash
pip install pytest
python3 -m pytest          # ~5s, should be all green
python3 validate_solved.py # the ground-truth check, 9/9
```

New work follows TDD: write the failing test first, then the minimal code to
pass (see the Testing section of `CLAUDE.md`).

## Repository layout

The Python lives under `src/`, grouped by role:

- **`src/core/`** — shared libraries (`gematria`, `parse_lp`, `ciphers`,
  `controls`, `language_model`, `keytexts`, `no_repeat_model`, …).
- **`src/attacks/`** — every `attack_*` (and `crib_drag`).
- **`src/analysis/`** — diagnostics, probes, and modelling (`analyze_*`,
  `compare_transcriptions`, `difference_space`, `model_norepeat_mechanisms`, …).
- **`validate_solved.py`** stays at the repo root (the canonical check).
- Non-code: `data/` (transcription, code pages, images), `docs/` (background),
  `download/` (public-domain key texts + research briefings), `results/` (dated
  run archives).

**Run scripts from the repo root**, so the `data/` and `results/` paths resolve —
e.g. `python3 src/attacks/attack_running_text.py`. Each script self-adds the
`src/` subfolders to its path, so the flat imports work regardless of which
folder a module sits in. `python3 validate_solved.py` works unchanged.

## Layout of the modules

| File | Purpose |
| --- | --- |
| `gematria.py` | The Gematria Primus table (29 runes ↔ letters ↔ primes) and transliteration both ways, including digraph handling (TH, ING, EA, …). |
| `parse_lp.py` | Parses the markdown into segments (section, key annotation, rune text). Run directly for an inventory. |
| `ciphers.py` | Cipher ops in rune-index space mod 29: shifts, atbash (reversed gematria), Vigenère, prime/totient keystreams — encrypt and decrypt, with Cicada's literal-ᚠ rule. |
| `validate_solved.py` | Reproduces every known solved page. Keyed pages are verified by *forward-encrypting* the known plaintext and comparing rune-for-rune. |
| `analyze_unsolved.py` | Statistics (IoC, periodic IoC, doublet rate) plus a battery of simple attacks over all unsolved segments. |
| `attack_autokey.py` | Brute force of plaintext- and ciphertext-autokey with short primers. |
| `crib_drag.py` | Word-aligned crib-dragging with the literal-ᚠ filter; tests implied keystreams for structure. `--selftest` recovers known keys. |
| `doublet_sim.py` | Simulates cipher families and measures which reproduce the observed (IoC 1.000, doublet 0.66%) signature. |
| `no_repeat_model.py` | Models the no-adjacent-repeat mechanism (re-roll vs key-skip) and quantifies the keystream desync. |
| `model_norepeat_mechanisms.py` | Sharpens the no-repeat model: shows the collision resolution is uniform (deterministic bump/nudge ruled out) and the residual doublets are transcription noise with no key-period leak. |
| `attack_keyskip.py` | Beam-search attack on the key-skip hypothesis over prime/totient streams. `--selftest` proves 98% recovery when the hypothesis holds. |
| `attack_runningkey.py` | Key-text-free running-key attack (joint English-ness of plaintext and key). Self-calibrates and reports when it is underpowered. |
| `language_model.py` | Frequency-weighted n-gram model (order 2–4) over rune indices, built from the `wordfreq` English list with Stupid Backoff. Run directly for the English-vs-random discrimination test. |
| `attack_keycrib.py` | Candidate-key attacks: self-referential running keys via key-skip (Part A) and a common-word key crib with a random-ciphertext false-positive control (Part B). |
| `keytexts.py` | Loads/caches candidate running-key texts (KJV from the `bible-kjv` npm package; any plain-text file, ASCII-folded so non-English texts don't crash) as rune streams. |
| `attack_running_text.py` | Tests any book as the running key against the key-skip hypothesis: trigram coarse scan → key-skip beam confirm, with a planted positive control (planted at the key's midpoint, so short texts work too). |
| `attack_vigenere_skip.py` | Short word key (Vigenère) + key-skip desync: beam-decodes Cicada/common word keys, with a planted positive control. `--mangle` also tests coined/mangled variants (the FIRFUMFERENFE=CIRCUMFERENCE family). |
| `mangle.py` | Coined/mangled key-word generator (consonant-collapse, atbash, reversal, vowel-rotation), self-checked to reproduce CIRCUMFERENCE→FIRFUMFERENFE. |
| `attack_shortbrute.py` | Exhaustive very-short (len 2..L) key brute + key-skip, judged against a random-ciphertext chance ceiling (short keys are underpowered under key-skip — see below). |
| `probe_shortkey_id.py` | Measures how identifiable a length-L key is under key-skip (ranks a planted key against random ones). |
| `difference_space.py` | Tests the cumulative/chained-cipher family on the first-difference stream `c[i]−c[i-1]` (keyless, repeating-key Vigenère, prime/totient), with planted controls. |
| `attack_prng.py` | Seeded-PRNG / hash-pad brute (LCG/xorshift/Mersenne/SHA-of-counter over small + thematic seeds) for the re-roll hypothesis, judged against a random-text chance ceiling. |
| `controls.py` | **The shared statistical spine** — detection floor (plant → recover → read the score a real break gives), matched chance ceiling, and the verdict renderer. Every attack routes through it. `--selftest` proves the helpers. |
| `solved_text.py` | Verified solved-page plaintexts + `full_plaintext()` (use this, not `english_plaintext()`, for anything about ᚠ or Gematria sums). |
| `attack_derived_seed.py` | Derived hash-CTR keystream from a short seed + key-skip, through the beam (reproduces a parallel project's control; §41/N6). |
| `attack_gromark.py` | Gromark / chain-addition mod-29 primer brute + key-skip beam (L=2 is Fibonacci, covered by §3; L=3 negative; §42/N10). |
| `attack_twovar.py` | Non-additive **affine** cipher `c = a·p + k`, every multiplier, through the key-skip beam (§48/N12). |
| `attack_depth.py` | Keyless depth detection by Smith-Waterman local alignment — a power analysis (no power at LP unit lengths; §43/N8). |
| `attack_wordpos.py` | Structural-position uniformity diagnostic (word/line/page initials) — the ACA Interrupted-Key / acrostic test (§45/N9). |
| `analyze_line_init.py` | Checks the §45 line-initial anomaly against an independent vision segmentation — resolved as a transcription artifact (§46/N19). |
| `attack_repeats.py` | Mines every exact ciphertext repeat vs a Smirnov null (Kasiski; §49/N11). |
| `attack_oeis.py` | OEIS-mod-29 + arithmetic keystreams via the key-skip beam, and the refutation of a no-output-rule doublet-suppressing key (§50/N16). |
| `attack_hintseeds.py` | Unused-hint numerics (onion cookies, the 2012 P.S. number) as keystreams / hash seeds / autokey primers (§51/N15). |
| `attack_padinvert.py` | LP2-as-pad inversion — the stream as a running key against candidate texts and its own reflections (§47/N18). |
| `attack_steg.py` | JFIF-density steg provenance gate + appended-data scan on the page scans (§52/N13). |
| `attack_magicsquare.py`, `attack_magicsquare_interrupter.py`, `attack_literal_f.py`, `attack_codepages.py`, `attack_pagekey.py`, `attack_selfkey.py`, `attack_difference_keys.py`, `attack_mangle2.py`, `attack_interrupt29.py` | The image/numeric and structural fronts — squares, code pages, per-page resets, composed manglings, the 29-rune interrupter power analysis. See [CLAUDE.md](CLAUDE.md) for the full annotated map. |
| `download/` | Candidate key texts (Liber AL, Mabinogion, Blake — public domain) + the research briefing, with provenance. |
| `docs/` | Background briefing on Cicada 3301, the runes, and the ciphers. |
| `results/` | Archived run outputs, dated. |

## Usage

```bash
cd liber-primus                        # always run from the repo root
python3 src/core/parse_lp.py           # segment inventory
python3 validate_solved.py             # should print 9/9 checks passed
python3 src/analysis/analyze_unsolved.py   # statistics + simple-attack battery
python3 src/attacks/attack_autokey.py      # autokey brute force (a few minutes)
```

Most scripts need only the Python 3 standard library. The n-gram model
(`src/core/language_model.py`, and the `--order` paths of the beam attacks) needs
`wordfreq`, and `src/attacks/attack_running_text.py` also needs `numpy` —
`pip install -r requirements.txt`. Models are cached under
`src/core/model_cache/` (gitignored) and rebuild in ~3s on first use.

The KJV key stream for `attack_running_text.py` is built once from the
`bible-kjv` npm package (Project Gutenberg is often network-blocked):

```bash
npm pack bible-kjv && tar xzf bible-kjv-*.tgz               # gives package/dist/
python3 src/core/keytexts.py --build-kjv package/dist       # caches src/core/keytext_cache/kjv.u8
python3 src/attacks/attack_running_text.py --key kjv        # runs the attack + control
```

Any other candidate key text works too:
`python3 src/core/keytexts.py --add-textfile mybook.txt mybook` then
`--key mybook`. The public-domain texts Cicada is documented to have used or
referenced (Crowley's *Liber AL*, the *Mabinogion*, Blake) are vendored under
`download/` — all tested and ruled out (see [REPORT.md](REPORT.md) §9).

## The cipher conventions (verified, not assumed)

All of these are proven by exact-match forward encryption in
`validate_solved.py`:

- Encryption is `c = (p + k) mod 29` in Gematria Primus index space; the
  "shift up/down" wording in community notes refers to direction conventions,
  and the key numbers quoted there are often `29 − index`.
- **Literal-F rule**: every plaintext F is written as ᚠ *unencrypted* and does
  not consume a key value. Crucially, ordinary encryption can also produce ᚠ
  (e.g. M+I ≡ 0 in "WELCOME"), so a ciphertext ᚠ is ambiguous when
  decrypting — which is why validation encrypts forward instead.
- Digraphs are transliterated per word (TH, ING before NG, EA, AE, OE, IA/IO,
  EO), never across word boundaries. K→C, V→U, Q→CW.
