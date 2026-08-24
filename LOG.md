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

## 2026-08-18 — Session 3: doublet-signature simulation (the productive one)

Goal: use the 17σ doublet anomaly as a *filter* on cipher families instead
of brute-forcing blind. Built `doublet_sim.py`: synthesize English-in-runes
plaintext from the solved pages, encrypt it with each candidate family under
random keys (deterministic LCG, since Date/random are unavailable), and
measure IoC + doublet rate against the observed (1.000, 0.66%).

**Result — only two families reproduce the signature** (`results/doublet_sim_2026-08-18.txt`):

| family | IoC | doublet % |
| --- | --- | --- |
| plaintext (no cipher) | 1.78 | 2.3 |
| OTP / long random key | 1.00 | **3.4** |
| Vigenère period 5 / 13 | 1.05–1.16 | 3.4 |
| prime stream mod 29 | 1.00 | 3.2 |
| running key (English) | 1.06 | 3.7 |
| plaintext-autokey lag 1/2 | 1.11–1.14 | 3.8–6.0 |
| **ciphertext-autokey lag 1** | **1.00** | **1.65 (= plaintext F-freq)** |
| **no-repeat OTP (rejection)** | **1.00** | **0.00** |

Every independent-keystream cipher sits at the random 3.4% doublet rate —
**all of them are ruled out**. Only ciphertext-autokey (analytic: doublets
occur iff the plaintext rune is F) and a deliberate no-repeat construction
drop below it. The observed 0.66% sits between them.

**Decisive test — first-difference the real ciphertext.** If the scheme were
a pure cumulative sum / ciphertext-autokey (`c[i]=p[i]+c[i-1]`), then
`d[i]=c[i]−c[i-1]` recovers the plaintext and should show English IoC ~1.7.
It does not:

- raw unsolved: IoC 1.000, doublet 0.66%
- first-difference lag 1: IoC **1.02** (not English), doublet **3.37%** (normal)

So pure autokey/cumulative-sum is **ruled out** (no English emerges), but the
snap-back of the doublet rate to 3.37% under differencing proves the anomaly
is a **pure lag-1 effect**.

**Full characterization.** The first-difference histogram is uniform over all
28 non-zero values (χ² = 41 on 27 dof) with a single sharp notch at d=0
(0.66%). I.e. the ciphertext is statistically a uniform random stream with
exactly one constraint: **adjacent runes are almost never equal**. The 86
surviving doublets are spread evenly across all 29 runes (not concentrated at
ᚠ or any interrupter candidate), so the no-repeat property is near-total and
rune-independent, with a uniform ~0.66% leak.

**What this eliminates, rigorously:** OTP, Vigenère (any period), running
key, prime/totient streams (all leave doublets at 3.4%); monoalphabetic
substitution (IoC would be 1.78); pure autokey/cumulative-sum (no English on
differencing). What remains: a construction that forbids adjacent-equal
ciphertext runes — either built into the cipher (a skip/interrupter or
no-repeat rule) or a flattening cipher over a plaintext with that property
(but the solved plaintext's doublet rate is ~2.3%, not 0.66%, so this is a
cipher property, not a plaintext one).

Next: (1) test skip/interrupter models — a rule that inserts or re-keys to
avoid repeats; (2) hunt the exact leak mechanism behind the residual 0.66%;
(3) revisit crib-dragging under a "differences" model, since the meaningful
plaintext structure may live in `c[i]−c[i-1]` space.

## 2026-08-18 — Session 4: modeling the no-repeat mechanism

**Boundary test (where do the 86 leak doublets sit?).** Classified every
adjacent-equal pair as within-word vs across a • boundary: 0.63% within-word,
0.80% across-word (random 3.45% both). Equal suppression on both sides → the
no-repeat rule runs over the **continuous rune stream**; the • separators are
cosmetic and don't reset it. Kills the "boundary-reset" explanation for the
leak.

**`no_repeat_model.py` — mechanism class.** Only constructions that enforce
no-repeat at the cipher's *output* stage keep IoC flat while killing
doublets. Two of them reproduce the full fingerprint (c-IoC 1.00, doublet
~0.7% with a dittography leak, d-IoC ~1.02):
- **RE-ROLL**: free pad; if `c[i]==c[i-1]`, pick another key value. Keystream
  stays position-locked → a known keystream is still testable.
- **KEY-SKIP**: fixed keystream K (primes/totients/text); advance the pointer
  an extra step to dodge a doublet. This **desynchronises** K — ~3% extra
  hidden key consumption over the text. That desync alone defeats
  crib-dragging and every periodicity test, which is exactly what we see.

Residual 0.66% modeled as dittography (hand-copy symbol-repeat) — reproduces
a rune-uniform, boundary-independent leak of the right size.

**`attack_keyskip.py` — decisive test of prime-family key-skip.** A beam
search over {0,1,2 skips}/position, scored by the solved-pages bigram model,
resyncs a key-skip stream. Self-test: encrypt English with prime key-skip →
beam recovers **98%**. So the attack works when the hypothesis holds.

Run on all 13 unsolved segments (prime & totient, both signs, all 29 start
offsets, beam 250, head 180): **negative everywhere.** Best bigram −3.57
(random baseline −3.37; English ≥ −2.4), best word-score 0.08 (English
≥ 0.3). Archived in `results/keyskip_2026-08-18.txt`.

**Verdict.** The mechanism is output-stage no-repeat enforcement, and its
keystream is **not** a prime-family stream under key-skip. The desync finding
is the important structural takeaway: it explains, mechanistically, why a
decade of position-locked attacks (this project's included) return noise.

Next: (1) run the beam attack with a running-key hypothesis (English-text
keystreams) instead of prime families; (2) work crib-dragging in
first-difference space; (3) the re-roll variant leaves the keystream
position-locked — if the pad is actually a hash/PRNG with a seed, that's a
separate search.

## 2026-08-18 — Session 5: running-key attack (and why it's inconclusive)

Ran the running-key hypothesis without guessing a key text: a running key
means `c = p + k` with BOTH p and k English, so `attack_runningkey.py`
beam-searches the decomposition maximizing English bigrams in p AND in k at
once. No key text needed — it tests every English key simultaneously.

**Built-in calibration is the whole point, and it failed the test for
power.** Same decoder on known inputs (head 120, beam 800):
- uniform-random text → joint-bigram **−4.39**
- genuine running-key ciphertext → joint-bigram **−4.26**, and it recovered
  only **19%** of the known plaintext.

Genuine-vs-random separation is just **0.13** → the test is **underpowered**.
Confirmed the failure mode directly: decoding a *pure uniform-random* stream
yields `...YOUDYOURANCRETODYOU...` — visibly full of YOU/YOUR/THE/AND — and
its substring-dictionary score (0.25) is *higher* than the genuine
running-key's (0.17). The bigram-greedy decoder manufactures English-looking
fragments from noise.

**So the real segments scoring −4.30 to −4.44 (some nominally "above
threshold", teasing fragments like "END YTHNGPR", "NOT YOU") are NOT
evidence of a running key.** They sit exactly where random noise sits under
this decoder. Word-scores stay ~0.04 (English ≥ 0.3).

**Honest verdict: inconclusive.** This method can neither confirm nor exclude
a running key at Liber-Primus segment lengths — a known limitation of
running-key cryptanalysis (needs a candidate key text to crib, trigram+
models over full pages, or a known-plaintext anchor). Recording this as a
guard rail: the decoded fragments are a decoder artifact, not a lead. Script
prints its own UNDERPOWERED warning so nobody (including a future me) mistakes
the fragments for signal. Archived in `results/runningkey_2026-08-18.txt`.

Genuinely open, in priority order: (1) obtain/enumerate specific candidate
key texts (Cicada's own decrypted passages, canonical public-domain works)
and crib the KEY side; (2) trigram/4-gram models to raise the power of both
this and the key-skip decoders; (3) test the re-roll (position-locked pad)
variant as a seeded PRNG/hash stream; (4) cross-check the page images for
interrupter positions the transcription flattens.

## 2026-08-18 — Session 6: trigram upgrade

The bigram model came from ~1,875 runes of LP plaintext — hopeless for
trigrams (29^3 ≈ 24k cells). Network to Project Gutenberg is blocked by the
proxy (403), but PyPI is allowed, so built `language_model.py` from the
`wordfreq` 50k-word English list: each word transliterated to runes, n-grams
counted *weighted by word frequency*, scored with Stupid Backoff, cached to
`model_cache/`.

**The model is strong.** English-vs-uniform-random separation (mean
window score): bigram 2.56, trigram 3.13, 4-gram 3.77 (the old LP-only
bigram managed ~0.9). So on a *fixed* sequence the model discriminates
English from noise cleanly.

**Re-ran the two beam attacks with it:**

- **Key-skip** (`attack_keyskip.py --order 3`): self-test still recovers 96%
  of a genuine prime-key-skip text, and the model refs are now far apart
  (English −3.38, random −6.17). All 13 real segments score −4.8 to −5.0
  with word-scores ≤ 0.11 — nowhere near English. Prime/totient key-skip is
  now **robustly** ruled out, backed by a proper LM.
  (`results/keyskip_trigram_2026-08-18.txt`)

- **Running-key** (`attack_runningkey.py --order 3`): **still underpowered.**
  Genuine running-key ciphertext −4.59 vs uniform-random −4.56 (separation
  −0.03), true plaintext only 12% recovered. This is the important result:
  the model is demonstrably strong on fixed sequences, so the failure is
  **intrinsic to running-key**, not a model-power problem. When the decoder
  is free to choose the plaintext (key follows), it finds a both-English
  decomposition for *any* input — including random — so the true one never
  stands out at these lengths. Conclusion upgraded from session 5's "maybe
  trigrams fix it" to: **trigrams do not fix it; a running key cannot be
  broken here without a candidate key text to crib the KEY side.**
  (`results/runningkey_trigram_2026-08-18.txt`)

Net: the LM is reusable infrastructure; the key-skip negative is now solid;
and the running-key avenue is closed unless we supply specific key texts.
That makes candidate-key-text cribbing (open thread #1) the clear next step.
Dependency: `wordfreq` (requirements.txt); cache gitignored.

## 2026-08-18 — Session 7: candidate-key cribbing (running-key closed out)

Reconciliation up front: the doublet signature already rejects a *plain*
running key (it would show 3.45% doublets, not 0.66%). So a running key is
only viable *combined with* the no-repeat enforcement. `attack_keycrib.py`
runs two well-powered (trigram) tests, and a false-positive control.

**Part A — self-referential running keys via key-skip.** Fed the key-skip
beam decoder candidate key streams from Cicada's own corpus: the solved-pages
plaintext, and every other unsolved segment's runes (a page keyed by its own
runes is the degenerate p=c−c=all-F and is excluded — a first pass had an
identity-check bug because `Segment.indices` is a fresh-list property; fixed
to compare by section id). All 13 segments: best score −4.79, far from
English (−3.38). Self-referential running keys ruled out.
(`results/keycrib_A_2026-08-18.txt`)

**Part B — key-word crib.** Slid 500 common English words (len 6–10) as
candidate KEY fragments over every segment, decoded p = c − k, kept
placements where the plaintext fragment cleared the 10th-percentile
English-window trigram threshold AND contained a dictionary word. 6.43M
placements → 8,178 "hits" (0.127%). But they are mundane modern key words
('ONLINE', 'MARKET', 'DOCTOR') over 6–7-rune fragments that start with a
common word then dissolve ("YOUELL", "THEIRMAY") — classic running-key crib
noise.

**The control makes it rigorous.** Ran the identical crib on a uniform-random
ciphertext of the same total length: **8,203 hits / 6.47M = 0.127%**, versus
the real text's **8,178 / 6.43M = 0.127%** — identical to three decimals. The
real "hits" occur at exactly the chance false-positive rate. **Zero signal.**
(`results/keycrib_B_2026-08-18.txt`)

**Running-key is now closed out**, every way testable without the actual key
text: plain running-key rejected by the doublet signature (S4);
self-referential key-skip negative (A); key-word crib at pure chance rate
(B); free-decoder joint-English intrinsically underpowered (S6). A break now
requires either the *specific* external key text Cicada used, or the page
images (interrupter positions the transcription may flatten).

Remaining open threads: (1) the re-roll no-repeat variant as a seeded
PRNG/hash pad (a fundamentally different search — needs the seed/algorithm,
not a language attack); (2) obtaining specific candidate key texts (KJV,
Crowley, Blake, Mabinogion) — blocked here by the proxy, feasible with the
right allow-listed source; (3) image-level re-transcription. All three need
inputs outside this sandbox; the language-only avenues are exhausted.

## 2026-08-19 — Session 8: candidate running-key text (KJV)

Moved the toolkit to its own repo (jens-wedin/liber-primus) and continued
here. Tested the canonical running-key guess, the King James Bible.

**Getting the text.** Proxy blocks Project Gutenberg (403). PyPI/npm are
allowed, so pulled the `bible-kjv` npm package's verse JSON, stripped markup,
concatenated Genesis→Revelation, and transliterated to a 3,162,779-rune
stream (`keytexts.py`, cached, gitignored). Crowley's *Liber AL* is not on
npm/PyPI and Gutenberg is blocked, so it could not be tested — framework is
ready for a dropped-in text file.

**Attack (`attack_running_text.py`).** A 3.16M-rune key can't be beam-searched
at every offset, so: (1) a vectorised trigram coarse scan slides KJV past
several short windows per segment and ranks offsets by English-ness of the
implied plaintext; (2) the key-skip beam confirms the top offsets. Multi-
window makes it robust to the ~3% skips (a skip-free window localises the key
even if others are corrupted).

**Debugging that mattered** (the control caught every bug):
- Wrong decrypt sign in the control (enc is c=p+k ⇒ decrypt sign −1, not +1).
- Unigram coarse scan too weak to localise 1 offset in 3.16M → upgraded to a
  dense trigram table; then a single early skip still broke a single long
  head → multi-window scanning fixed it.
- coarse scan was 22s/call (int64 + repeated casts) → int16 rows + float32
  table brought it to ~1.1s.
Positive control now PASSES: plants KJV at offset 500000, recovers it at key
offset ~500079, ~100% of the window, trigram −3.4.

**Result: KJV ruled out.** Negative on all 13 segments — best decode trigram
−3.95 (gibberish), vs English/true-hit ≈ −3.4 (control −3.42). The whole
book, every offset, both directions. `results/running_kjv_2026-08-19.txt`.

Also removed the duplicate `liber-primus/` folder from the Manfred branch
(studio-manfred/manfred-design-system) so the toolkit lives only here.

Open threads unchanged: other specific key texts (Crowley, Blake, Mabinogion
— need a reachable source), the re-roll pad as a seeded PRNG/hash (non-
linguistic), difference-space analysis, and the page images.

### Session 8 (cont.) — short word key + key-skip

Couldn't reach more running-key texts (nltk gutenberg download host blocked;
npm book packages are code, not text). Pivoted to a real gap: the solved
pages use short WORD keys + an interrupter, but I'd only tested short keys
without desync, and desync only with prime/totient. `attack_vigenere_skip.py`
key-skip beam-decodes every candidate word key.

Debug: a straight-decode coarse filter is useless for short repeating keys —
one key-skip desyncs the key phase for the rest of the head, so the true key
(CIRCUMFERENCE) ranked ~4000/14000. Confirmed the confirm stage is fine
(true key → 98%). Fix: drop the coarse filter, beam every key over a bounded
word set. Control then PASSES (CIRCUMFERENCE rank #1, 83%).

Result: negative over Cicada vocab + top 1200 words (best −4.23 gibberish vs
English −3.38, genuine key −3.90). Rules out common/thematic dictionary word
keys — but NOT mangled/coined keys (the known FIRFUMFERENFE = CIRCUMFERENCE
with C→F is exactly such a non-dictionary key). Natural next: substitution
variants of thematic words, and very-short brute force.
`results/vigenere_skip_2026-08-19.txt`.

### Session 9 (2026-08-20) — coined/mangled word keys

Picked up the active lead: the one gap Session 8 left was Cicada's own habit of
mangling a key word (FIRFUMFERENFE = CIRCUMFERENCE, every C→F), which no
dictionary word list can reach. New `mangle.py` expands the thematic vocab into
coined variants using ONLY attested Cicada transforms: consonant collapse
C↔F/K/Q and S/Z, U/V; atbash (i→28−i, the page 06–09 cipher); rune-space
reversal; vowel rotation. `attack_vigenere_skip.py --mangle` beams the 121
variants through the existing (unchanged) key-skip pipeline.

Discipline: kept the CIRCUMFERENCE control and added a second one. The
generator has a ground-truth self-check (CIRCUMFERENCE→FIRFUMFERENFE via C→F,
PASS), and the run plants a *coined* key that is in no word list —
PRESERVATION~atbash — and requires the expanded space to recover that exact
sequence. First tried DIVINITY~atbash (only 73% at head 30 — a short 8-index
key desyncs too much), so I probed a handful of coined keys and switched to
PRESERVATION~atbash (100%, rank #1). Both controls PASS; `validate_solved.py`
still 9/9 (core cipher code untouched).

Result: **negative on all 13 segments.** Best decode trigram −4.13 (gibberish,
no words). The two positive controls (correctly-keyed short decodes at this
head length) land at −3.90 and −4.00; English is −3.38. Every real segment
scores *below even the known-correct-key band* — none looks correctly keyed.
Rules out single-transform coined variants of the thematic words.
`results/vigenere_skip_mangle_2026-08-20.txt`.

Coverage stated: thematic words only (not the common-word list), one transform
each (no compositions like atbash∘C→F), key length 4–16, 30-rune heads. Still
open: multi-transform manglings, mangled common words, very-short (<4) brute
force.

### Session 10 (2026-08-20) — very-short brute, more running-key texts, research

Housekeeping: `.DS_Store` → `.gitignore`.

**Very-short key brute.** Built `attack_shortbrute.py` (all 29^L keys, key-skip
beam). Its plant-and-recover control FAILED at L=2 — the planted key wasn't
recovered. Not a param bug: a 2-rune key is too short for key-skip to pin down.
Quantified it with `probe_shortkey_id.py` (plant length-L key, rank the true
key vs random distractors): true-key rank ~6/1500 at L=2, ~2 at L=3–4 (head 30),
~1 at L=5; a 60-rune head pulls L=3–4 to ~1 but leaves L=2 at ~6. So the
brute-feasible lengths (2–3) are underpowered and the identifiable lengths (≥5)
aren't brute-forceable — a 3-hour L=3 brute would return chance decodes, so it
was NOT run. Reframed `attack_shortbrute.py` to the honest test (like the §4
key-crib): brute real segments vs matched-length random ciphertexts. L=2 result:
real best −4.26 vs chance ceiling −4.23 → NO SIGNAL. Underpowered, not ruled out.
`results/shortkey_id_2026-08-20.txt`, `results/shortbrute_len2_2026-08-20.txt`.

**Research (subagent) → candidate running-key texts.** Dispatched a research
agent for the Cicada history, the runes/Gematria Primus, the ciphers, and — key
for us — the texts Cicada *used/referenced* as keys. Briefing in
`docs/cicada-3301-background.md` (Gematria table spot-checked against
`gematria.py`, exact). Highest priors: Crowley's *Liber AL* (2013 book-cipher
key), the *Mabinogion* (2012 key), Blake's *Marriage of Heaven and Hell*.
Downloaded (Gutenberg reachable now; sacred-texts 403s curl, got Liber AL via
firecrawl); vendored under `download/` (PD) + provenance README.

**Two pipeline fixes to run them.** (1) `keytexts.py` now ASCII-folds source
text (Æ→AE, NFKD accent strip) — the Welsh Mabinogion crashed `latin_to_indices`
on 'Æ'. (2) `attack_running_text.py`'s control planted at a hardcoded offset
500000, past the end of any short text; now plants at the key's midpoint, so it
works for Blake/Liber AL (tens of k runes), not just KJV.

**Running-key texts — all negative, control-validated.** Every control PASSED
(planted key recovered ~100% at trigram ≈ −3.5). Best real decodes: Liber AL
−3.97, Mabinogion −3.97, Blake −4.15 — all at the ~−3.95 gibberish floor (= KJV),
vs English −3.38. So the four strongest literary running keys (KJV + these three)
are ruled out. `results/running_{liberal,mabinogion,blake}_2026-08-20.txt`.
`validate_solved.py` still 9/9 (core untouched). REPORT §9, §10.

Open threads now favour difference-space (`c[i]-c[i-1]`) attacks and the
re-roll pad as a seeded PRNG — the running-key and short-key avenues are spent.

### Session 11 (2026-08-20) — overview site + modeling the no-repeat mechanism

Published a one-page overview: an esoteric-codex `index.html` (dark ink & gold,
Cormorant/EB Garamond, the 29-rune Gematria Primus band) summarising the central
finding, the ruled-out ledger, the key-text verdicts and the open threads, with
links out to REPORT/LOG/background. Live on GitHub Pages at
jens-wedin.github.io/liber-primus (main / root, `.nojekyll`); also seeded as a
Claude Design canvas. README links it.

Then §5.1: `model_norepeat_mechanisms.py` pushes past `no_repeat_model.py`'s
re-roll-vs-key-skip, on two fingerprint-decidable questions, each control-gated.
- (A) HOW is a collision resolved? Synthesised uniform no-repeat streams under
  different rules: a deterministic bump (c += k on collision) spikes the first-
  difference histogram at bin k (1.9x uniform); a uniform re-pick / key-skip
  stays flat (~1.1x). Real data is flat (1.11x) → resolution is UNIFORM;
  deterministic bump/nudge ruled out (no arithmetic interrupter to invert).
- (B) Are the 86 residual doublets noise or a leak? Rune-uniform (chi2 26 vs 28),
  memoryless gaps (CV 0.85), no periodicity (best T=31, permutation p=0.82 over
  2000 shuffles). A control planting INDEPENDENT doublets into synthetic streams
  of the same segment lengths behaves identically (p=0.80) → the test reads true
  noise as noise. So the residual is transcription dittography, no key-period
  leak. Low power at 86 events (caveat noted).

validate_solved.py still 9/9. `results/norepeat_mechanisms_2026-08-20.txt`.
REPORT §11; §5.1 closed. Sharper picture: near-total no-repeat with UNIFORM
resolution — consistent with a free re-roll pad or a pseudo-random key-skip,
which is why the linguistic attacks all die. Difference-space and the seeded-PRNG
(re-roll) angle are what's left.

### Session 12 (2026-08-20) — difference-space: the cumulative-cipher family

Took on §5.2. Key reframe: the fingerprint (uniform c, notch at d=0) is exactly
what a CUMULATIVE cipher c[i]=c[i-1]+m[i] with m!=0 produces — so d[i]=m[i] is
the meaningful stream, and if m=p+k, d is a plain keystream cipher. §4 only
killed the KEYLESS case (m=p, d would be English — it isn't). `difference_space.py`
tests the KEYED case, gated by planted controls: cumulative-Vigenere → d shows a
periodic-IoC bump 1.84 at the planted period (PASS); cumulative-prime →
key-subtract trigram −3.36 (PASS).

Real difference stream: negative everywhere. d-IoC 1.024 (random ~1.00, English
1.78); best periodic-IoC 1.03 @ period 35 (flat — no Vigenere period); d read as
plaintext trigram −6.49 (keyless cumulative re-confirmed dead with the trigram
model); prime/totient subtraction best −6.02 (random-level). So the cumulative /
chained family (keyless, repeating-key ≤40, prime/totient) is ruled out — the
differences are as random as the raw stream, consistent with §11's uniform
resolution. validate_solved 9/9. `results/difference_space_2026-08-20.txt`.
REPORT §12; §5.2 closed.

State of play: every linguistic / algebraic keystream avenue — on the raw stream
AND on the differences — is now exhausted and control-validated. The one live
thread left is the **re-roll pad as a seeded PRNG/hash** (non-linguistic: search
for the generator/seed, not a language model); the page images are the other.
Lower-prior leftovers: running-key text or word-key-with-skip on the difference
stream.

### Session 13 (2026-08-20) — seeded-PRNG / hash-pad (the re-roll pad)

Took on the main live thread. `attack_prng.py` brutes (generator, seed) for
p = c − K English. Framed honestly up front: a good PRNG + non-trivial seed is a
one-time pad, unbreakable without the seed (why c is uniform); so this only
reaches NAIVE/weak generators with SMALL/thematic seeds, and only the RE-ROLL
variant (K position-locked; a key-skip pad would desync and defeat position-
locked subtraction).

Battery: glibc/NR/Java LCGs, xorshift32, Mersenne Twister, SHA256-of-counter;
seeds 0..20000 + thematic (3301, years, gematria sums), both signs, tried global
(one seed) and per-segment. Control PASS — planted glibc seed 1234 recovered
exactly, trigram −3.57 (≈ English −3.38). Chance ceiling on random text −3.91
(bounds the multiple-comparison inflation over ~280k candidates/brute). Real
best −5.14 — BELOW the ceiling, i.e. no better than the same brute on random
text. NEGATIVE: these naive generators with small/thematic seeds are ruled out;
a keyed CSPRNG is not (and cannot be) touched. validate_solved 9/9.
`results/prng_2026-08-20.txt`. REPORT §13.

State: the linguistic/algebraic space is fully exhausted on both the raw and the
difference streams, and the naive-PRNG pad is ruled out. What genuinely remains
is the PAGE IMAGES (the only untapped source of new information); everything else
is either information-theoretically out of reach (a keyed CSPRNG pad) or a
lower-prior leftover.

### External lead reviewed + page images fetched (2026-08-20)

Reviewed a 2025 write-up (Echo446Ghq/Magic-Square-Solution) claiming to solve a
Liber Primus "page-16" 5x5 magic square (magic constant 3301, centre prime 809).
The square IS a valid magic square (verified: rows/cols/diagonals all 3301), but
the claimed decode is **numerology, not usable**: take the centre row
[626,620,809,620,626], reduce mod 256, read as ASCII -> 'rl)lr'. Mod-256-ASCII
has no basis in Cicada's Gematria Primus (runes<->primes); 'rl)lr' is not a
message; "100% ASCII validity" and "p<0.0001" are vacuous (every int mod 256 IS
a byte, and the "4 independent methods" all just re-read the same centre row);
the Nigeria-coordinate and digital-root "layers" are apophenia. Nothing to fold
into the toolkit; the square's provenance as a genuine LP artifact is itself
uncited.

Useful outcome: downloaded the full Liber Primus page images (75 scans,
2400x3600, ~50 MB) from the transcription's own source (scream314/cicada3301,
`assets/2014/liber-primus-complete`) into `data/pages/` (gitignored; rebuild with
`bash fetch_pages.sh`). Page 00 confirmed = the "Liber Primus" title page. These
feed the page-images thread — the one remaining lead.

### Page-images analysis — flattened features are cosmetic (§5 → §14)

Compared the scans to `data/liber_primus.md` on unsolved pages 50 & 57 and solved
page 06. The transcription flattens three things; the decisive test for each is
whether a SOLVED page carrying the feature still decodes exactly with it ignored.
- COLOUR: every page opens with a red illuminated drop-cap + a run of red runes,
  then black (systematic, incl. solved page 06). Monochrome transcription loses
  it — BUT solved page 06 (atbash+3, "A KOAN…") carries the red runes and
  forward-encrypts to an EXACT match treating all runes uniformly (validate 9/9).
  So red = rubrication, part of the normal cipher stream. Cosmetic.
- PUNCTUATION: besides `•` (3308×) the pages carry `"` (44×) and `:` (8×); the
  toolkit drops all non-rune chars. These appear in SOLVED segments too (page 06:
  22 `"` + 8 `:`) which still decode exactly -> plaintext punctuation (quoted
  koan speech), cosmetic; dropping is correct.
- ORNAMENT: page-local non-futhorc glyphs the transcription omits (cuneiform-like
  marks at the foot of page 50; tree/border art on 57). Outside the rune stream.
Faithfully captured: line breaks, `•` dots, `•••` dividers. The transcription's
stray digits are the TITLE page's hash (page 00), not embedded numbers -> no
numeric magic square in the book (re the 2025 claim).
Net: for cipher purposes the transcription is FAITHFUL — flattened features are
provably cosmetic (solved pages carry them and decode without them). Validates
the toolkit's input; closes the page-images lead as negative for the main stream.
Only open curiosity: the page-local ornamental glyphs (e.g. page-50 cuneiform),
worth cataloguing. REPORT §14. This exhausts the untapped in-transcription and
in-image leads for the main rune stream.

### Page catalogue — §14 was WRONG; the images carry magic squares & code (§15)

Catalogued all 75 scans (5 subagents; key pages verified firsthand). §14's "the
images add nothing" was drawn from 3 pages and is overturned: 21 pages carry
non-rune content absent from data/liber_primus.md, and some is real DATA:
- MAGIC SQUARES: page 16 = 5x5, magic constant 3301, palindromic, prime centre
  809 — IDENTICAL to the 2025 Echo446Ghq square, so THAT SQUARE IS GENUINE (I was
  wrong to doubt its provenance; only its mod-256->ASCII decode is numerology).
  Page 32 = 4x4 grid where every cell = 3301 - prime (verified: 2,3,5,7,13,23,43,
  79,149,263,463,829,1481,2593), 3299(=3301-2) in red, + a hand-drawn Mobius.
- CODE PAGES: page 67 = ENTIRE page of 104 two-char alphanumeric codes (digit 0-4
  + letter), no runes (verified firsthand); pages 66, 68 carry more; page 73 a
  hex block; page 05 a small palindromic numeric table.
- Marks: recurring cuneiform cluster (50-56, a section motif), red pixel-blocks
  at line-ends (50-56, 66, 70-74), red verse numerals (10,11,53-55), dot
  constellations (24,40,73).
Colour/punctuation ARE still cosmetic (§14 that part stands, proven by solved
pages). But the rune-only toolkit was blind to all this numeric/code content.
`results/page_glyph_catalogue_2026-08-20.txt`, REPORT §15.

Honest correction: the rune-cipher campaign (§1-§13) is exhausted, but the
investigation is NOT complete — the images opened a genuinely new front (two
magic squares + 100+ codes with obvious cryptographic intent). The user's
magic-square lead was right. Next: analyse page 16 / page 32 squares and the
page 66-68 code as possible keys for the unsolved runic pages, or a separate
cipher. Updated the overview site + canvas from "complete" to "a new front".

### Testing the new front — magic-square keys & code pages (§16)

(1) Magic squares as keys — `attack_magicsquare.py` derives keystreams from both
squares (page-16 5×5, page-32 4×4): row/col/unique/reversed mod 29, plus page-32
prime transforms (3301−value mod 29, GP-prime rune indices, prime ordinals);
key-skip beam-decoded on all unsolved segments, both signs, via the validated
word-key pipeline. NEGATIVE, control-validated: best −4.23 (gibberish) at the
−4.57 chance ceiling, English −3.38. Neither square is a repeating key under
these derivations. `results/magicsquare_2026-08-20.txt`. (Debug: first control
run FAILED because `positive_control` plants CIRCUMFERENCE and my key list didn't
contain it → fixed by adding it to the searched set; a negative behind a failed
control is worthless, so the fix mattered.)

(2) Code pages — pages 66/67/68 carry two-char codes (digit 0-4 + base-62 char).
Transcribed 67 (104 codes, full page) + 68 (72 codes above 4 rune lines — codes
spatially SEPARATE from runes) firsthand → `data/code_pages.txt`.
`analyze_codepage.py`: HIGH-ENTROPY in both positions (2nd char flat over 49/62
symbols max count 5, letters no English skew — 'q' appears 5×, primes at chance
density). So the codes are KEY-LIKE data, not a substituted message; no natural
decode (base-62; digit×26+letter; 2nd-char-alone) reads English (≈−6.6=random)
or keys the unsolved pages (−4.33, chance). Genuine unsolved sub-cipher;
hand-transcription caveat (mixed-case OCR).

Net: §15's new front is opened and characterised, not cracked. validate_solved
9/9. The magic squares are not keys (these derivations); the code pages are a
separate high-entropy cipher awaiting a verified transcription + more context.

### 2026-08-21 — square as interrupter schedule (§17) + r/cicada GP-sum check (§18)

(1) Interrupter schedule — the last open magic-square reading (CLAUDE.md §16.1).
`attack_magicsquare_interrupter.py` reads M16 (row/col/boustro/spiral) as a
repeating schedule driving three interrupter mechanisms — **stride** (pointer +=
1+(s mod m)), **gated** (extra skip when s mod k==0 / s prime), **reset** (pointer
→0 at trigger, the classic interrupted key) — over four base streams (primes,
totients, square-self, DIVINITY), both signs = 384 deterministic decrypts.
NEGATIVE, control-validated: positive control recovers the planted interrupter at
100%; chance ceiling −5.64, best real −5.66 (*at* the ceiling, English −3.38).
Winners cluster on high-stride/gated (heavy desync → randomise). Scope note:
`attack_keyskip` already covered skip-≤2 schedules over primes/totients; the NEW
ground was **reset** (beam can't express a pointer reset), larger strides, and the
square/DIVINITY streams — all negative. Additive (§16) AND interrupter (§17)
readings of the square are now both closed. `results/magicsquare_interrupter_2026-08-21.txt`.

(2) r/cicada "56-57.jpg: GP sums 3301 & 1033" (the second half of the task — the
thread the user linked). It is NOT a second magic square (my first web-search
guess was wrong); it is a **GP-sum observation on SOLVED parable plaintext**.
`verify_gp_sums.py` reproduces both exactly: `WE MUST SHED OUR OWN CIRCUMFERENCES`
= 30 runes GP 1031, +errant ᚠ → 31 runes = **1033**; the `…PILGRIM…SEEK OUT…
PAGE. PARABLE…INSTAR…SURFACE.` run = 75 runes GP 3303, minus one skipped ᚠ (−2) =
**3301**, splitting 37+37 at the period. Lengths 31/37/37 emirp; 1033 = anagram of
3301; the literal-ᚠ is the ±2 knob. Skeptic control (Part 2): a single target is
NOT rare given free boundaries + ±2 F (1033 hit 28× vs neighbours 24–31×; 3301
111× vs 100–128×) — the weight is the co-occurrence, not the arithmetic. Bearing:
a **plaintext-side ᚠ steganography layer**, not a decryption lever (GP sums aren't
preserved through mod-29 addition, so uncheckable on ciphertext). Use as a
plausibility filter for future decrypts + catalogue ᚠ positions on unsolved pages.
`results/gp_sums_verify_2026-08-21.txt`.

Reddit access note: the thread would not fetch (Reddit 403s datacenter IPs on
www/old/.json; no Wayback snapshot; redlib/jina mirrors blocked; Chrome extension
not connected). The user pasted the text; WebSearch alone had mis-summarised it as
a "second magic square". Lesson: get the primary source before modelling on a
search gloss.

### 2026-08-21 (cont.) — Uncovering-Cicada wiki sweep + experiment backlog

Indexed four wiki pages into the context-mode knowledge base (fandom WAF 403s
direct fetches; the ctx fetcher gets through; content persists for `ctx_search`):
Frequency_Analysis_Unsolved_Pages, Liber_Primus_Unsolved_Pages,
Possible_hints_never_used, and the portal. Findings recorded in
`docs/cicada-3301-background.md` (Addendum 2026-08-21):

- The community frequency analysis **independently replicates REPORT §4** (bigram
  840/12952, quadgram repeats 255 vs random ≈235 — random). Their "840 not 841"
  checked locally: the single absent bigram is **B–B**; 28/29 doublet types occur;
  drawing 0 B–B is a ~5% Poisson fluctuation, not a banned bigram (deflates the
  "extra constraint" reading). Noted in REPORT §4.
- Cross-check for §18: the pilgrim/SEEK-OUT run is the SOLVED "AN END" page
  (φ(prime) stream), transliterated "IT IS THE DVTY OF EVERY PILGRIM TO SEEC OVT
  THIS PAGE" — the "awkward SEEK OUT" is just C→K, V→U. §18 sits on solved text.
- New leads logged: rtkd/iddqd second transcription (diff vs vendored to test the
  transcription-noise account of the 86 doublets); mortlach/lp-decrypter; prime
  whitespace / emirp "hints never used" (low prior, pre-LP2).

Wrote **BACKLOG.md** (8 experiments, each hypothesis→method→control→priority) and
mirrored the top items on `index.html` ("The Trail Ahead" section + a BACKLOG
link card). P1: the literal-ᚠ interrupter on unsolved pages (the solved-page rule
never applied in an attack), the ᚠ-position structural map, and the code-pages
verified transcription. Both "square is a key" readings are now closed (§16/§17),
so the backlog pivots to ᚠ-structure and the numeric/image content.

### 2026-08-21 (cont.) — P1.1 + P1.2 run (both negative, §19/§20)

(P1.1) `attack_literal_f.py` — the literal-ᚠ rule as an interrupter on the
unsolved pages. New coverage vs key-skip: at a ciphertext ᚠ the pointer can HOLD
(advance by 0), which the key-skip beam (advance 1–3) cannot express. Beam over
{hold=F, advance} at each ᚠ, prime/totient/word keys, PURE + +SKIP, both signs.
NEGATIVE, control-validated: control recovers 100% incl. every literal-F position;
ceiling −4.79, best real −4.86 (below ceiling), English −3.38.
`results/literal_f_2026-08-21.txt`. Bonus: ᚠ is at chance (3.53% ≈ 1/29), which is
itself mild evidence against a literal-ᚠ rule on these pages.

(P1.2) `analyze_fpositions.py` — ᚠ-position structural map. Gap-length prime/emirp
and word-edge tests vs a Monte-Carlo null; solved plaintext as positive reference.
All consistent with random placement (emirp z −0.2, word-edge z −0.4). The lone
borderline — prime-gap z +2.7 — is a doublet-suppression artifact: correcting for
the removed ᚠᚠ (gap 1, non-prime) drops it to +2.3, within multiple-comparison
noise. Solved reference flat too. So no ᚠ fingerprint survives into the ciphertext
— empirically confirms §18's caveat. `results/fpositions_2026-08-21.txt`.

(P1.3) Code pages — verified transcription + re-analysis. The scans
(`data/pages/{66,67,68}.jpg`) are clean line-art and legible, so I read them
directly: pages 67 (104) and 68 (72) confirmed EXACT against the existing
hand-transcription (case included); page 66 transcribed for the first time (10×8
= 80 codes, below 3 rune lines + a red pixel-block). All 256 codes validate as
digit(0-4)+base-62; `analyze_codepage.py` now loads all three from
`data/code_pages.txt`. Re-run on the full set: §16 verdict holds — no natural
decode reads English (−6.48 ≈ random) or keys the pages (−4.33 vs −4.40).
New structural hints: total = 256 = 2⁸ (cross-checks the page-66 row count; maybe
a 256-entry table/pad), and the leading digit is non-uniform (0–3 ~60 each, 4
rare at 6.6%). REPORT §21, `results/codepage_2026-08-21.txt`. Remaining P1.3 work
(codes as an index into the runes / a pad / self-enciphered) stays open (P2/P3).

All three P1 experiments are now run; P1.1 and P1.2 negative, P1.3 transcription
complete + verified with the analysis unchanged (two new structural leads).

### 2026-08-21 (cont.) — code-page deeper attacks (P1.3 remainder, §22)

`attack_codepages.py` — pad / index / self-cipher / table on the verified 256
codes, all control-validated / ceiling'd. Table/permutation RULED OUT: only 161
distinct codes of 256 (95 repeats), no bijective map → a repetition-bearing
stream, not an S-box; the 256 = 2⁸ is a pad/message length, not a table size.
Position-locked pad: control PASS, best −5.73 vs −6.19 ceiling (gibberish). Index
into solved-plaintext/unsolved-cipher/alphabet: best −4.84 at its −4.76 ceiling (a
bag of English letters, no coherence). Self-cipher (digit as shift on the base-62
symbol): −6.2. All negative. `results/codepages_attacks_2026-08-21.txt`. The code
pages are now characterised as far as key-free analysis reaches — consistent with
a keyed pad/self-cipher (§13 wall). Structure carried forward: 256 = 2⁸ and the
4-ary+escape leading digit.

### 2026-08-21 (cont.) — P2.4 transcription cross-check questions §11 (§23)

Fetched rtkd/iddqd's master transcription (vendored to
`download/rtkd_liber_primus_transcription.txt`, CC-BY-SA) and aligned it to our
scream314 stream (`compare_transcriptions.py`). **Full-file the two are
near-identical: 15938 vs 15933 runes, 99.95%, only ~11 differing.** rtkd
reproduces ALL 86 unsolved doublets. Reading: either the 0.07% inter-transcription
error rate is ~10× too low for copy error to explain the 0.66% doublet rate (→
doublets REAL), or the two share lineage at 99.95% agreement (→ inconclusive).
Net: §11's "transcription noise" reading is no longer supported; "real doublets"
favoured, not proven. Updated REPORT §11 note + §23, index.html, CLAUDE.

Same-session correction: my FIRST draft claimed "0.994 ratio, 6 disagreements,
~185 runes rtkd has that ours drops" and overstated "REAL, overturns §11". That
was an artifact of comparing `parse()`'s 15750 SEGMENT runes against rtkd's full
15933 — a full-file vs full-file redo shows near-identity and NO dropped content
(diff −5); the ~188-rune gap is non-segment runes (solved-page reproductions in
prose). Corrected §23, the §11 note, index.html, CLAUDE, and BACKLOG (dropped the
bogus "recover 185 dropped runes" item). Lesson: compare like-for-like extractions
before drawing a conclusion, and don't assume independence from mere agreement.

Bonus that survives: rtkd transcribes the code pages too — both exactly 256 tokens
(corroborates the page-66 count §21); they differ only on ~6 case-ambiguous glyphs
(my `3l` vs rtkd `3I` ×3, plus l/L, s/S) — my §21 read stands bar those.
`results/transcription_compare_2026-08-21.txt`.

### 2026-08-21 (cont.) — P2.6 squares as a standalone message (§24, negative)

`analyze_squares.py` reads the page-16/page-32 square VALUES directly (row/col/
spiral/boustro → runes mod 29; page-32 3301−value → GP-index/prime-ordinal; ASCII
mod 256), vs a numerology ceiling (same battery on random grids). Nothing above
ceiling: page-16 −6.72 vs −4.60; page-32 −4.71 vs −2.09 (random grids score
higher → 16-25 symbols have no n-gram power). ASCII gives the known palindromic
`rl)lr` numerology, nothing more. The squares' meaning is their 3301/prime
structure, not a hidden message — but at this length the test can't be decisive,
so it's "no evidence" rather than a strong negative. `results/squares_message_2026-08-21.txt`.

### 2026-08-21 (cont.) — P2.5 GP-sum filter fails to discriminate; deflates §18 (§25)

`gp_filter.py` built §18's signature detector (adjacent prime-length runs summing
to 3301 AND 1033, ±2 F) as a would-be tie-breaker, and controlled it. Result: the
solved parable scores 7, but random 1875-rune text averages 10.9 (95th pct 17,
P(random≥7)=88%) — the real text is BELOW the random mean. So the conjunction is
common in random text; the filter can't discriminate and is unusable. Bigger point:
this deflates §18 further — even the co-occurrence it leaned on is within (below)
the noise, so §18 is best treated as numerology (verified arithmetic, no evidential
weight). Noted in §18 + new §25. `results/gp_filter_2026-08-21.txt`.

All P2 items now done: P2.4 (doublets favoured-real, §23), P2.5 (GP filter fails /
§18 deflated, §25), P2.6 (squares no message, §24). Net of the P2 tier: two clean
negatives, one honest revision (doublets), and a deflation of §18.

### 2026-08-21 (cont.) — P3 tier (§26/§27), closes the backlog

P3.7 (`attack_hints.py`, §26): the pre-LP2 "hints never used" numeric sequences as
keys/primers through the key-skip beam — 2012/2014 whitespace prime sequences,
cookie emirps 167/761 (digits, mod 29, and as start-offsets into prime/totient),
and the "missing primes" 73…1223. Control PASS; ceiling −4.65, best real −4.38
(~1 below English) → NEGATIVE. A few keys edge the noisy ceiling by tenths =
multiple-comparison chance. `results/hints_2026-08-21.txt`.

P3.8 (§27): the AN END deep-web SHA-512 (= page 73's hex, confirmed §21) — a Tor
OSINT hunt, not runic cryptanalysis; documented, not run.

BACKLOG P1–P3 now fully worked. Session net: §17–§27. No break; the value is a
comprehensively narrowed, control-validated hypothesis space, one honest revision
(§11 doublets likely real), and one deflation (§18 → numerology).

### 2026-08-21 (cont.) — SELF-AUDIT of the session's own work (§28)

Ran two adversarial audits over §17–§27 (one on the attack scripts' controls, one
on the statistical null models) plus my own claims-vs-archives check. They found
real defects. **No headline negative was overturned**, but several rested on
invalid evidence and are now re-grounded. All fixed in code and re-run; the
archived results/ files are the corrected outputs. Full detail in REPORT §28.

The serious ones:
- **§26 verdict rule would have MISSED a real break.** Planting the very keys
  under test and recovering them at 97-100% scored −4.00, below my −3.88
  "near-English" cutoff → the script would print NO SIGNAL on a total break of
  4/9 keys. Replaced with an empirical DETECTION FLOOR (plant → recover → use
  that score). Real best −4.38 is 0.38 below the floor, so the negative now has
  demonstrated power. Also: 3/9 keys aren't recoverable even when planted (now
  reported as NOT COVERED), and `missing_primes` == prime_stream[20:].
- **§25's detector never implemented its own test.** It gated both runs to prime
  lengths, but §18's 3301 run is 74 runes (not prime) — so it counted ZERO true
  signatures and compared noise to noise. Re-implemented + re-run on the full
  solved plaintext: 31 real vs shuffle-null 30.6, P=50.2%. Conclusion (§18 is
  numerology) SURVIVES, now on real evidence.
- **The English reference dropped a third of the solved text.** english_plaintext()
  omits every keyed page — including page 73 "AN END", the page §18 is about.
  New `solved_text.py` / `full_plaintext()` (2530 vs 1875 runes) fixes it; the
  plaintext constants are de-duplicated there and validate_solved still says 9/9.
- **§22's pad control was vacuous** (an algebraic identity that passes with the
  pad stubbed to zeros) and the self-cipher had no null at all. Both fixed;
  margins corrected for length. Byte-encoding hypothesis newly ruled out.
- **§24's null wasn't the real battery** (random grids make 3301−v rarely prime →
  3-5 symbol readings, and short sequences score high). Permutation null instead:
  page-16 p=72% (sound), page-32 **p≈8% — marginal, not the clean negative**.
- **§20 was overstated**: its positive reference silently failed (only ~41 ᚠ →
  can't reach z=3), and the prime-gap row breaches its own band (Bonferroni
  p≈0.13). Downgraded to "no evidence on an underpowered test".
- **§23**: the error rate wasn't like-for-like (~17× not ~10× within the analysed
  corpus). NEW finding: the transcription disagreements are systematically ᚠ —
  the ᚠ inventory itself is disputed, a caveat on every ᚠ-counting result.
- **Ceilings were under-powered throughout** (max of 6 draws vs max of 13
  segments). Matched, §17's best real sits 0.37 BELOW its ceiling (stronger than
  reported) and §26's ceiling moves −4.65 → −4.49.

Verified sound: 9/9 solved reproduction; the difflib alignment and 86/86 doublet
reproduction (independently re-derived); verify_gp_sums' headline sums and
base-rate control; §17's grid identifiability (48/48 planted mechanisms recovered
at 100%); the MC sampler; and every documented number matching its archived run.

Lesson recorded in CLAUDE.md: calibrate the decision threshold by planting and
recovering the hypothesis; make nulls match in length, composition AND
multiplicity.

### 2026-08-21 (cont.) — R-backlog execution: R5, R1, R2, R3 done (§29)

Plan was R5 first (shared controls) then R1 through it — that ordering paid off.

R5: wrote `controls.py` (self-tested): `detection_floor()`, `matched_ceiling()`,
`shuffled()`/`shuffle_ceiling()`, `verdict()`. Its own self-test immediately
caught a bug in MY earlier attack_hints fix: I had required BOTH a name match and
>90% accuracy, which demotes keys that rank first but decode imperfectly.
IDENTIFIABILITY (does the true hypothesis rank first? → defines the floor) is not
DECODE QUALITY (accuracy → reported separately). Fixing that raised §26's coverage
from 6/9 to 9/9 with the same negative.

R1 (all four now calibrated, all negatives HOLD):
  §16 attack_magicsquare  floor −3.95, best −4.23 (0.27 below), 8/9 covered
  §21 analyze_codepage    floor −4.00, best −4.33 (0.33 below), 4/4
  §19 attack_literal_f    floor −3.65, best −4.81 (1.17 below), 33/34; head 80→120
  §26 attack_hints        floor −4.00, best −4.38 (0.38 below), 9/9
Two coverage gaps now visible that the old scripts never reported: sq16_rev (§16)
and one §19 config are non-identifiable → no evidence either way for those.

R2: §17 interrupter now takes a ceiling at each segment's OWN length. Every
segment sits below its own ceiling (best margin −0.19) → negative is STRONGER
than the published fixed-length comparison suggested, as the audit predicted.

R3: attack_autokey.py had no positive control at all. Added one — planted
ciphertext- and plaintext-autokey both recovered (99%/100%, right method+sign) →
PASS, real segments word-score 0.00. §3's autokey negative is validated for the
first time. The control surfaced a real cipher property: a ciphertext-autokey
primer only supplies the first L key values, so the primer is essentially
unidentifiable — criterion is method+sign+recovery, not exact primer match. (My
first attempt used exact-primer matching and "failed" a 99%-accurate recovery.)

R4 (audit the never-audited §3–§13 scripts, incl. an independent recomputation of
the central finding) delegated to two adversarial agents — in progress.

validate_solved 9/9 throughout; controls.py self-test passes. REPORT §29.

### 2026-08-21 (cont.) — R4a: audit of the never-audited statistical core (§30)

CENTRAL FINDING CONFIRMED by independent recomputation (own parser, no project
helpers): doublet 0.6649% (86/12,934), z=−17.35, IoC 0.9998, lags 2–8 null (pure
lag-1). Sigma computed correctly (pairwise-independent indicators → exact
variance). Cross-segment concatenation immaterial (0 spurious doublets). Only
correction: "first differences uniform" is marginal (χ²41.2/df27, p≈0.04).

§10 REFUTED — and this one is a conclusion reversal, not a methodology tidy-up.
`probe_shortkey_id.py`'s "true key ranks ~6/1500 at L=2, NOT identifiable" was a
ranking bug with three compounding causes: distractors drawn WITH replacement
from an 841-key space (true key redrawn ~1.8×/trial, counted as beating itself);
`score_key` maxes over both signs so every key's sign-mirror decodes identically
and always tied; `>=` counted ties as beats. Fixed → rank 1.0 at L=2, 1.3 at L=3,
1.0 at L=4/5/6; 1.0 everywhere at head 60. So short keys ARE identifiable, the
L=2 brute is a CLEAN NEGATIVE, and the stated reason for never running L=3 is
void. L=3 brute (24,389 keys) launched.

CRITICAL contaminated null (§13): attack_prng drew its ceiling from LCG(700+d) —
the same NR LCG it brute-forces, seeds inside range(20000) — so it recovered the
null's own stream, decoded all-ᚠ, scored −3.91 vs a true ≈−5.25. Under that
inflated ceiling ~30% of genuine planted breaks read as negative. Root cause had
reached MY controls.py (same LCG in random_runes). Fixed: domain-separated
SHA-256 null + a self-test that no searched LCG seed reproduces it.

Weakened but not overturned: §11's "no key-period leak" only excludes a
POSITION-LOCKED leak (a period-31 leak with the ~3% drift key-skip itself causes
scores p≈0.07–0.18 → would read as "noise"); doublet_sim's fit band was 15× the
observed SE and mislabelled ciphertext-autokey (1.65%) a MATCH — tightened to
3 SE, now only no-repeat matches, agreeing with §4; difference_space (§12) has no
matched ceiling and its controls never enable the no-repeat notch (margin shrinks
0.32→0.08 nats when enabled) — negative survives on a narrower margin.

Sound: parse/gematria (independent reparse matches), validate_solved 9/9,
language_model (independent reimplementation matches to 1e-15), english_plaintext
has no ciphertext leakage, §11's permutation statistic correctly constructed.

### 2026-08-23 — External research sweep 2 (backlog N6–N17)

Four parallel research agents ran to completion: solve status 2023–2026,
steganography and hashes, solver tooling, academic methods. The first sweep
(N1–N5) lost 30 of 98 agents; this one covered every planned lane. Condensed
reports with all URLs: `results/external_research_2026-08-23_sweep2.md`.

Headlines:
- LP2 stays 2 of 58 solved. No credible break exists through Aug 2026.
- The doublet finding is now independently confirmed three times: the wiki's
  per-chapter table, Dukotah/cicada3301, and relikd's InterruptDB negative.
- relikd's `db/` ships the FINISHED 29-rune interrupter sweep as data. The
  unsolved sections top out at db_norm 0.55–0.63; solved controls hit
  0.99–1.00. That de-risks N1: query the db, skip the ~38 h rebuild.
- Dukotah/cicada3301 gives the sharpest current verdict: "OTP-class" with one
  open lane — a short-seed DERIVED keystream. Their planted control recovers a
  SHA-256-CTR seed by beam (−4.170) where rigid decode reads noise (−6.835).
- I checked their rigid-decoder critique against our code. It does NOT hit the
  key-text battery: `attack_running_text.py` confirms with the key-skip beam,
  and its planted-skip control passes. It DOES hit `attack_prng.py` (§13,
  direct-decode) — audit queued as N6, folded into R4.
- The steg front is closed externally: rtkd's outguess corpus holds only known
  2014 clues plus null garbage on the runic pages. N13 reproduces this with
  our own controls.
- No academic cryptanalysis of the LP exists. Bean's K4 cryptodiagnosis is the
  publication precedent (N17).

Backlog: N1, N2, N5 updated; N6–N17 added. No experiment ran; no REPORT
section. validate_solved untouched.

### 2026-08-23 (cont.) — N6: derived-seed hash pad through the beam (§41)

`attack_derived_seed.py`. Closes the key-skip × derived-seed cell that §13 left
open.

Audit first (N6 step b): `attack_prng.py` is scoped, not buggy. It decodes with
a position-locked subtract and plants a re-roll pad, so §13 is valid for re-roll
pads only. A key-skip derived pad desyncs and needs the beam — untested until
now.

Reproduction (the gate): plant CICADA3301 via SHA-256-CTR, key-skip 200 runes
(3 skips). Rigid decode −4.91 / 56% (desyncs); beam decode −3.56 / 100%. PASS —
reproduces Dukotah's claim in our pipeline (class reproduction, not byte).

Real run — NEGATIVE, well-powered. 116 thematic passphrases × 4 hash framings ×
2 signs, beam-decoded per segment + global. Floor −3.73 (5/5 seeds recover at
100%), ceiling −4.18, best real −4.26 (seed 'truth', global) — 0.53 below the
floor and at the ceiling, 0.45-nat margin. Global decode is gibberish. Rules out
low-entropy thematic hash-pad seeds under key-skip.

Caught and fixed a ceiling bug before trusting the run: the matched_ceiling call
passed extra=head*(skip+1)+16, which drew 192-rune nulls instead of 44 —
length-mismatched (biases the ceiling low) and 4x slower. brute() makes its own
keystream, so extra=0. Re-ran clean.

The reproduction proves the lane is attackable (a low-entropy seed IS
recoverable), so the §13 wall is now sharpened to SEED ENTROPY, not the derived-
pad idea. High-entropy seeds and a true external pad stay out of reach.
validate_solved 9/9. `results/derived_seed_2026-08-23.txt`.

### 2026-08-23 (cont.) — N10: Gromark / chain-addition primer family (§42)

`attack_gromark.py`. Tests the by-hand keystream: short primer extended by chain
addition k[i]=k[i-L]+k[i-L+1] mod 29, through the key-skip beam.

Analytic reduction first: L=2 chain addition is Fibonacci mod 29, Pisano period
14 — all 841 L=2 primers have period ≤14, already covered by §3. Only L=3
(period 871, 24,388 of 24,389 primers) is new. So N10 = the L=3 family.

Identifiability is partial and beam-invariant. A probe (5 plants, 1500
distractors, beams 40/80/150) showed the true primer beaten by ~1/1500 on a
low-entropy primer, 0 on the rest — SAME at every beam, so the degeneracy is the
44-rune head length, not the search. The full-space floor: 3/5 planted primers
rank #1 (floor −3.79); the 2 low-entropy plants are NOT COVERED.

Result NEGATIVE (global stream, one primer, all 24,360 L=3 primers × 2 signs):
floor −3.79, ceiling −4.29, best real −4.20 (primer (9,27,12)) — 0.41 below the
floor, gibberish decode, 0.50-nat margin. Demonstrated power for 3/5 primers.

Two coverage limits, both compute-driven: per-segment (per-page primer) brute
skipped (global-only); L≥4 untested. Carried to BACKLOG N10.

Harness lesson: plain background jobs were reaped ~25 min in (twice), so the run
uses brute-level checkpointing (results/gromark_ckpt.json, gitignored scratch)
driven as foreground timeout-slices that resume from cache. validate_solved 9/9.
`results/gromark_2026-08-23.txt`.

### 2026-08-23 (cont.) — N8: keyless depth detection, a power analysis (§43)

`attack_depth.py`. Depth = keystream reuse: c_A−c_B=p_A−p_B cancels the key, so
two in-depth units are detectable without it via the English difference
distribution. Key-skip desyncs the pointers, so Smith-Waterman local alignment
(gaps=skips) is used. Written as a power analysis (like §40): measure power
before scanning real pairs, because a null from a powerless instrument is not a
negative (§28).

NO POWER, blocked two ways:
- Signal weak: English kappa 0.062 vs 0.034. A desync-free coincidence test
  separates depth from independent pairs only at L≈600 (L=120/300 overlap,
  600/1200 separable) — this is also the positive control that the scorer works.
- Desync kills it: SW on planted key-skip depth vs independent pairs OVERLAPS at
  every L (300,600) and gap (−0.5,−1,−2). A coherent aligned run lasts ~17 runes.
- Real units too short anyway: 54 pages 66–277 (median 263), 586 lines 3–26 —
  none ≥600.

Verdict: the real pairwise scan is NOT run. Keyless depth / key reuse is
UNTESTABLE on the LP with this method, not disproven. No core change;
validate_solved still 9/9. `results/depth_2026-08-23.txt`.

### 2026-08-23 (cont.) — N7: Dukotah ledger cross-diff + soft-rejection fit (§44)

Fetched Dukotah/cicada3301 PROBLEM.json + LEDGER.json (57 entries). Two parts:

Same object to 0.07%: our stream matches theirs on the first 24 indices and
per-page lengths (first 10 exact); totals 12,947 vs 12,956 (9 runes, hashes
differ) — the §23 transcription-lineage delta. Comparable, not byte-identical.

Ledger diff (results/dukotah_ledger_diff_2026-08-23.md):
- Independent confirmation: B-21 PRNG = §13; R12-C1 k-history = §12; OTP-class =
  §13 wall; R12-D2 miscount = §28/§30.
- Importable negatives they ran, we hadn't: B-05 (pp49-51 as PRF/RC4 seed →
  keystream, NEG — the derived-pad reading of our N2); R12-A1 (CicadaOS binaries
  as pad, NEG).
- Our rigor exceeds theirs: B-16 — they eliminated their OWN keytext nulls as
  unsound (beam validated on wrong mechanism); ours use the beam with a passing
  planted-skip control (N6), so our book-key negatives stand.
- Their B-04 (derived short-seed dictionary, in-flight) = our N6 (ran a slice,
  negative).
- Neither ran: C-02 (our N9), D-04 (our N12), B-08/B-02 (extend N6), D-03
  (Z340 homophonic), and F-01 (LP2-as-pad inversion — a NEW angle, added to
  backlog).

Soft-rejection reconciliation (the substantive result): their model is a SOFT
anti-repeat, p_keep≈0.18; our §11 is UNIFORM resolution. Orthogonal — §11 fixes
HOW a rejected doublet resolves, soft-rejection fixes WHETHER it is rejected.
Fitted on our stream: p_keep = 86/(12934/29) = 0.193 ≈ their 0.18. enc_soft at
0.19 reproduces flat IoC + 0.66% doublet. Reframes the 86 doublets as the
filter's acceptance LEAK (signal), the mechanism behind §23. Added enc_soft +
fit_p_keep to no_repeat_model.py. validate_solved 9/9.
`results/norepeat_soft_2026-08-23.txt`.

### 2026-08-23 (cont.) — N9: structural-position uniformity (§45)

`attack_wordpos.py`. Group ciphertext runes by structural position, test each
for non-uniformity. Controls pass: a planted word-reset key lights up
word-initials (IoC 1.66, z 105); a continuous key stays flat (z 2.2).

PRIMARY: CLEAN NEGATIVE, well-powered. word-initial (n=2898), every within-word
position, word-final, page-initial all uniform (|z|<1.4). No word/page-
synchronised key (ACA Interrupted-Key) and no word/page acrostic. Extends §4 to
the conditional case.

ANOMALY (not overclaimed): line-initial is non-uniform — IoC 1.092, z 7.19,
survives Bonferroni, localised to position 1 (7.19→1.90→0.18). rtkd segmentation
validated (solved line-inits show English, z 3.68). BUT it fails project
scrutiny as a break: split-half 2.25/5.53 (homogeneous would be ~5.1 each),
per-page underpowered (~11 lines/page, mean z 0.04), weak corr with solved
line-init (0.36). Source unresolved (cipher signal vs line-wrapping/pooling
artifact). Logged as anomaly, NOT a lead; carried to backlog N19 (needs an
independent line segmentation). No core change; validate_solved 9/9.
`results/wordpos_2026-08-23.txt`.

### 2026-08-23 (cont.) — N19: line-initial anomaly resolved as artifact (§46)

`analyze_line_init.py`. Tested the §45 anomaly against an INDEPENDENT
segmentation: Dukotah's read4.json, a vision (from-image) transcription with
per-glyph page/band/x/class. chi2 is relabeling-invariant, so vision classes are
tested directly; vision noise only pushes toward uniform.

RESOLVED as artifact. Vision interior flat (z +2.83); both edges skewed
(line-init +38, line-final +36 vs uniform; +20 each vs its own marginal),
dominated by the default class cls 0 (89 vs 31) — edge-misclassification. rtkd is
asymmetric (init 7.19, final −0.01); vision is symmetric (both edges). The two
segmentations disagree, each explained by its own edge artifact. With §45's weak
split-half, the line-initial skew is a segmentation/transcription artifact, not a
cipher signal — §4 uniformity stands. read4.json staged in download/ (gitignored,
1.7MB). validate_solved 9/9. `results/line_init_n19_2026-08-23.txt`.

### 2026-08-23 (cont.) — N18: LP2-as-pad inversion (§47, F-01)

`attack_padinvert.py`. Inverts the frame: U as KEY material, not ciphertext.
P = C − U (position-locked) for candidate texts C, best-window English scan.

Framed by a guarantee: U is uniform (§4), so U − C is uniform for any C
INDEPENDENT of U; §6/§9 showed U independent of the 5 book texts, so those arms
are a formality. A folded pad would force U palindromic (it is not). Novel arms:
self-folds (U vs reverse/atbash(U)) and U vs solved plaintext.

NEGATIVE, control-validated. Planted English window recovered (floor −3.84);
ceiling −4.78; all real arms at/below chance (reverse −5.04, atbash −5.24,
atbash(rev) −5.08, solved-plaintext −4.81, kjv/runepoem sanity −5.08/−5.20).
Best real −4.81, 0.97 below the floor, 0.94-nat margin. The inversion is closed.
No core change; validate_solved 9/9. `results/padinvert_2026-08-23.txt`.

### 2026-08-23 (cont.) — N12: non-additive affine two-variable cipher (§48)

`attack_twovar.py`. Generalises c=(p+k) to the affine c=a*p+k, a in 1..28 (the
clean invertible non-additive family on a 29-prime alphabet; pure multiplicative
fails on 0, XOR undefined on 29). a=1 is additive (known); a=2..28 is a
multiplicative relabel the additive attacks missed. Affine inverse folded into
the key-skip beam.

NEGATIVE, well-powered. Control recovers planted affine+skip incl. the multiplier
a (floor −3.68, 4/4 at 91–100%); ceiling −4.31; best real −4.46 (a=18,
FIRFUMFERENFE), 0.79 below the floor, 0.63-nat margin. Prime/totient + DIVINITY/
FIRFUMFERENFE keystreams, all a, both signs. Generalising the cipher function
fails like generalising the key did. No core change; validate_solved 9/9.
`results/twovar_2026-08-23.txt`.

### 2026-08-23 (cont.) — N11: long exact repeats vs a Smirnov null (§49)

`attack_repeats.py`. Mine every exact ciphertext repeat, calibrate against a
SMIRNOV null (uniform, no adjacent repeats — the right null; iid would
over-count). Statistic: distinct k-grams occurring ≥2 times, real vs 300 nulls.

NEGATIVE — coincidental. No length beats the null: k=5 6 vs mean 4.72 (p=0.34);
the one 6-gram (DJUBEI at 6546/12941 — the community's eyeballed repeat) mildly
elevated z=2.71 but p=0.11; k≥7 empty. Gaps share no factor (6395=5·1279, 6553
prime, 1031 prime, 4992=2^7·3·13) → no Kasiski period, gap-as-key-period vacuous.
Mines all repeats vs the ~5 eyeballed, confirms §4 from a new angle. No core
change; validate_solved 9/9. `results/repeats_2026-08-23.txt`.

### 2026-08-23 (cont.) — N16: doublet-suppressing keystreams (§50)

`attack_oeis.py`. Two parts. REFUTED in principle: a no-output-rule
doublet-suppressing keystream would leave English difference structure in Δc; a
constant-Δk key on English gives nonzero-Δc chi2 295.6 / doublet 3.58% vs the
real 41.4 (df27, ~uniform) / 0.66%. Uniform Δc + 0.66% notch ⟹ output rule (§4).

NEGATIVE in practice: 16 sequences (Fibonacci, Lucas, tribonacci, Pell,
triangular, squares, pentagonal, pow2/3, Catalan, factorial, partition, arith
d=1,2,3,7) through the key-skip beam. Control 4/4 (floor −3.80), ceiling −4.47,
best real −4.44 (triangular) — 0.64 below the floor. OEIS/arithmetic keystreams
don't key the runes. No core change; validate_solved 9/9.
`results/oeis_2026-08-23.txt`.

### 2026-08-23 (cont.) — N15: unused-hint numerics as keystreams (§51)

`attack_hintseeds.py`. The onion cookies 167/761 (256-bit hex) and the 128-digit
2012 P.S. number, as keystream material: digits/bytes mod 29 (key-skip beam,
offset scan), SHA-256-CTR seeds (N6 construction), and leading-digit autokey
primers. Distinct from §26 (small numbers 167/761) and N6 (passphrases).

NEGATIVE, well-powered. Control 4/4 at 95–98% (floor −3.95); ceiling −4.46; best
keystream arm −4.32 (ps.bytes), autokey arm −4.70; best real 0.37 below the floor.
Pre-LP2 hint numerics don't key the runes — confirms §26 for the exact values.
No core change; validate_solved 9/9. `results/hintseeds_2026-08-23.txt`.

### 2026-08-24 — N13: steganography provenance gate (§52)

`attack_steg.py` on the 75 page scans (data/pages, gitignored; re-fetched — 9
outguess-fingerprint + 66 re-saved already on disk). outguess binary + DCT
library absent, so the local, decisive question: are our scans valid steg
targets?

PROVENANCE GATE — no. JFIF density is the outguess fingerprint (unit 0, 1×1). 9/75
keep it — exactly the intro pages 00-03/08/10-13 that carried the known 2014
clues; 66/75 are 400-DPI re-saves. ALL runic pages are re-saves → steg-dead.
Matches and explains the external negative. SHA-256 manifest archived.

APPENDED-DATA SCAN — one artifact. Verified post-EOI (prefix must decode to a
full image). Only 05.jpg: 72,700 bytes after a complete page, but no file header,
entropy 6.90, ends mid-SOI, on a 400-DPI re-save → corrupt/concatenated mirror
file, not a payload. Flagged for independent-copy check (N20).

Steg front closed for our material. No core change; validate_solved 9/9.
`results/steg_2026-08-24.txt`, `results/steg_hashes_2026-08-24.txt`.
