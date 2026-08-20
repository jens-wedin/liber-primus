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
