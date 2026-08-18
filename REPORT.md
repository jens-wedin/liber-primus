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
