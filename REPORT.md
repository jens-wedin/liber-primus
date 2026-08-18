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

## 4. Interpretation and where to go next

The numbers reproduce and sharpen the community consensus: the unsolved
Liber Primus is not a substitution, not a repeating-key Vigenère, not the
prime/totient streams used on the solved pages, and not a short-primer
autokey. The flat IoC says the keystream is close to uniform; the 17σ
doublet deficiency says it is *not* independent of position — the two
together point at something like a running key drawn from an unknown text,
a hash/PRNG-derived stream, or a scheme with a built-in no-repeat
constraint, possibly keyed per page.

Promising directions this toolkit is set up for:

1. **Crib-dragging** Cicada's own recurring phrases ("A KOAN", "AN
   INSTRUCTION", "KNOW THIS", "THE PRIMES ARE SACRED") along each segment:
   for each offset, derive the implied keystream and test it for structure
   (primes, totients, digits of constants, gematria sums of the crib …).
2. **Modeling the doublet deficiency**: simulate candidate schemes
   (autokey variants with long primers, lagged keystreams, no-repeat
   rejection sampling) and compare their doublet/IoC signatures against the
   observed 0.66% / 1.000 — use the anomaly to *filter hypotheses* before
   brute-forcing them.
3. **Per-page keying**: the first-word/first-line of several pages may be
   headers ("A KOAN"-style); testing key resets at line or page boundaries
   shrinks the effective unknown per unit.
4. Cross-checking against the **page images** (rune spacing, section marks)
   for information the transcription flattens.

Sober expectation: this cipher has resisted a decade of exactly this kind of
analysis; the realistic value here is a verified, scriptable foundation to
test new hypotheses quickly rather than an imminent break.
