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
  *(correction §31: only **18** were effectively tested — `--min-runes 8` drops 4,
  including the page openers A KOAN and AN END, and all 10 F-bearing cribs had
  every legal placement rejected by the literal-ᚠ filter, contributing zero
  scored placements)*
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
non-zero values (χ² = 41 on 27 dof — *marginally* so: p ≈ 0.04, max-bin
z = +2.6, so read "uniform" as "uniform to p≈0.04", not exactly flat) with a
single sharp notch at zero. **The
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

**Independent corroboration (2026-08-21).** The Uncovering-Cicada wiki's
*Frequency Analysis Unsolved Pages* reports n-gram counts on the same stream and
reaches the same verdict: bigrams 840 unique / 12952 total-repeated (random ≈ 841
/ ≈ 12955); quadgram repeats 255 (random ≈ 235, ~1σ) — statistically random. We
verified their "840 not 841" locally: the one absent bigram is **B–B** (ᛒᛒ), with
28/29 doublet types present; at the 0.66% doublet rate the expected B–B count is
~3, so drawing 0 is an ordinary ~5% Poisson fluctuation — inside the
doublet-suppression story, not a separately-banned bigram. See
`docs/cicada-3301-background.md` (Addendum 2026-08-21).

## 5. Where to go next

Done so far: crib-dragging (§3, negative), doublet-signature filtering (§4,
the productive result). Genuinely open threads, in priority order:

1. **Model the no-repeat mechanism.** *(Done — see §11.)* Modeled further: the
   collision resolution is uniform (deterministic bump/nudge ruled out) and the
   86 residual doublets carry no key-period leak. *(§23 revises the other half:
   an independent transcription reproduces all 86, so "transcription noise" is
   not supported — real doublets are favoured, not proven.)* The mechanism
   forbids adjacent-equal runes near-totally with a uniform re-pick — no
   arithmetic-interrupter shortcut to invert.
2. **Work in difference space.** *(Done — see §12.)* Tested the cumulative /
   chained-cipher family on `c[i] − c[i-1]`: keyless, repeating-key Vigenère
   (≤40), prime/totient — all negative, control-validated. The differences are
   as random as the raw stream. Untested (lower prior): a running-key text or
   word-key-with-skip on the difference stream.
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
mangled or coined word outside any word list. That specific gap is closed in
§8; very-short brute is addressed in §10.

## 8. Coined/mangled word keys — negative

The one gap §7 left open was Cicada's own habit of *mangling* a key word
(FIRFUMFERENFE = CIRCUMFERENCE with every C→F). A dictionary word list can
never reach such a key, so `mangle.py` expands the thematic vocabulary into
coined variants, using only transforms Cicada is attested to use on a solved
page: the **consonant collapse** C↔F/K/Q and S/Z, U/V (the C→F family that
produced FIRFUMFERENFE, plus the futhorc's own letter collapses); **atbash**
(reversed gematria, i→28−i, the page 06–09 cipher); **reversal** in rune
space; and a light **vowel rotation**. `attack_vigenere_skip.py --mangle`
feeds the 121 resulting variants through the same key-skip beam as any word.

Two controls gate the run, both passing:
- the generator reproduces the one ground-truth mangling
  (CIRCUMFERENCE→FIRFUMFERENFE via C→F);
- a planted **coined** key that is *not* in any word list
  (PRESERVATION~atbash) is recovered as the rank-#1 key at 100% of the
  window — so the expanded key space provably has power to catch a coined
  key, not just dictionary ones.

Result on the real ciphertext: **negative on all 13 segments.** Best decode
anywhere is trigram −4.13 (gibberish, no words). For calibration on this
head length the two positive controls — *correctly* keyed short decodes —
land at −3.90 (CIRCUMFERENCE) and −4.00 (the coined PRESERVATION~atbash);
English is −3.38. Every real segment scores *below even the known-correct-key
band*, so none behaves like a correctly-keyed page. Coined/mangled variants
of the thematic words (consonant-collapse, atbash, reversal, vowel-rotation)
are ruled out. `results/vigenere_skip_mangle_2026-08-20.txt`.

Coverage, stated plainly: only the ~29 *thematic* words were mangled (not the
common-word list), each by a *single* transform (no compositions like
atbash∘C→F), key length 4–16, both signs, key-skip max-skip 2, 30-rune heads.
Still open: multi-transform manglings, mangled common words.

## 9. More candidate running-key texts — all negative (control-validated)

After KJV (§6), a background briefing (`docs/cicada-3301-background.md`, also
in `download/`) pinned down the texts Cicada is *documented* to have used as
book-cipher keys or heavily referenced. The three strongest were tested as
running keys through the same key-skip pipeline (`attack_running_text.py`),
each with a planted positive control:

| Key text | Cicada link | runes | control | best real decode |
| --- | --- | --- | --- | --- |
| Crowley, *Liber AL vel Legis* | 2013 book-cipher key (strongest prior) | 22,045 | PASS (−3.51, 100%) | −3.97 |
| *The Mabinogion* (Guest tr.) | 2012 book-cipher key | 425,501 | PASS (−3.53, 91%) | −3.97 |
| Blake, *Marriage of Heaven and Hell* | referenced 2012 | 33,195 | PASS (−3.51, 100%) | −4.15 |

Every control passed — a planted key recovered ~100% at trigram ≈ −3.5 — so
each negative is meaningful. Every real decode sits at the ~−3.95 gibberish
noise floor, identical to KJV's best (§6), versus English −3.38 and the
true-hit band ≈ −3.5. None is a running key for any page: whole text, every
offset, both directions.

Two fixes enabled this. `keytexts.py` now ASCII-folds non-English source text
(Æ→AE, accents dropped via NFKD) so the Welsh *Mabinogion* transliterates
without crashing; and `attack_running_text.py`'s positive control now plants at
the middle of whatever key text it is given, so it works for short texts
(Blake, Liber AL — tens of thousands of runes), not only the 3.16M-rune KJV.

Source texts and provenance are vendored under `download/` (all public domain).
Not tested: Gibson's *Agrippa* (not public domain — living author); Emerson's
*Self-Reliance* and the Old English Rune Poem remain available if wanted (lower
prior — no documented use as a cipher key). Runs:
`results/running_{liberal,mabinogion,blake}_2026-08-20.txt`.

## 10. Very-short key brute force — ~~underpowered~~ **a clean negative** (corrected §30)

> **This section's original conclusion is WRONG and is retained for the record.**
> It rested on `probe_shortkey_id.py` reporting the true key at rank ~6/1500,
> which §30 shows was a ranking bug (distractors drawn with replacement from an
> 841-key space; sign-mirrors always tying; ties counted as beats). Corrected, a
> planted key ranks **#1** at L=2–6. The L=2 exhaustive brute is therefore a
> clean negative, and the L=3 brute this section declined to run is legitimate
> (§31).

The last short-key gap was a very short, meaningless run of runes as the key
(page 56's φ-stream is essentially that). Before brute-forcing it,
`probe_shortkey_id.py` measured whether such a key is even *identifiable* under
the key-skip: plant a random length-L key, encrypt English with key-skip, and
rank the true key against random length-L keys through the same beam.

The verdict (`results/shortkey_id_2026-08-20.txt`): at a 30-rune head the true
key ranks **~6/1500 at L=2** — it does not even come first, because the
key-skip's per-position freedom lets several wrong 2-rune keys decode to
English-looking text. L=3–4 reach rank ~1 only with a longer (60-rune) head,
and even then the residual ~1/4500 per-key false-positive rate, scaled over a
full 29³ = 24,389-key brute, implies several chance "hits". Since brute force is
only feasible at L=2–3 and clean identifiability arrives at L≥5 (29⁵ = 20.5M,
not brute-forceable), a very-short-key brute + key-skip cannot decisively test
short keys.

`attack_shortbrute.py` therefore runs the honest test for an underpowered
regime (as §4's key-crib does): it brutes the real segments AND matched-length
random ciphertexts, and asks whether any real segment beats the random chance
ceiling. Result at L=2 (`results/shortbrute_len2_2026-08-20.txt`): the best
real decode is trigram **−4.26**, *below* the random chance ceiling of **−4.23**
— real ciphertext does no better than random. **No signal.** This neither
confirms nor excludes a short key; it is underpowered, the same intrinsic limit
as the key-text-free running key (§4). A full L=3 brute was **not** run: it
would return chance decodes, not a clean negative.

## 11. The no-repeat mechanism, modeled further (§5.1)

§4 showed a re-roll pad and a key-skip both reproduce the fingerprint. Two
questions the fingerprint can still decide, each behind a control
(`model_norepeat_mechanisms.py`):

**How a collision is resolved — uniformly, not deterministically.** Synthesising
uniform no-repeat streams under different resolution rules and comparing their
first-difference histograms: a DETERMINISTIC rule (bump c by a fixed k on a
collision, or nudge to the nearest free value) forces every ~3.4% collision into
one difference bin, raising it to **1.9×** the uniform height — a clear spike at
that bin. The real stream's tallest difference bin is **1.11×** uniform (flat),
matching a uniform re-pick (1.07×) or a key-skip over a pseudo-random keystream
(1.19×). So the collision resolution lands UNIFORMLY on the other 28 values; a
deterministic bump or nearest-value nudge is ruled out. That fits a free re-roll
pad or a pseudo-random fixed keystream, and rules out a simple arithmetic
interrupter — there is no fixed offset to invert at the avoided positions.

**What the 86 residual doublets are — no key-period leak.** *(Update: §23 questions
the "transcription noise" half — a second transcription (rtkd/iddqd) reproduces all
86 doublets and disagrees with ours on only ~11 runes book-wide, so copy error is
either far too rare to explain them (→ real) or the two share lineage (→
inconclusive); "transcription noise" is no longer supported. The no-key-period
result below still stands.)*
If the residual doublets leaked from the mechanism at key events, their
positions would beat at that period, handing us the key period. They do not: the
doubled runes are rune-uniform (χ² 26 vs ~28), the gaps between doublets are
memoryless (CV 0.85), and a period scan (T = 2..64) finds no periodicity beyond
chance — the strongest period (T = 31) sits at permutation **p = 0.82** over
2000 shuffles. A control that plants independent (noise) doublets into synthetic
streams of the same segment lengths behaves identically (rune-uniform, CV 0.92,
best-period p = 0.80), proving the test reads true noise as noise. So the 86
doublets carry no exploitable structure — they are consistent with the ~0.66%
transcription dittography §4 proposed. Honest caveat: at only 86 events the
periodicity test has low power; a very weak periodic leak could still hide below
the noise floor the control establishes.

Net: the mechanism is a near-total no-repeat enforcement with **uniform**
collision resolution, and its residual leak is noise, not signal — slightly
sharper than, and fully consistent with, §4's re-roll / key-skip picture.
`results/norepeat_mechanisms_2026-08-20.txt`.

## 12. Difference-space: the cumulative-cipher family — negative (§5.2)

The fingerprint — c uniform, differences uniform with a notch at 0 — is exactly
what a CUMULATIVE / chained cipher produces:
`c[i] = (c[i-1] + m[i]) mod 29` with `m[i] != 0`. That makes the difference
`d[i] = c[i]-c[i-1] = m[i]` the meaningful stream; if `m = p + k`, then d is an
ordinary keystream cipher of the plaintext. §4 ruled out only the *keyless* case
(m = p). `difference_space.py` tests the *keyed* case, gated by controls that
plant a cumulative cipher of known English and recover it in difference space
(cumulative-Vigenère → periodic-IoC **1.84** at the planted period;
cumulative-prime → key-subtract trigram **−3.36**; both PASS).

Result on the real difference stream — negative on every path:
- **d-IoC 1.024** (random ~1.00, English 1.78): the differences are as random as
  the raw stream.
- **Best periodic-IoC over periods 1–40 is 1.03** (at 35) — flat, no
  cumulative-Vigenère period hiding in the differences.
- **d read as plaintext scores trigram −6.49** (random −6.62; English −3.38):
  the keyless cumulative case, re-confirmed dead with the trigram model (sharper
  than §4's IoC-only test).
- **Subtracting the prime and totient streams from d** (both signs, small start
  offsets) tops out at **−6.02** — random-level.

So the cumulative / chained-cipher family — keyless, repeating-key Vigenère
(period ≤ 40), and prime/totient keystreams — is ruled out; the difference
stream carries no more structure than the raw ciphertext. This fits §11: the
differences are uniform *because* the collision resolution is uniform, so a
cumulative cipher (which would leave a periodic or keystream-recoverable
signature in d) is excluded. `results/difference_space_2026-08-20.txt`.

Coverage: not tested in difference space are a running-key *text* on d
(intrinsically underpowered, as on the raw stream — §4) and word-keys-with-
key-skip on d; both lower prior. The periodic-IoC test does cover every
repeating key up to period 40.

## 13. Seeded-PRNG / hash-pad — negative for naive generators (§5, re-roll)

§11's uniform resolution fits a free re-roll pad; if that pad is a *seeded*
generator, the keystream is deterministic and the break is finding
(generator, seed) with `p = c − K` English. **Honest scope, stated first:** a
good PRNG with a non-trivial seed makes `c = p + K` a one-time pad, unbreakable
without the seed — which is exactly why `c` is uniform. So `attack_prng.py` only
targets the low-hanging fruit — naive/weak generators seeded with a SMALL or
THEMATIC value — and the RE-ROLL variant (re-roll keeps K position-locked, so
`c − K` aligns; a key-skip pad desyncs and would need the beam, not a seed
brute).

Battery: 7 generators — glibc LCG (raw and high-bits), Numerical-Recipes LCG,
Java LCG, xorshift32, Python's Mersenne Twister, and SHA-256-of-counter (a hash
pad) — over every integer seed 0..20,000 plus thematic seeds (3301, years, and
the Gematria sums of DIVINITY / CIRCUMFERENCE / …), both signs, tried both as a
GLOBAL seed (one for the whole stream) and PER-SEGMENT (a seed per page).

Controls: a planted glibc-LCG pad + re-roll is recovered exactly — seed and all,
trigram **−3.57** (≈ English −3.38); and a **chance-ceiling** brute on random
text (**−3.91**) bounds the multiple-comparison inflation.

Result: **negative.** The best real decode is trigram **−5.14** — *below* the
−3.91 chance ceiling, i.e. no better than the same brute on random text, and far
from English −3.38. No tested generator+seed reads English. This rules out these
naive/weak generators with small or thematic seeds; it does NOT — and cannot —
rule out a keyed CSPRNG. `results/prng_2026-08-20.txt`.

## 14. The page images: what the transcription flattens (§5 page-images lead)

Fetched the full book (75 scans → `data/pages/`, via `fetch_pages.sh`) and
compared the actual pages to `data/liber_primus.md`. The transcription omits
some visual features; the decisive test for each is whether a **solved** page
carrying the feature still decodes exactly with the feature ignored — if so, the
feature is cosmetic, not cipher.

- **Colour (red vs black).** Every page opens with a large red illuminated
  drop-cap and a short run of red runes, then turns black (systematic on
  unsolved pages 50, 57 and solved page 06). The transcription is monochrome —
  colour is fully lost. BUT solved page 06 (atbash+3, "A KOAN…") carries the red
  drop-cap + red opening runes and forward-encrypts to an **exact** match with
  every rune treated uniformly (validate_solved 9/9). So the red is rubrication
  of the opening capital/word — decorative, part of the normal cipher stream,
  not a separate key. **Cosmetic.**
- **Punctuation (`"` and `:`).** Besides the `•` word-dot (3308×) the pages carry
  a double-quote `"` (44×) and a colon `:` (8×); the toolkit drops all non-rune
  characters, collapsing them to word breaks. Decisive test: these marks appear
  in **solved** segments too — page 06 has 22 `"` + 8 `:` and still decodes
  exactly. They are plaintext punctuation (the koan's quoted speech), cosmetic
  for the cipher; dropping them is correct.
- **Page-local ornament.** Some pages carry non-futhorc marks the transcription
  omits entirely — cuneiform-like glyphs at the foot of page 50, decorative
  tree/border art on page 57, figure illustrations. These sit outside the rune
  stream; whether any is a distinct micro-cipher is untested, but they are not
  part of the 12,956-rune body.

Faithfully captured, by contrast: line breaks (indented lines), `•` word-dots,
and the `•••` section divider. And the stray digits/hex in the transcription are
the **title page's hash** (page 00), not embedded numbers — so there is no
numeric magic square in the runic book (bearing on the 2025 "page-16 magic
square" claim, whose square is uncited).

Net: **for cipher purposes the transcription is faithful** — the features it
flattens (colour, punctuation) are provably cosmetic, since solved pages that
contain them decode exactly without them. This validates the input the whole
toolkit rests on and closes the page-images lead as negative for the main
stream.

> **Correction (§15 supersedes the last claim here).** The sentence above
> originally added "the only genuine omission is page-local ornament, a
> curiosity" — that was drawn from just three pages and is WRONG. A systematic
> sweep of all 75 scans (§15) found the transcription also omits substantial
> **numeric and code content**: two magic squares, a numeric table, 100+
> alphanumeric codes, a hex block. Colour and punctuation are still cosmetic;
> but "the images add nothing" was premature.

## 15. The images DO carry more: numeric grids & code pages the transcription drops

Prompted by an external 2025 write-up claiming a Liber Primus "page-16 magic
square" (Echo446Ghq/Magic-Square-Solution — its square is arithmetically valid
but its mod-256→ASCII 'rl)lr' decode is numerology, see LOG), I catalogued all
75 scans for non-rune content (`results/page_glyph_catalogue_2026-08-20.txt`).
This overturns §14's over-broad "the images add nothing" — that was drawn from
three pages. **21 pages carry non-rune content absent from
`data/liber_primus.md`**, and some of it is substantial DATA, not decoration:

- **Two magic squares.** Page **16** carries a **5×5 magic square** (verified
  firsthand): magic constant **3301**, fully palindromic, prime centre 809 —
  *identical* to the 2025 write-up's square, so that square is a **genuine LP
  artifact** (only its decode was numerology). Page **32** carries a **4×4
  numeric grid** whose every cell is **3301 − a prime** (2,3,5,7,13,23,43,79,
  149,263,463,829,1481,2593), with 3299 = 3301−2 in **red** and a hand-drawn
  **Möbius/∞** — deeply on-theme ("the primes are sacred, the totient is
  sacred"). Page 16's runic instruction is solved (substitution); the square is
  a *separate* element the transcription omits.
- **A whole page of codes.** Page **67** is entirely a **13×8 grid of 104
  two-character alphanumeric codes** (each = digit 0–4 + a letter; verified
  firsthand), no runes at all. Pages **66** and **68** carry more of the same
  code. Page **73** carries a **hex block**. Page **05** carries a small
  palindromic **numeric table**.
- **Recurring marks** (probably structural/decorative): red pixel-block squares
  at line-ends (pages 50–56, 66, 70–74), a recurring **cuneiform-like glyph
  cluster** on pages 50–56 (identical each page → a section motif), red verse
  numerals (10, 11, 53–55), and small dot constellations (24, 40, 73).

**None of this is in the rune transcription** — the toolkit's 12,956-rune stream
never saw it. So the honest position: the *rune-cipher* campaign (§1–§13) is
exhausted and its input is faithful (colour/punctuation are cosmetic, §14), but
the **images open a genuinely new front** the toolkit was blind to — two magic
squares and 100+ codes with obvious cryptographic intent. Whether they are keys
for the unsolved runic pages, a separate cipher, or an index, is untested. This
re-opens the investigation on new material. `results/page_glyph_catalogue_2026-08-20.txt`.

## 16. Testing the new front — magic-square keys (negative) and the code pages

**Magic squares as keys — negative, control-validated.** `attack_magicsquare.py`
derives candidate keystreams from both squares under natural transforms —
row/column/unique/reversed reading orders with values mod 29, plus page 32's
prime structure (3301−value mod 29; the Gematria-Primus-prime rune indices; the
prime ordinals mod 29) — and key-skip beam-decodes every unsolved segment with
each, both signs, through the validated word-key pipeline (CIRCUMFERENCE control
passes: recovered #1, 83%, −3.90). Result: **negative**. Best decode −4.23
(gibberish), at the −4.57 chance ceiling, far from English −3.38. Neither square
is a repeating keystream for the unsolved pages under these derivations.
Untested: a bespoke-path key, a per-page sub-square, or the square as an
interrupter schedule. `results/magicsquare_2026-08-20.txt`.

**The code pages — a high-entropy, unsolved sub-cipher.** Pages 66, 67, 68 carry
two-character codes (a digit 0–4 + a base-62 character); page 67 is a full
104-code page (no runes), page 68 has 72 codes *above* four ordinary rune lines
(the codes are spatially separate from the runes, not interlinear). Transcribed
firsthand into `data/code_pages.txt`. Analysis (`analyze_codepage.py`): the codes
are **high-entropy** in both positions — the second character spreads flat over
49 of 62 symbols (max count 5), the letters show no English skew (even 'q'
appears 5×), and the base-62 values are mostly distinct with primes at chance
density. So the codes are **key-like data, not a simple substituted plaintext** —
which is why no natural numeric decode (base-62; digit×26+letter; second-char
alone), mapped into rune space, reads as English (all ≈ −6.6 = random) or works
as a key for the unsolved pages (−4.33, chance). A genuine unsolved sub-cipher:
plausibly itself-encrypted, a pad, or an index set. Caveat: this rests on a
hand-transcription of small mixed-case codes (error-prone); a verified
transcription of all three pages, plus community context, is the way forward.

Net: the magic squares and the code pages are real, newly-recovered content, but
neither yields to a first-pass attack. The §15 front is opened and characterised,
not cracked.

## 17. Page-16 square as an interrupter *schedule* (not an additive key) — negative

§16 closed the square as an additive keystream (`c = p + sq[j]`). This closes the
other reading CLAUDE.md flagged: the square **schedules the motion** of a base
keystream rather than supplying the added values. `attack_magicsquare_interrupter.py`
reads M16 in four orders (row, column, boustrophedon, spiral) as a repeating
schedule that drives three interrupter mechanisms over four base streams (primes,
totients, the square's own values, DIVINITY), both signs — a 384-mechanism grid,
each a deterministic invertible decrypt:

- **stride** — the key pointer advances by `1 + (s mod m)` each rune (a dense,
  square-dictated key-stride);
- **gated** — pointer advances +1 normally, +2 when the schedule value triggers
  (`s mod k == 0`, or `s` prime) — a sparse interrupter, the closest analogue to
  the observed ~3% key-skip;
- **reset** — pointer resets to 0 at each trigger (the classic *interrupted key*).

Result: **negative, control-validated.** The positive control (plant a known
interrupter encryption, recover it) passes at 100%; the chance ceiling on random
text is −5.64; the best real decode is −5.66 (*at* the ceiling, ~2.3 below
English −3.38), so no segment reads as English under any mechanism. The winners
cluster on high-stride / gated rules — i.e. schedules that heavily desync and
merely randomise — which is why they edge the ceiling by chance.

Honest scope: `attack_keyskip.py` already beam-searches *every* skip-≤2 schedule
over primes and totients (negative), so **stride/gated with small skips over those
streams was largely subsumed**; the genuinely new coverage here is the **reset**
interrupter (which the local beam cannot express), larger strides, and the
square/DIVINITY base streams — all negative. Both readings of "the square is a
key" (additive §16, interrupter §17) are now closed. `results/magicsquare_interrupter_2026-08-21.txt`.

## 18. The r/cicada GP-sum observation — reproduced; a plaintext-side ᚠ layer

A July-2025 r/cicada post ("56-57.jpg: GP sums of 3301 and 1033 found next to
each other") reports that the **solved** parable/instar plaintext is arranged so
adjacent rune-runs hit Cicada-themed Gematria-Primus totals. `verify_gp_sums.py`
reproduces both claims exactly from the toolkit's own gematria:

- `WE MUST SHED OUR OWN CIRCUMFERENCES` = 30 runes, GP **1031**; the errant
  literal-ᚠ (F, GP value 2) makes it **31 runes = 1033**;
- `…IS THE DUTY OF EVERY PILGRIM TO SEEK OUT THIS PAGE. PARABLE LIKE THE INSTAR
  TUNNELING TO THE SURFACE.` = **75 runes, GP 3303**; ignoring one *skipped* ᚠ
  (−2) gives **3301**, and the period splits the remaining **74 into 37 + 37**.
  All three sub-run lengths (31, 37, 37) are **emirp** primes; **1033 is a
  digit-anagram of 3301**. The literal-ᚠ is the ±2 knob used to land the totals —
  the same F-abuse seen in the 2016-17 hidden message.

Skeptic's control (Part 2): with free run boundaries and the optional ±2 F, a
*single* target is not rare — sliding all prime-length windows over the 1875-rune
solved plaintext, 1033 is hit 28× (arbitrary neighbours 24–31×) and 3301 111×
(neighbours 100–128×). So the arithmetic alone is weak; the weight is the
**co-occurrence** (two *adjacent* runs, all-emirp lengths, anagram totals, and
the otherwise-inexplicable ᚠ skips explained). *(Update: §25 tests that
co-occurrence and finds it common in random text — the parable scores below the
random mean — so even the conjunction is not statistically distinguished. Treat
§18 as numerology; the verified arithmetic stands but carries no evidential
weight.)*

Cryptanalytic bearing: this is a **plaintext-side authoring/steganographic layer**
via deliberate literal-ᚠ placement — **not a decryption lever**. GP sums are not
preserved through the mod-29 additive cipher, so they cannot be checked on
unsolved *ciphertext*; the property only exists once a page is in plaintext. Its
value is (a) a **plausibility filter** for any future candidate decrypt (a real
plaintext should partition into thematically-summing prime-length runs at its
ᚠ/period marks), and (b) motivation to **catalogue ᚠ positions/counts on the
unsolved pages** as possible structural markers. `results/gp_sums_verify_2026-08-21.txt`.

## 19. Literal- f-rune rule as a keystream interrupter on the unsolved pages — negative (P1.1)

*(Audit §28H: conclusion unchanged, but the coverage claim is softened — with the hold branch disabled 6 of 13 segments decode identically, so this partly re-measures the §4 key-skip negative; and the control exercises only one literal-ᚠ at the default head. The ᚠ inventory is itself disputed between transcriptions, §28G.)*

The solved pages use a key/stream + the **literal-f-rune rule** (a plaintext F is
written as an unencrypted f-rune and consumes no key value — the pointer holds).
`validate_solved.py` proves it, yet no *unsolved*-page attack had modelled it:
every keystream attack advanced the pointer once per rune. This is distinct from
the key-skip (§4): the key-skip beam advances the pointer by 1–3 (a forward
desync) and *cannot* express an advance-by-0 hold. `attack_literal_f.py` decodes
each unsolved head with prime/totient/word keystreams where every ciphertext
f-rune branches {hold: plaintext F, pointer stays; advance: p = c ∓ K}, in two
variants — PURE (the exact solved-page scheme) and +SKIP (literal-f plus the §4
key-skip).

Result: **negative, control-validated.** The positive control (plant English +
prime + literal-f, PURE and +SKIP) recovers 100% and every literal-F position;
chance ceiling −4.79, best real decode −4.86 (*below* the ceiling, English −3.38).
No segment reads as English; winners lean on the +skip freedom (mere desync). The
f-rune count is at chance to begin with (3.53% ≈ 1/29, §20), so a literal-f scheme
with an English F-rate would predict a mild excess that is not observed — weak
evidence against the rule here, and the decode settles it. `results/literal_f_2026-08-21.txt`.

## 20. f-rune position structural map — nothing survives into the ciphertext (P1.2)

*(Audit §28F: DOWNGRADED. The positive reference was underpowered and silently failed to fire, and the prime-gap row breaches the script's own band (Bonferroni p≈0.13). Read this as "no evidence of a fingerprint on an underpowered test", not a clean negative.)*

Does §18's deliberate literal-f placement leave a usable fingerprint on the
unsolved pages? `analyze_fpositions.py` maps the f-rune positions and tests
gap-length prime/emirp enrichment and word-edge clustering against a Monte-Carlo
uniform-placement null, with the solved plaintext (where literal-F is
identifiable) as the positive reference. The f-rune sits at **3.53%** (≈ 1/29,
uniform). All tests are consistent with random placement: emirp-gap z = −0.2,
f-at-word-edge z = −0.4, and the one borderline value — prime-length gaps — is
z = +2.7 raw but **+2.3 once the suppressed f-f doublet (gap = 1, a non-prime the
no-repeat rule removes) is corrected for**, i.e. within multiple-comparison noise
across the six statistics. The solved reference shows no bulk enrichment either
(only 31 literal-Fs), matching §18's finding that the effect is a curated
co-occurrence, not a population signal. Conclusion: the literal-f layer is a
**plaintext** property that does not survive encryption into the ciphertext — a
clean empirical bound, consistent with §18. `results/fpositions_2026-08-21.txt`.

## 21. Code pages verified + completed (P1.3) — still high-entropy, two structural hints

P1.3 asked for a verified, non-OCR transcription of the code pages and a re-test.
The scans are clean line-art at legible size, so pages 67 and 68 were re-read
code-by-code against `data/pages/{67,68}.jpg` and the existing hand-transcriptions
confirmed **exact** (case included: 0S/0s, 1O/1o, 1l/1I). Page 66 — a 10×8 block
of 80 codes below three rune lines and a red pixel-block — is now transcribed for
the first time. All 256 codes validate as digit(0-4)+base-62.

Re-running `analyze_codepage.py` on the full, verified 256-code set: the §16
verdict holds — no natural numeric decode (base-62; digit×26+letter; second-char
alone) reads as an English rune message (best −6.48 ≈ random −6.59) or keys the
unsolved pages (−4.33 vs −4.40 ceiling). High-entropy, key-like, unbroken.

Two structural notes for future work: (1) the three blocks total **256 = 2⁸**
codes (104+72+80) — a round total that also independently cross-checks the
page-66 row count; the set may be a 256-entry table / pad / S-box. (2) the leading
digit is **not** uniform over 0–4: 0–3 are common (~60 each) but **4 is rare**
(17/256 = 6.6%), so the first char behaves like a 4-ary symbol with an occasional
escape rather than a flat 5-ary one. Neither cracks the pages, but both sharpen
the "treat as a pad / index / self-enciphered stream" direction (BACKLOG P1.3
remainder). `results/codepage_2026-08-21.txt`.

## 22. Code pages: pad / index / self-cipher / table — all negative (P1.3 remainder)

*(Audit §28D: the pad control was vacuous and the self-cipher had no null; both fixed and re-run. Conclusions unchanged, margins corrected — the pad best sits at its length-matched ceiling, not below it. Byte encoding additionally ruled out.)*

`attack_codepages.py` takes the verified 256-code set past the natural numeric
decodes (§21) into the interpretations its structure invites, each
control-validated / chance-ceiling'd:

- **Table / permutation — ruled out.** The 256 codes are only **161 distinct** as
  2-char strings (95 repeats), and no value map is a bijection — so the set is a
  stream *with repetition*, not a 256-entry S-box / lookup table. The 256 = 2⁸
  total is therefore a message/pad length, not a table's size.
- **Pad** (position-locked `p = c − pad`, offset-aligned, no skip — distinct from
  §21's repeating-key test): control passes; best real −5.73 vs −6.19 ceiling
  (English −3.38) — gibberish, no signal.
- **Index** (each code selects a rune from solved plaintext / unsolved ciphertext
  / the 29-rune alphabet): best −4.84 selecting from the English solved plaintext,
  at its own −4.76 ceiling — i.e. just a bag of English letters, no coherence; the
  other streams below their ceilings.
- **Self-cipher** (digit as a per-position shift on the base-62 symbol, rune and
  letter paths): −6.2, gibberish.

So every natural pad / index / self-cipher / table reading is exhausted,
control-validated. What survives is only the structure (§21): 256 = 2⁸ codes and a
4-ary-plus-escape leading digit, on a repetition-bearing stream — consistent with
a **keyed pad or self-cipher**, unbreakable without the key (§13). The code pages
are now characterised as far as key-free analysis reaches.
`results/codepages_attacks_2026-08-21.txt`.

## 23. Transcription cross-check — the 86 doublets are stable across transcriptions; §11's noise reading questioned (P2.4)

§11 attributed the 86 residual unsolved-stream doublets to transcription noise (a
plausible ~0.66% hand-copy error rate). `compare_transcriptions.py` tests that
against rtkd/iddqd's master transcription
(`download/rtkd_liber_primus_transcription.txt`, github.com/rtkd/iddqd). Full-file
difflib alignment: the two are **near-identical — 15938 vs 15933 runes, similarity
0.9995, only ~11 differing runes (0.07% of the book)**. At our 86 unsolved
doublets, rtkd reproduces **all 86**.

What this does and does not show. The 0.07% inter-transcription disagreement rate
admits two readings:
- **If the two are independent**, that rate is ~10× below §4's 0.66% dittography
  figure — so hand-copy error is far too rare to explain the 0.66% doublet rate,
  and the doublets are **real ciphertext**.
- **If they share lineage** (likely, at 99.95% agreement two hand-transcriptions
  of ~16k runes almost certainly derive from a common source), the test only shows
  the *canonical* transcription stably contains all 86 — it cannot exclude a
  common-source error, so it is **inconclusive**.

Net: §11's "transcription-noise-consistent" reading is **not supported** either
way; "the doublets are real" is favoured but not proven, and §11's other result
(no key-period leak) is untouched. Correcting a mid-analysis error: an earlier
draft of this section reported "~185 runes rtkd has that ours drops" and a
0.994 ratio — that was an artifact of comparing `parse()`'s 15750 *segment* runes
against rtkd's full 15933; at the full-file level there is **no dropped content**
(diff −5 runes) and the ~188-rune gap is non-segment runes (solved-page
reproductions in prose) `parse()` doesn't pull into segments.

Bonus — code pages: rtkd transcribes the code pages too; both have exactly **256
tokens** (corroborating the page-66 count, §21) and differ only on ~6
case-ambiguous glyphs (my `3l` vs rtkd `3I` ×3, plus l/L, s/S calls) — the §21
read stands bar those genuinely ambiguous characters.
`results/transcription_compare_2026-08-21.txt`.

## 24. The squares as a standalone message — nothing above numerology (P2.6)

*(Audit §28E: the null was not the real battery. Under a corrected permutation null, page-16 p=72% (sound) but page-32 is p≈8% — MARGINAL, not the clean negative reported here.)*

§16/§17 closed the squares as keys/interrupters; this reads their VALUES directly.
`analyze_squares.py` maps page-16 (25 values) and page-32 (16 values) through
several reading paths (row/col/spiral/boustrophedon) into runes (mod 29), plus
page-32's prime structure (3301−value → GP-index / prime-ordinal), and an ASCII
(mod-256) reading. Every decode sits **at or below a numerology ceiling** (the
same battery on random value-grids): page-16 best −6.72 vs ceiling −4.60; page-32
best −4.71 vs ceiling −2.09 — random grids score *higher*, the tell that 16-25
symbols carry no n-gram power. The mod-256 ASCII reading reproduces the known
palindromic `rl)lr` numerology (page-glyph catalogue), nothing more. Conclusion:
the squares hold no hidden runic/ASCII message; their meaning is the established
3301/prime structure. At 16-25 symbols no such test could be decisive regardless,
so this closes the reading as "no evidence", not a strong positive-power negative.
`results/squares_message_2026-08-21.txt`.

## 25. The GP-sum plausibility filter does not discriminate — deflates §18 (P2.5)

*(Audit §28B: the original detector could not represent the signature at all (the 3301 run is 74 runes, not prime), so its numbers were meaningless. Re-implemented and re-run on the full solved plaintext: 31 real vs null 30.6, P=50.2% — the conclusion below survives on valid evidence.)*

Intended as a tie-breaker built on §18's signature (adjacent prime-length runs
summing to 3301 and 1033, ±2 F). `gp_filter.py` counts that conjunction and
controls it: the solved parable plaintext scores **7**, but random text of the
same length (1875 runes) averages **10.9** (95th pct 17), with P(random ≥ 7) =
88%. The real text scores *below* the random mean. So the adjacent-3301+1033
conjunction is common in random text and the parable is not distinguished — the
filter cannot discriminate and is unusable as more than the softest prior. This
further deflates §18: not only is a single GP hit unremarkable (§18's own
base-rate), the **co-occurrence** §18 leaned on is also within (indeed below) the
random range. §18's verified arithmetic stands, but its "suggestive of deliberate
authoring" reading is **not statistically supported** — it is best treated as
numerology. `results/gp_filter_2026-08-21.txt`.

## 26. Pre-LP2 "hints never used" as keys — negative (P3.7)

*(Audit §28A: the original verdict rule would have printed NO SIGNAL on a real break. Re-run against an empirical detection floor (−4.00); the real best −4.38 is 0.38 below it, so the negative now has demonstrated power — but 3 of 9 keys are NOT COVERED, and `missing_primes` is just the prime stream offset 20.)*

`attack_hints.py` runs the numeric sequences from Uncovering-Cicada's "Possible
hints never used" through the validated key-skip beam: the 2012 OutGuess whitespace
(0,2,3,5,7,11,13,…), the 2014 message.txt.asc whitespace (2,3,5,7,11,13,17,23,29,
31,37 — it skips 19), the emirp cookie ids 167/761 (as digits, mod 29, and as
**start offsets** into the prime/totient streams), and the "missing primes" 73…1223.
Control passes (CIRCUMFERENCE, 83%); chance ceiling −4.65; best real −4.38
(missing_primes), ~1 below English −3.38 → **NO SIGNAL**. A couple of keys edge the
noisy ceiling by tenths (multiple comparison over 14 keys × both signs) — chance.
The pre-LP2 hint sequences do not key the unsolved pages, as expected at their low
prior. `results/hints_2026-08-21.txt`.

## 27. The AN END deep-web hash (P3.8) — out of scope, documented

The solved "AN END" page (LP2 56 ≈ scream314 73; §23 cross-check) reads: "WITHIN
THE DEEP WEB THERE EXISTS A PAGE THAT HASHES TO
`36367763ab73783c7af284446c59466b4cd653239a311cb7116d4618dee09a8425893dc7500b464fdaf1672d7bef5e891c6e2274568926a49fb4f45132c2a8b4`",
and page 73's hex block is exactly that SHA-512 (confirmed §21). Finding the page
that hashes to it is a **Tor hidden-service OSINT hunt**, not runic cryptanalysis —
it is not actionable with this toolkit and is recorded for completeness only. No
experiment run.

## 28. Self-audit of §17–§27 — defects found and corrected

Two adversarial audits were run over the session's own code (one on the attack
scripts' controls, one on the statistical null models). They found real defects.
**No headline negative was overturned** — but several were resting on invalid
evidence and are now re-grounded. Everything below is fixed in code and re-run;
the archived `results/` files are the corrected outputs.

**A. A verdict rule that would have missed a real break (§26).** `attack_hints.py`
declared a break only if the score beat `English − 0.5` (−3.88). Planting the very
keys under test and recovering them at 97–100% accuracy scores as low as **−4.00**
— i.e. the script would have printed "NO SIGNAL" on a total break of 4 of its 9
keys. Fixed by calibrating the threshold empirically: each key is planted and
recovered, and the minimum recovered score is the **detection floor** (−4.00). The
real best is −4.38, **0.38 below the floor** → the negative now has demonstrated
power. Two further §26 corrections: 3 of 9 keys (`ws2012`, `ws2014`,
`cookies_mod29`) cannot be recovered even when planted, so they are reported as
**not covered** rather than negative (cf. §10); and `missing_primes` is
mathematically `prime_stream[20:]`, so its top score is the already-known prime
stream, not a new lead.

**B. A statistic that never implemented its own test (§25).** `gp_filter.py` gated
BOTH runs to prime lengths — but §18's 3301 run is **74 runes, not prime**, so the
detector could never see the signature: the old "real = 7" contained zero true
signatures and compared noise to noise. Fixed (3301 searched over a length window,
1033 at prime length) and re-run on a corrected reference: **31 real signatures vs
a shuffle-null mean of 30.6, P = 50.2%**. §25's conclusion — the §18 co-occurrence
is numerology — **survives, now on real evidence**.

**C. A reference stream missing a third of the solved text.** `english_plaintext()`
silently omits every keyed page, including page 73 "AN END" — the page carrying
§18's own run — using 1875 of 2794 solved runes. New `solved_text.py`
(`full_plaintext()`, 2530 runes, keyed pages decrypted from the plaintexts
`validate_solved.py` proves) fixes this and is now the reference for §20 and §25.
The plaintext constants are de-duplicated into that module; `validate_solved`
still reports 9/9.

**D. Vacuous / missing controls (§22).** The pad control tested `c − pad == p`, an
algebraic identity that passes even with the pad stubbed to zeros; the self-cipher
test had **no null at all**. Both fixed: the pad control now requires the search to
recover a planted pad (it does — 100%, detection floor −3.57, vs a real best of
−5.73), and both self-cipher paths get composition-matched shuffle nulls. Also
corrected: the pad ceiling was computed at a fixed 256 runes while short segments
were scored on 91–121 symbols (shorter sequences score higher), so the reported
margin was wrong — length-matched, the best real sits **+0.07 from its own
ceiling**, not 0.46 below it. And the script's structural line asserted "a
256-entry pad/S-box is the natural read" while printing 161 distinct codes; that
is now stated correctly as a **stream with repetition, not a table**, plus a new
falsified hypothesis: the codes are **not** a byte encoding (digit 4 spans b62
0–41 and 12 values exceed 255).

**E. A null that was not the real battery (§24).** `analyze_squares.py` drew
random-valued grids, for which `3301 − v` is rarely prime, so the prime-based
readings collapsed to 3–5 symbols — and the per-symbol score's SD explodes at
short length, so the "ceiling" was set by the shortest random reading. It also
compared ~2400 null samples against 12 real ones. Replaced with a **permutation
null** (shuffle the square's own cells, best-of-battery vs best-of-battery, 2000
draws). Page-16: p = 72% — no message, sound. Page-32: **p = 8.2% — marginal, not
the clean negative first reported**. Still not significant, and 2.5 below English
at 14 symbols, so "no message" stands, but as a weak result.

**F. An overstated negative (§20).** `analyze_fpositions.py` printed a clean
negative while its own prime-gap row (z = +2.31) breached the |z| < 2 band it
declares, and its "positive reference" **silently failed**: with ~41 literal-ᚠ the
null SD is ~8pp, so the reference could not reach z = 3 even if the effect were
real. The read-out now states the power limitation and the multiplicity correction
(6 statistics; Bonferroni p ≈ 0.13 for the prime-gap row) explicitly. §20 is
downgraded from "clean negative" to **"no evidence of a fingerprint, on an
underpowered test"**. An emirp obs/null filter mismatch was also fixed (z −0.21 →
−0.37).

**G. A not-like-for-like rate, and a new finding (§23).** The inter-transcription
error rate was computed over the whole book but compared to a doublet rate over the
unsolved stream; like-for-like inside the analysed corpus it is **6/15750 =
0.038% (~17× below 0.66%)**, not the ~10× reported. Direction unchanged. New
finding: the disagreements are **systematically ᚠ** — 4 of our 10 extra runes are
ᚠ, i.e. the two sources disagree precisely about the rune the literal-ᚠ thesis
depends on. The ᚠ inventory is itself disputed, which is a standing caveat on any
ᚠ-counting result (§19, §20).

**H. Under-powered ceilings throughout.** All the session's attack scripts used a
max over 6 random draws as the ceiling while the real result is a max over 13
segments, biasing ceilings low. Matched, the §26 ceiling moves −4.65 → −4.49, and
in §17 the length-matched ceiling puts the best real **0.37 below** it rather than
level with it (a *stronger* negative than reported). §19's conclusion is unchanged
but its coverage claim is softened: with the ᚠ-hold branch disabled, 6 of 13
segments decode byte-identically, so that run substantially re-measures the §4
key-skip negative rather than adding fully independent coverage, and its control
exercises only one literal-ᚠ at the default `--head 80`.

Verified sound and unchanged: the 9/9 solved-page reproduction; the difflib
alignment and the 86/86 doublet reproduction (independently re-derived); the
`verify_gp_sums` headline sums (1033 at 31 runes, 3301 at 74) and its base-rate
control; the interrupter grid's identifiability (**48/48 planted mechanisms
recovered at 100%**, so §17's negative is genuinely supported); the ᚠ-position
Monte-Carlo sampler; and every documented number matching its archived run.

## 29. Re-doing the work on calibrated controls (R1–R3, R5) — every negative holds

§28 found that several negatives rested on invalid evidence. This section is the
re-do. **No conclusion changed; all of them are now supported by demonstrated
power** — each attack proves it *could* have seen a break before claiming it
didn't.

**R5 — `controls.py` (the systemic fix).** One self-tested module now provides
`detection_floor()` (plant each hypothesis, recover it through the identical
pipeline, take the minimum recovered score as the threshold a real break would
产 produce), `matched_ceiling()` (a null with the same LENGTH and the same number of
TRIALS as the real run), `shuffled()` / `shuffle_ceiling()` (composition-matched
nulls) and `verdict()` (so the wording cannot drift from the numbers). It also
encodes the distinction §28 exposed: **identifiability** (does the true
hypothesis rank first? — this defines the floor) is not **decode quality**
(accuracy, reported separately). Conflating them was itself a bug in the first
§26 fix, which under-reported coverage as 6/9 when it was 9/9.

**R1 — the three scripts whose verdict rule could have hidden a break.** All
re-run through the floor; all negatives hold, and each now states its coverage:

| § | script | floor | best real | margin | coverage |
| --- | --- | --- | --- | --- | --- |
| 16 | `attack_magicsquare.py` | −3.95 | −4.23 | 0.27 below | 8/9 (`sq16_rev` NOT COVERED) |
| 21 | `analyze_codepage.py` | −4.00 | −4.33 | 0.33 below | 4/4 |
| 19 | `attack_literal_f.py` | −3.65 | −4.81 | 1.17 below | 33/34 |
| 26 | `attack_hints.py` | −4.00 | −4.38 | 0.38 below | 9/9 |

§16 is the one proven broken in §28 — its own planted control scored −3.90
against its own −3.88 threshold. Recalibrated, its negative stands. §19's default
head is raised 80 → 120 so the control exercises several literal-ᚠ rather than
one. Two coverage gaps are now visible that the old scripts never reported:
`sq16_rev` (§16) and one §19 config are non-identifiable — for those the runs
yield no evidence either way.

**R2 — length-matched ceilings.** `attack_magicsquare_interrupter.py` (§17) now
draws its ceiling at each segment's own length. Every segment sits **below** its
own ceiling (best margin −0.19), so the negative is *stronger* than the published
fixed-length comparison implied.

**R3 — the attack that had no control at all.** `attack_autokey.py` (§3) ranked
by chi² with only a random baseline, so its negative was unvalidated under the
project's own ground rule. A planted control now recovers both ciphertext- and
plaintext-autokey (99% / 100%, correct method and sign) → **PASS**, while the real
segments score word-score 0.00. The autokey negative is validated for the first
time. The control also documents a genuine property: a *ciphertext*-autokey
primer supplies only the first L key values, so it is essentially unidentifiable
— the criterion is method + sign + recovery, not an exact primer match.

Net: the hypothesis space is unchanged, but the evidence under it is now sound,
and the coverage gaps are stated rather than hidden. R4 (auditing the
never-audited §3–§13 scripts, including an independent recomputation of the
central finding) is outstanding.

## 30. Audit of the never-audited statistical core (R4a) — central finding confirmed, §10 refuted

The §28/§29 work audited only this session's code. R4 turned the same adversarial
treatment on the scripts behind the project's oldest and most load-bearing claims
(§2, §4, §10–§13). Result: **the central finding is independently confirmed, and
one long-standing conclusion (§10) is refuted as a software bug.**

**The central finding (§4) survives an independent recomputation.** The auditor
rebuilt the parser and rune table from scratch — no project helpers — and got:
doublet rate **0.6649%** (86 within-segment pairs of 12,934) against a 3.448%
null, **z = −17.35** (p ≈ 1e-66), **IoC 0.9998**, unigram χ² 25.9 on df 28
(marginals uniform), and equality at lags 2–8 all null — confirming the effect is
purely lag-1. The σ is computed correctly: doublet indicators are *pairwise*
independent under the iid-uniform null, so Var = np(1−p) is exact. Concatenating
segments (which counts 12 cross-boundary pairs) is immaterial: 0 spurious
doublets, 0.6643% vs 0.6649%. One overstatement corrected: "first differences are
otherwise uniform" is only marginal — χ² 41.2 on df 27, **p ≈ 0.04**, max-bin
z = +2.6 — now written as "uniform to p≈0.04".

**§10 is REFUTED — short keys ARE identifiable.** `probe_shortkey_id.py` reported
the true key ranking ~6/1500 at L=2 and concluded that key-skip freedom makes
short keys non-identifiable, which is why REPORT §10 and CLAUDE.md called the
short-key brute "underpowered, not a clean negative" and why an L=3 brute was
never run. That rank was a **ranking bug**, three compounding errors: distractor
keys were redrawn *with replacement* from a space of only 841 (so the true key was
redrawn ~1.8× per trial and counted as beating itself); `score_key` maximises over
both signs, so every key's sign-mirror `(−k mod 29)` decodes to the identical
plaintext and always tied; and `>=` counted ties as beats. Corrected (distinct
distractors, sign-mirror excluded, strict comparison), the true key ranks:

| L | old (buggy) | corrected |
| --- | --- | --- |
| 2 | ~6/1500 | **1.0** |
| 3 | ~2 | 1.3 |
| 4, 5, 6 | ~2 | **1.0** |

At head 60 every length ranks 1.0. Consequences: the existing L=2 exhaustive brute
is a **clean negative**, not an underpowered non-result; and the L=3 brute became
worth running. **But see §33: this probe samples only 400 distractors, so it
measures identifiability against 400 competitors, not against a full brute's
24,389. Against the whole L=3 key space only 1 of 10 planted keys survives, so
"short keys are identifiable" holds at L=2 and FAILS at L=3.**

**A contaminated null (critical, §13).** `attack_prng.py` drew its chance ceiling
from `LCG(700+d)` — the *same* Numerical Recipes LCG it brute-forces (`lcg_nr`),
with seeds inside `range(20000)`. The brute recovered the exact stream that
generated the null, decoded it to all-ᚠ, and scored −3.91 against a true ceiling
of ≈ −5.25: inflated by 1.36 nats, under which **~30% of genuine planted breaks
would have been reported as negative** (24 of 80 planted breaks fall below the
rule's threshold). The root cause was systemic and had reached `controls.py`, this
session's own fix, whose `random_runes()` used the same LCG. Nulls now come from a
domain-separated SHA-256 stream no searched generator can produce, and the module
self-tests that LCG seeds 0–20k cannot reproduce it. §13's conclusion survives —
against the corrected ceiling the real best is still below it — but its published
evidence did not.

**Two weakened (not overturned) claims.**
- §11's "no key-period leak" was tested only against a *position-locked* leak. The
  permutation test's control checks specificity, never sensitivity; planting a
  period-31 leak with the ~3% phase drift that key-skip itself produces yields
  p ≈ 0.07–0.18, i.e. it would be reported as "consistent with noise". So §11
  excludes a rigid periodic leak, not a drifting one.
- `doublet_sim.py`'s fit band was ~15× the observed rate's standard error,
  accepting anything under 1.66% and labelling ciphertext-autokey (1.65%, ~14 SE
  from 0.66%) a "MATCH" — contradicting §4's own ruling-out of autokey. Tightened
  to 3 SE; the only matching family is now no-repeat (rejection), as §4 concludes.
- `difference_space.py` (§12) has no matched ceiling and its controls never
  enable the no-repeat notch that defines the real data; enabling it shrinks the
  prime control's margin from 0.32 to 0.08 nats. The §12 negative survives (best
  real −6.02 vs English −3.38) but on a narrower margin than published.

Verified sound: `parse_lp`/`gematria` (independent reparse matches exactly),
`validate_solved` 9/9, `language_model` (score_sequence is a per-symbol mean over
L−1 terms; an independent reimplementation matches to 1e-15), `english_plaintext`
contains no ciphertext leakage, and the §11 permutation statistic itself is
correctly constructed.

## 31. Audit of the never-audited attack scripts (R4b) — three negatives weakened, two coverage claims wrong

The companion to §30, over the scripts behind §3 and §5–§9. **No negative is
overturned**, but three rest on far less than the write-ups claimed, and two
stated coverage figures are simply wrong.

**§5 (self-referential running keys) — coverage ≈0.1%, and no control at all.**
`attack_keycrib.py` Part A has no positive control (violating the project's first
ground rule) and hardwires every candidate key stream to start at rune 0
(`Kx = (K + K)[...]`). Planting the hypothesis at other offsets shows what that
costs: offset 0 → recovered (95% accuracy, −3.72); offset **50 → missed** (4%);
offset **300 → missed** (3%). The run therefore covers 26 of ~26,000 natural
hypotheses (13 streams × 2 signs × ~1000 offsets). The offset-0 conclusion is
sound — a computed detection floor of −3.76 against a matched ceiling of −4.86
puts the archived best (−4.79) 1.03 below the floor — but §5's claim that the
running-key hypothesis is "exhausted in every form testable without the actual
key text" is **not supported**.

**§7/§8 (word keys) — a negative with essentially zero operating margin.**
Planting 13 real keys × 5 plaintexts through the exact `main()` settings gives a
**detection floor of −4.00**; a matched 13-trial ceiling at the same length is
**−4.01**. The score a genuine break produces and the level pure noise reaches are
the same number. The negatives survive (0 of 60 planted breaks scored as low as
the real −4.23/−4.13), but with no headroom. Worse for coverage: on the script's
own control plaintext **5 of 13 planted keys do not rank first** (INSTAR→INSIDE,
TRUTH→VOTE, SACRED→SOMETHING, GOVERNMENT→TOUR, KNOW→TALK) — had the author
planted TRUTH instead of CIRCUMFERENCE, the control would have failed. ~38% of the
key space yields no evidence.

**§6/§9 (book keys) — the "gibberish noise floor" was never computed, and it is
not a property of the ciphertext.** Matched 13-trial ceilings through the
identical pipeline:

| key text | runes | matched ceiling | archived real best | |
| --- | --- | --- | --- | --- |
| Liber AL | 22,045 | **−4.13** | −3.97 | 0.16 **above** |
| Blake | 33,195 | −4.01 | −4.15 | below ✓ |
| Mabinogion | 425,501 | −3.92 | −3.97 | below ✓ |
| KJV | 3.0M | **−3.90** (computed, §36) | −3.79 | below floor ✓ |

The key result is that **the ceiling scales with key-text length** (−4.01 at 33k
offsets → −3.92 at 425k), because the coarse scan cherry-picks the top-200
most-English-looking offsets from a larger pool. So §9's observation that all four
bests cluster near −3.95 is exactly what a **chance maximum** looks like — it is a
selection artefact of the search, not a shared "gibberish floor" property of the
ciphertext as §9 framed it. Extrapolating, KJV's ceiling would be ≥ −3.92, putting
§6's −3.95 at/below its own ceiling too — though that cannot be confirmed while
`keytext_cache/kjv.u8` is missing, which makes **§6 not reproducible from the
repo**. Only Liber AL exceeds its own ceiling, by 0.16 against a ceiling whose
sampling error is ~±0.15 — a marginal excess at the edge of the null, still ~0.43
below the detection floor (−3.54, verified by 5 plants at 5 offsets, all
recovered). The negative stands; the "identical noise floor" sentence does not.

**Two coverage claims that are simply wrong.**
- **Crib-dragging searched 18 cribs, not 32** (§3). `--min-runes 8` silently drops
  4 — including *A KOAN* and *AN END*, the documented openers of pages 14 and 73 —
  and all 10 F-bearing cribs produced **zero** scored placements, every legal
  placement rejected by the literal-ᚠ filter. All 422 scored placements come from
  18 F-free cribs. Given §19 finds no literal-ᚠ convention on the unsolved pages,
  those 10 cribs were effectively never tested.
- **"Both directions" means both SIGNS** (p = c−k, p = c+k), not a reversed key
  text (§6/§9). No key-text reversal or atbash appears anywhere in
  `attack_running_text.py` or `keytexts.py`. A backwards-read key text is the
  classic book-cipher variant, and Cicada demonstrably uses reversed gematria on
  solved pages 06–09 — so this is a genuine, untested, high-prior hypothesis.
  A `--reverse` option now exists and is being run (§32).

**Other confirmed defects.** `crib_drag.selftest()` is partly vacuous — deleting
the literal-ᚠ rule entirely, or zeroing the bigram model, still leaves it passing
(only the structural arm is exercised); its printed "random baseline" of −3.37 is
`−log 29`, an upper bound, where the empirical mean is **−3.95** (LOG.md reasoned
from the wrong number). `attack_keyskip.py` looped `range(N)` for the key START
OFFSET — using the alphabet size (29) as a keystream index bound; planted starts
0/10/28/40 are found but **120 is missed**, so §3's key-skip negative covered
starts ≈0–50 only (now `--max-start`, default 200). `attack_running_text.py` scans
only the first ~140 runes of each segment (mean coverage ≈14%, 4.7% on the
largest), which §6/§9 never state. And across all six scripts **controls were
advisory, never gating** — a FAILED control printed "FAIL" and the script carried
on to report its negative; they now abort.

**Verified sound.** §3's prime/totient key-skip negative is clean and now has
numbers (floor −3.66, matched ceiling −4.77, real bests −4.89…−4.98 — below both);
`attack_keyskip.selftest` genuinely exercises its mechanism (4 of 5 deliberate
breakages kill it); §3's never-computed claim that the best crib keystream is
"indistinguishable from the best of 422 random draws" is **true** (P = 0.31);
`attack_running_text` really does search every offset and its control plants a key
from the same text and recovers it (5/5); and `attack_runningkey`'s
"intrinsically underpowered" self-diagnosis is correct and not a beam artifact
(separation stays ≤0.04 at beam 4000).


## 32. Reversed key texts — the untested book-cipher variant (R4b follow-up)

§31 found that §6/§9's "both directions" only ever meant both *signs*; a
backwards-read key text was never tried, despite Cicada using reversed gematria
on solved pages 06-09. `attack_running_text.py --reverse` closes that gap.

**Crowley's *Liber AL vel Legis*, read backwards — negative.** Best decode
**-3.95** (on 32-36.jpg), against a matched chance ceiling of ~-4.13 for this text
length and a detection floor of -3.54 (a genuine planted running key from the same
text scores there). So the reversed reading lands in exactly the same place as the
forward one (-3.97): ~0.2 above a chance ceiling that a top-200 offset scan is
expected to produce (§31: the ceiling is a selection artefact that scales with
key-text length), and ~0.4 BELOW the score a real break gives. The decodes read as
gibberish (`SRISOODMRCYUPICALEFIRTEOEEAMNTECTIUTIUEARONELL`).

**All three cached texts, read backwards — all negative.** Each control passed
(a key planted in the reversed text is recovered, e.g. Blake at 100% of its
window, −3.50):

| key text (reversed) | best decode | matched ceiling | vs floor (−3.54) |
| --- | --- | --- | --- |
| Liber AL | −3.95 | ~−4.13 | 0.41 below |
| Blake | −4.00 | −4.01 | 0.46 below |
| Mabinogion | **−3.81** | −3.92 | **0.27 below** |

Every reversed reading lands within ~0.15 of its forward counterpart, so reading
direction makes no difference — as expected once §31 established that these
numbers are chance maxima of a top-200 offset scan rather than a property of the
ciphertext. Reversed *Mabinogion* (−3.81) is the closest any book key has come to
the detection floor and sits 0.11 above its own ceiling, but that excess is inside
the ceiling's ~±0.15 sampling error and it is still 0.27 short of the score a
genuine planted key produces — i.e. the narrowest margin so far, not a lead. KJV
cannot be run in either direction until `keytext_cache/kjv.u8` is restored (§31).

Net: the four documented candidate key texts are now covered in both reading
directions × both signs, and are negative throughout — with the honest caveat that
the scan reaches only ~14% of each segment (§31).
`results/running_{liberal,blake,mabinogion}_reversed_2026-08-21.txt`.


## 33. The L=3 short-key brute — NO EVIDENCE, and a false positive from my own verdict rule

The L=3 exhaustive brute (24,389 keys x 2 signs x key-skip) is the experiment §10
declined to run and §30 unblocked. It completed after ~4 h of CPU. Its first
printed verdict was **"AT/ABOVE the break floor: possible real break — INSPECT"**
on segment 71.jpg (key 'WEEO', -3.85). That verdict is **wrong**, and the reason
matters more than the result.

**Why it is not a break.** The detection floor is the minimum score over
hypotheses that *self-recover*, and at L=3 only **1 of 10** planted keys did. The
other nine were beaten by a WRONG key, which won with scores of -3.54, -3.67,
-3.71, -3.78, -3.81, -3.82, -3.82, -3.85 and -3.88. In other words: given 24,389
keys, both signs, and key-skip freedom, this search fits *any* 30-rune text to
about -3.8 — whether or not a real key is present. The real data's best (-3.85)
sits squarely inside that overfitting range and only 0.04 from the matched chance
ceiling (-3.89). The "floor" of -4.00 that triggered the verdict rests on a single
sample and is *lower* than what wrong keys routinely achieve.

**The decode settles it.** Decoding 71.jpg with the flagged key gives:

    BUNTNATHOUSTANDEBURBONANAHMOTEA

— bigram-greedy gibberish with teasing fragments (THOUSTAND, BURBON), precisely
what CLAUDE.md's ground rules forbid presenting as a lead. And the decisive
number: a genuine English string of the same length scores **-3.96**, while this
gibberish scores **-3.85**. *The flagged "break" outscores real English.* At 30
runes with 24,389 keys x 2 signs x key-skip, the trigram score simply cannot
discriminate — which is the same intrinsic underpowerment §4 found for the
key-text-free running-key attack, arriving from a different direction.

**The fix.** `controls.verdict()` now applies a **coverage gate**: below 50%
identifiability it refuses to declare a possible break and returns NO EVIDENCE,
because a floor computed from a handful of survivors cannot separate signal from
overfitting. Under the gate the L=3 run reads: *"only 1/10 planted short keys are
identifiable… this run cannot distinguish a real break from overfitting — it is
not a negative and not a lead."* That is the honest verdict.

**This refines §30, which over-corrected.** §30 said short keys "ARE identifiable"
and treated §10's underpowerment claim as simply refuted. The truth is
size-dependent, and both earlier statements were partly wrong:

| key length | competing keys | identifiable? | what the run yields |
| --- | --- | --- | --- |
| L=2 | 841 | yes (rank 1 of 841) | a **clean negative** |
| L=3 | 24,389 | **no** (1/10 planted recovered) | **no evidence** |

`probe_shortkey_id.py` samples only 400 distractors, so it measures
identifiability against 400 competitors, not against a full brute's 24,389 — it
therefore *overstates* identifiability for L>=3. So §10's original "underpowered"
verdict was **right for L>=3 and wrong for L=2**, while its stated evidence (the
buggy ranking) was wrong either way. The corrected position: L=2 is settled
negative; L=3 and above are beyond this pipeline's resolving power, not ruled out.

`results/shortbrute_len3_2026-08-21.txt`.

## 34. Per-page key resets — a decisive negative (BACKLOG item 9)

The last untested rune-side idea, flagged in §5.3 and never run because our
vendored transcription bundles several .jpg pages per segment and carries no line
marks. rtkd/iddqd's transcription — vendored for the §23 cross-check — has
explicit `%` page and `/` line delimiters, so the structure was available after
all: **72 pages carrying runes, 9–13 lines each of ~22 runes.**

The hypothesis was the one structural variant that could explain §3's uniform
failure *without* requiring an unbreakable pad: if the key pointer **resets at
every page**, no whole-stream attack could ever work, however good the keystream
guess, because the effective unknown is only one page long.

`attack_pagekey.py` tests three schedules over the same key material, with no
per-unit search freedom (which would merely overfit, per §33): `none` (one
continuous pointer, = §3's baseline), `reset0` (pointer returns to K[0] at every
boundary) and `reset_i` (unit *i* starts at K[i], a "page-numbered" key) — across
prime, totient, DIVINITY and FIRFUMFERENFE streams, both signs, with and without
the §4 key-skip. 32 mechanisms.

**Result: negative, with the strongest evidence in the project.**

| quantity | value |
| --- | --- |
| detection floor (planted schedules recovered) | **−3.38** at **100%** accuracy, **32/32 identifiable** |
| matched chance ceiling (independent null, L=10,198) | −6.43 |
| best real decode | **−6.46** |
| margin below the floor | **3.08** |

Three things make this the cleanest negative here. Coverage is **total** — every
one of the 32 schedules is recovered when planted, so nothing is untested-by-
omission. The floor sits exactly at the English reference (−3.38) because these
decodes are deterministic with no beam freedom, so a correct schedule reproduces
English *exactly* — the ideal control. And the analysed sequence is **10,198
runes**, long enough that the trigram score is a reliable statistic, unlike the
30-rune regimes where §33 showed gibberish can outscore real English.

**Per-LINE resets are equally dead.** The finer granularity (54 unsolved pages,
**586 line units** of ~22 runes) gives the same picture: floor −3.38 at 32/32
identifiable, matched ceiling −6.45 at L=12,797, best real **−6.49** — **3.10
below the floor**.

In both runs the winning mechanism on real text is `none`, the continuous-pointer
baseline: **resetting the key helps not at all.** The best decodes
(`NEMPSFXYNWMTHXEOIAOMIEOOEOM…`, `BJDIBOSMNYLFBTFUYOLGEUIAJEANGRSHM…`) are pure
noise. Per-page and per-line keying are ruled out.

This matters beyond one more negative: it closes the last structural hypothesis
that could have explained §3's uniform failure *without* an unbreakable pad. The
remaining explanation for why every keystream attack returns noise is the one §13
named — a keyed pad whose key we do not have.
`results/pagekey_{page,line}_2026-08-22.txt`.

## 35. Closing two coverage gaps the audit exposed (§31 follow-ups)

**§5 — self-referential running keys, with the key offset actually searched.**
§31 showed §5's "exhausted in every form" claim rested on code that hardwired
every key stream to offset 0 and had no control at all: ~26 of ~26,000 natural
hypotheses, about 0.1%. `attack_selfkey.py` searches the offset — **832
hypotheses per segment** (13 streams × 32 offsets × 2 signs) — with the floor and
ceiling the original lacked. Result: **negative, now properly supported.**
Detection floor **−3.81** (12/12 planted (stream, offset) pairs recovered),
matched chance ceiling **−4.43** at the same search freedom, best real **−4.45** —
0.64 below the floor and at/below the ceiling. The best decode
(`BLBOUTTAREASOAYESEMPAENTAGROMEOONUAEIGH…`) is noise.

A detail worth keeping: in calibration, solved-plaintext offsets 234 and 468 are
**not identifiable** — they get recovered as offset 0, because any offset of an
English key text looks English-ish and offset 0 wins the tie. Self-referential
keys drawn from *English* are therefore intrinsically harder to localise than
keys drawn from ciphertext-like streams, which recover exactly.

**§3 — key-skip with a keystream offset bound that is not the alphabet size.**
§31 found `attack_keyskip.py` looping `range(N)` for the key START OFFSET, i.e.
using the 29-rune alphabet size as a keystream index bound; planted starts
0/10/28/40 were found but 120 was missed, so §3's negative only ever covered
offsets ≈0–50. Re-run with `--max-start 200`: still **negative** (best word-score
**0.05**, where an English decode scores >0.3), and the selftest passes at 96%.
Notably the search now picks winners at starts **31 and 104** — the latter beyond
the old bound entirely — so the wider range was genuinely exercised and the
extended coverage changes nothing.
`results/{selfkey_offsets,keyskip_start200}_2026-08-22.txt`.

## 36. KJV, both directions, with its ceiling finally computed — negative, and a power limit

§31 found §6 was not even reproducible (its key cache was gitignored and absent)
and that §9's "every decode sits at the ~−3.95 noise floor" had never been
computed. The key text is now rebuilt (Gutenberg #10, 3,007,380 runes) and
`ceiling_running_text.py` measures the null this attack actually faces.

| KJV | best real | matched ceiling (13 trials) | detection floor | |
| --- | --- | --- | --- | --- |
| forward | −3.79 | −3.90 (median −4.03) | **−3.54** (planted key recovered, 98%) | 0.25 below floor |
| reversed | −3.85 | −3.89 (median −3.98) | **−3.50** (recovered, 100%) | 0.35 below floor |

Both **negative**: a genuine planted KJV key scores −3.5, and the real text
reaches only −3.79/−3.85. The forward result is 0.11 *above* its own chance
ceiling, but a max-of-13 carries ~±0.15 sampling error, so that excess is inside
the noise — and the floor, not the ceiling, is the criterion.

**The power limit is the real finding.** On KJV the ceiling (−3.90) and the floor
(−3.54) are only **0.36 nats apart**. The book-key attack loses discrimination as
the key text grows, because the coarse scan cherry-picks the best of ever more
offsets: Blake (33k runes) has a 0.47-nat window between ceiling and floor,
Mabinogion (425k) about 0.38, KJV (3.0M) 0.36. Extrapolating, a key text of a few
tens of millions of runes would have **no usable window at all** — its noise
ceiling would meet its break floor, and the attack could not distinguish a real
key from chance at any score. This is the same zero-operating-margin problem §31
found for the §7/§8 word keys, arrived at from the other direction, and it bounds
how far the book-key approach can ever be pushed. Larger candidate texts are not
merely unpromising; they are progressively untestable by this method.

With this, all four documented candidate key texts are covered in both reading
directions and both signs, each against a computed ceiling and a demonstrated
floor. `results/{running_kjv,running_kjv_reversed,ceiling_kjv,ceiling_kjv_reversed}_2026-08-22.txt`.
