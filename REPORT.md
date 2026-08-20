# Liber Primus — analysis report

*Working from the transcription in scream314/cicada3301. 25 parsed segments,
15,750 runes total: 2,794 in solved pages, **12,956 unsolved** across 14
segments.*

## 1. The toolkit is validated against every solved page (9/9)

Plain-substitution pages (05, 10–13, 16, 57) transliterate directly. The
keyed pages were verified by forward-encrypting the known plaintext with the
documented key and comparing rune-for-rune against the actual ciphertext:

| Page(s) | Cipher | Match |
| --- | --- | --- |
| 03 | Vigenère, key DIVINITY, literal-ᚠ rule | 251/251 runes exact |
| 06–09 | Reversed gematria (atbash), then +3 | clean plaintext ("A KOAN…") |
| 14–15 | Vigenère, key FIRFUMFERENFE, literal-ᚠ | 319/319 runes exact |
| 56 | Keystream φ(pᵢ) over consecutive primes, literal-ᚠ | 85/85 runes exact |

Small side-findings from getting to 100%: the page-14 word usually
transcribed "LESSION" only encrypts correctly as **LESSON**; the md's rune
block for page 04 is internally inconsistent (its own author marks it
unverified) and was excluded from strict checks; and the md's plaintext for
page 03 covers only the first 251 of that section's 394 runes.

## 2. What the unsolved sections look like statistically

Reference: English written in Gematria Primus runes (from the solved pages'
plaintext) has a normalized index of coincidence (IoC) of **1.735** and a
doublet rate of 2.65%.

The combined unsolved stream (12,947 runes):

- **IoC = 1.000** — exactly what a uniformly random stream gives. Every
  fixed single-substitution (any alphabet permutation, not just shifts) is
  ruled out, since substitution preserves IoC.
- **No periodicity**: best periodic IoC over periods 1–40 is 1.005, i.e.
  noise. Repeating-key Vigenère up to period 40 is ruled out. (Small
  segments show inflated "best periods" — e.g. 2.167 at period 29 on a
  91-rune segment — but that is small-sample noise, not signal.)
- **Doublet anomaly, ~17σ**: adjacent identical runes occur at **0.66%**
  where a flat random stream predicts 3.45% (1/29). This is the strongest
  known structural signal in the unsolved text: a true one-time pad would
  *not* do this. Whatever generates the keystream couples neighboring
  positions (or the scheme forbids/avoids repeats).

Per-segment IoC ranges 0.93–1.06 with no outliers beyond what the segment
sizes explain.

## 3. Attacks run, all negative

- **All 87 fixed-mapping variants** per segment (29 shifts × {plain, atbash
  before, atbash after}) — nothing scores above noise on an English model
  built from the solved pages.
- **Prime and totient keystreams** (the page-56 scheme and its sibling),
  both directions, with and without the literal-ᚠ rule — negative. Cicada
  did not reuse the φ(prime) trick on any unsolved segment.
- **Autokey** (plaintext- and ciphertext-fed), both signs, all primers of
  length 1–2 everywhere and length 3 on small segments — negative. Note:
  plaintext-autokey always "improves" chi² spuriously because the decrypt
  feedback loop skews the output distribution regardless of content; word
  scores stay at zero, which is the honest verdict.
- **Crib-dragging** (`crib_drag.py`): 32 Cicada-vocabulary cribs dragged
  word-aligned over every unsolved segment, exploiting the preserved word
  boundaries and the literal-ᚠ rule as filters (422 legal placements). The
  implied keystream at each placement was tested for constant/AP/short
  period/prime-family structure and for English-ness (running-key
  hypothesis). Zero structural hits; best "English" keystream is
  indistinguishable from the best of 422 random draws. The tool self-tests
  by recovering the DIVINITY rotation on page 03 and the φ(prime) stream on
  page 56 from cribs alone, so the negative is genuine. Details in
  [LOG.md](LOG.md).

## 4. The doublet anomaly, characterized (main result)

Using the doublet deficiency as a *filter* on cipher families
(`doublet_sim.py`) turned out to be the productive move. Synthesizing
English-in-runes plaintext and encrypting it under each family shows that
**every independent-keystream cipher — OTP, Vigenère at any period, running
key, prime/totient streams — leaves the doublet rate at the random ~3.4%**.
None of them can produce the observed 0.66%. Only two constructions drop
below it: ciphertext-autokey (where doublets occur exactly when the
plaintext rune is F) and a deliberate no-repeat rejection scheme.

A decisive test rules the autokey family out too. If the cipher were a pure
cumulative sum (`c[i] = p[i] + c[i-1]`), first-differencing the ciphertext
would recover the plaintext. It doesn't — `d[i] = c[i] − c[i-1]` has IoC
**1.02** (not English's 1.7). But differencing *does* restore the doublet
rate to the normal **3.37%**, which proves the anomaly is a **pure lag-1
effect**.

Fully characterized: the first-difference histogram is uniform across all 28
non-zero values (χ² = 41 on 27 dof) with a single sharp notch at zero. **The
unsolved ciphertext is statistically a uniform random stream with exactly one
constraint — adjacent runes are almost never equal.** The 86 residual
doublets are spread evenly over all 29 runes, so the no-repeat property is
near-total and rune-independent.

This eliminates, rigorously: substitution (IoC would be 1.78), every
repeating/independent keystream (doublets would be 3.4%), and pure
autokey/cumulative-sum (differencing yields no English). What survives is a
construction that *forbids adjacent-equal ciphertext runes* — an
interrupter/skip rule or an explicit no-repeat step, plausibly keyed per
page. Note this is a **cipher** property, not a plaintext one: the solved
pages' plaintext doublet rate is ~2.3%, not 0.66%.

The suppression runs over the continuous rune stream, not per word: the leak
doublets sit equally within words (0.63%) and across • boundaries (0.80%), so
the separators are cosmetic and don't reset the rule.

Two output-stage mechanisms reproduce the whole fingerprint (`no_repeat_model.py`):
**re-roll** (a free pad that re-picks a key value whenever it would emit a
doublet — keystream stays position-locked) and **key-skip** (a fixed
keystream whose pointer advances an extra step to dodge a doublet). They are
statistically identical but the key-skip variant **desynchronises the
keystream by ~3%** — every avoided doublet consumes a hidden, invisible key
value. That desync is, mechanistically, why crib-dragging and every
periodicity/fixed-position test — this project's attacks included — return
noise. The 0.66% residual matches a small transcription-dittography leak
(a rune-uniform, boundary-independent doublet, as observed).

A beam search that resyncs a key-skip stream (`attack_keyskip.py`, self-tested
to 98% recovery on a genuine prime-key-skip text) was run against all 13
segments for both the prime and totient keystreams, both directions, all 29
offsets: **negative everywhere** (best word-score 0.08 vs ≥0.3 for English).
So the keystream, if key-skip, is not a prime-family sequence.

The remaining natural candidate — a **running key** drawn from an English
text — was tested key-text-free (`attack_runningkey.py`): a running key means
`c = p + k` with both p and k English, so a beam search can seek the
decomposition that makes both look like English at once. This came back
**inconclusive, by its own calibration**. On known inputs the decoder
separated a genuine running-key ciphertext (joint-bigram −4.26) from
uniform-random text (−4.39) by only 0.13, and a pure random stream decodes to
teasing fragments (`...YOU DYOUR AN...`) scoring as "English" as anything —
so it has no power to confirm or exclude running key at these segment lengths.
The real segments score right in that ambiguous band. This is a known limit
of running-key cryptanalysis: breaking it needs a specific candidate key text
to crib, higher-order (trigram+) models over full-length pages, or a
known-plaintext anchor — recorded so the teasing fragments are not mistaken
for a lead.

**Trigram upgrade (does it rescue the running-key test?).** Built a proper
n-gram language model (`language_model.py`) from the `wordfreq` 50k-word
English list — frequency-weighted rune n-grams with Stupid Backoff — since
the earlier bigram model came from far too little text. On *fixed* sequences
it is strong: English-vs-random separation rises from ~0.9 (old bigram) to
2.56 / 3.13 / 3.77 for orders 2 / 3 / 4. Re-running the attacks:
- **Key-skip** with the trigram model: prime/totient key-skip is now
  *robustly* rejected — self-test still recovers 96%, model refs sit far
  apart (English −3.4, random −6.2), yet all segments score −4.8 to −5.0
  (word-score ≤ 0.11).
- **Running-key** with the trigram model: **still underpowered** (genuine vs
  random separation −0.03; 12% recovery). Because the model is demonstrably
  strong on fixed sequences, this proves the running-key failure is
  *intrinsic* — when the decoder chooses the plaintext freely, it fits any
  input, including random. A running key here cannot be broken without a
  specific candidate key text to crib.

**Candidate-key cribbing (`attack_keycrib.py`) — running-key closed out.**
Since the doublet signature already rejects a *plain* running key, a running
key is only viable combined with the no-repeat enforcement. Two trigram-
powered tests plus a control:
- *Self-referential keys via key-skip*: feeding the beam decoder Cicada's own
  solved plaintext and every other segment's runes as the key stream —
  negative on all 13 (best −4.79 vs English −3.38).
- *Key-word crib*: sliding 500 common English words as candidate key
  fragments over every segment (6.4M placements), keeping English+dictionary
  plaintext fragments — 8,178 pass (0.127%). A **false-positive control** on a
  same-size random ciphertext passes 8,203 (0.127%): *identical to three
  decimals*, so the hits are pure chance, not signal.

So the running-key hypothesis is exhausted in every form testable without the
actual external key text. A break now needs either the specific key text
Cicada used, the re-roll variant treated as a seeded PRNG/hash pad (a
non-linguistic search for the seed/algorithm), or the page images
(interrupter positions the transcription may flatten).

## 5. Where to go next

Done so far: crib-dragging (§3, negative), doublet-signature filtering (§4,
the productive result). Genuinely open threads, in priority order:

1. **Model the no-repeat mechanism.** The signature points at a construction
   that forbids adjacent-equal ciphertext runes. Test explicit skip/
   interrupter models: a rule that, after normal keyed encryption, inserts a
   spacer rune or advances the key whenever a repeat would occur. Cicada
   already uses interrupters (the literal ᚠ), so an interrupter-driven
   no-repeat rule is in character. The 86 rune-uniform residual doublets are
   the fingerprint to reproduce.
2. **Work in difference space.** Because the meaningful lag-1 structure is in
   `c[i] − c[i-1]`, re-run crib-dragging and keystream tests on the
   first-difference stream rather than the raw runes.
3. **Per-page keying.** Several pages open with what look like short headers
   ("A KOAN"-style); testing key resets at line/page boundaries shrinks the
   effective unknown per unit.
4. **Cross-check the page images** (rune spacing, section marks) for
   information the transcription flattens — relevant if interrupters are
   positional.

Sober expectation: this cipher has resisted a decade of exactly this kind of
analysis; the realistic value here is a verified, scriptable foundation plus
a rigorously narrowed hypothesis space — not an imminent break.

## 6. Candidate running-key text: KJV ruled out (control-validated)

The one running-key avenue left open was a *specific* external key text. The
King James Bible is the canonical first guess, so `attack_running_text.py`
tests it directly against the key-skip hypothesis. Because a plain running
key is already excluded by the doublet signature (§4), the test decodes with
the key-skip beam (which tolerates the ~3% desync), not straight subtraction.

Method — two stages, since a 3.16M-rune key can't be beam-searched at every
offset:
1. a vectorised **trigram coarse scan** slides the whole KJV rune stream past
   several short windows of each segment and ranks key offsets by how English
   the implied plaintext looks;
2. the **key-skip beam** confirms the top offsets per window.

A planted **positive control** (encrypt English with KJV at a known offset via
key-skip, then recover it through the same pipeline) passes: it relocates the
key to within a rune or two and recovers ~100% of the window at trigram ≈
−3.4. So the pipeline provably finds a real KJV key.

Result on the actual ciphertext: **negative on all 13 segments.** The best
decode anywhere scores trigram −3.95 (gibberish, no words), well short of the
English/true-hit band at ≈ −3.4 (English reference −3.38; the control landed
−3.42). KJV is not the running key for any page — the whole book, every
offset, both directions.

Crowley's *Liber AL vel Legis* — the other common guess — could not be tested
here: no clean public-domain copy was reachable through the sandbox's proxy
(Project Gutenberg is blocked; it is not on npm/PyPI). The framework is ready
for it: drop the text in via `keytexts.py --add-textfile <path> crowley` and
run `attack_running_text.py --key crowley`. Same for any candidate text.

## 7. Short word key + key-skip (the solved-page scheme) — negative

The solved pages use short *word* keys (DIVINITY, FIRFUMFERENFE) with an
interrupter. Earlier work tested short repeating keys *without* the desync
(periodic-IoC, crib-dragging) and the desync *only* with prime/totient
streams — never the two together. `attack_vigenere_skip.py` closes that: it
key-skip beam-decodes every candidate word key directly (a straight-decode
coarse filter provably fails here — a short repeating key desynchronises
after the first skip, so the true key ranks ~4000/14000).

Key space: the Cicada vocabulary + the top ~1200 English words. Positive
control passes (plant CIRCUMFERENCE + key-skip → recovered rank #1, 83%,
trigram −3.90). Result on the real ciphertext: **negative** — best decode
trigram −4.23 (gibberish), against English −3.38 and a genuine key at −3.90.

Caveat on coverage: this rules out *common/thematic dictionary* word keys,
not all short keys. Notably the known key FIRFUMFERENFE is CIRCUMFERENCE with
C→F — a deliberate non-dictionary mangling — so a real key may be a similarly
mangled or coined word outside any word list. Widening `--nwords`, adding
letter-substitution variants of thematic words, or brute-forcing very short
keys are the natural extensions.
