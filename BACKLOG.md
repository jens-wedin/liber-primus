# BACKLOG.md — experiments, by status

Framing: hypothesis → method → **control** → priority. Nothing is trusted
without a positive control (encrypt known English with the scheme, recover it)
and a matched chance ceiling — both live in `controls.py`. Most results are
negatives; a clean negative with a control beats a flashy maybe.

**Ids (N1–N19) are stable anchors** cited in REPORT.md, LOG.md and commit
messages — kept even after an item is closed, so references never rot. This file
is organised by STATUS, not by number. Detailed evidence for every closed item
lives in REPORT.md at the cited § and in LOG.md by date.

---

## OPEN — still to run

Two items remain, neither runnable-to-a-result here: N14's local halves are
closed (§59) and only its **external OSINT** residual is left, and N17 needs the
**author to submit**. Every in-reach experiment this campaign is now closed.

### N14. Deep-web-hash hunt — LOCAL halves DONE (§59); only the external OSINT remains.
The three tractable parts are now closed:
- **Code→byte map — DONE (§53):** our codes reproduce rtkd's 256-byte "String 4"
  256/256.
- **Hash battery on String-4 — DONE (§59), NEGATIVE:** 12 renderings × 11
  algorithms = 132 hashes vs the AN-END 512-bit target (§27); no match. Whirlpool
  and Streebog-512 are absent from the local OpenSSL build (the community harness
  `cicada-solvers/Cicada-DWH-HashcatAttempts` covers them). Low prior confirmed —
  Cicada says "a page," String-4 is a byte matrix.
- **Dukotah's 6 contested byte indices — DONE (§59), RESOLVED:** §53 fixed 25; the
  other five (175 `0I`=18, 182 `2l`=167, 199 `0l`=47, 215 `1O`=84, 237 `0W`=32)
  agree with rtkd 256/256 and sit on pp.67/68 (§21 scan-verified code-by-code).

**Residual — external only, not runnable here.** Finding the page that hashes to
the target is a Tor/clearnet OSINT hunt, out of scope for this toolkit (§27), run
by the community (`Cicada-DWH-HashcatAttempts`, `3301-hash-alarm`). The algorithm
is unconfirmed (a 512-bit battery, not just SHA-512) and the onion path is a dead
end (Northeastern "honions" → unindexed clearnet). This is the §13 wall's numeric
sibling: the bytes behave as key material behind their own pad (§22, Dukotah B-05).

### N17. Publish the cryptodiagnosis — DRAFT + VENUE TYPESET (§ paper/). **Write-up + post, not an attack.**
**DRAFT 2026-08-24.** Full draft in the Bean-K4 cryptodiagnosis genre. References
and the Gematria Primus table are complete. Two typeset builds compile clean with
Tectonic (XeTeX): `paper/liber-primus-cryptodiagnosis.tex` (readable single-column)
and `paper/liber-primus-cryptodiagnosis-histocrypt.tex` (the HistoCrypt author-kit
ACL two-column, 7 pages, `paper/histocrypt.sty`). Remaining: submit. Below is the
original note.
No peer-reviewed cryptanalysis of the Liber Primus exists; Bean's "Cryptodiagnosis
of Kryptos K4" (HistoCrypt) is the exact precedent. Our doublet / key-skip model,
the soft-rejection fit (p_keep≈0.19, §44), and the control-validated elimination
ledger fit Cryptologia or HistoCrypt. Publication recruits the community that
could supply the external key material the code pages appear to need.

---

## DONE — closed this campaign (all control-validated)

Each is a negative, a no-power finding, or a resolved artifact. Full evidence at
the cited § in REPORT.md.

| Id  | Item | Outcome | § |
| --- | --- | --- | --- |
| N5  | Community consensus (LP2 = 2/58 solved) | confirmed through Aug 2026 | sweep 2 |
| N6  | Derived-seed hash pad via the beam | NEGATIVE; §13 wall sharpened to seed entropy | §41 |
| N7  | Dukotah ledger cross-diff + soft-rejection fit | same object to 0.07%; p_keep≈0.19 reconciled | §44 |
| N8  | Keyless depth detection (Smith-Waterman) | NO POWER at LP scales (power analysis) | §43 |
| N9  | Word/line/page-initial uniformity | word/page CLEAN NEGATIVE; line-initial anomaly → N19 | §45 |
| N10 | Gromark / chain-addition primers | L=2 = Fibonacci (covered); L=3 NEGATIVE | §42 |
| N11 | Long exact repeats vs a Smirnov null | coincidental, no Kasiski anchors | §49 |
| N12 | Non-additive affine cipher (all multipliers) | NEGATIVE, well-powered | §48 |
| N15 | Unused-hint numerics as keystreams/seeds/primers | NEGATIVE; the full `hints_never_used.md` page now closed (2013/2015 whitespace added; wisdom/folly = high-entropy binary, not text) | §51 |
| N16 | Doublet-suppressing keystreams (OEIS/arith) | REFUTED in principle + NEGATIVE | §50 |
| N18 | LP2-as-pad inversion (F-01) | NEGATIVE, closed by uniformity | §47 |
| N19 | Line-initial anomaly vs independent segmentation | segmentation/transcription ARTIFACT | §46 |
| N13 | Steg provenance gate on the 75 scans | runic scans are 400-DPI re-saves (steg-dead) | §52 |
| N14a | Code→byte map for pages 66–68 | **SOLVED** — reproduces rtkd's String 4 256/256 (map + 3 l/I fixes) | §53 |
| N3  | mortlach transform space (orientation) | NEGATIVE; rest of the space collapses to covered ground | §54 |
| N1  | 29-rune interrupter (relikd's finished DB) | NEGATIVE; unsolved at floor, solved recover — verified firsthand | §55 |
| N4  | modulo / alternating-alphabet (relikd DB) | NEGATIVE; higher scores are short-slot inflation | §56 |
| N21 | Cypherpunk Manifesto + Gibson's Agrippa as running keys | NEGATIVE both texts, both signs + reversed; controls PASS | §57 |
| N20 | 05.jpg appended blob vs an independent copy | scream314 CORRUPTION ARTIFACT; independent onion7 copy is clean | §58 |
| N14b | Hash battery on String-4 + Dukotah's 6 contested bytes | hash battery NEGATIVE (132 combos); all 6 bytes RESOLVED (agree rtkd 256/256) | §59 |
| N10-ext | Gromark per-segment (per-page primer) L=3 brute | NEGATIVE; best real −4.17 vs floor −3.79, ceiling −4.14 | §60 |

**Set aside (not items), recorded so they are not re-proposed:**
- A classic **book code** (line:column index into a source text; named in
  `download/cicada talk 2.md` for the 2012 path). Structurally a poor fit for LP2
  — one rune is a single value in 0..28, too small to be a line:column index
  without grouping, and the lag-1 no-repeat is not a book-code signature.
- **Gromark L≥4 primers / other lags.** L=3 is closed global (§42) and
  per-segment (§60), both negative; L=2 is Fibonacci (§3). L=4 is 707,281 primers
  (~29× the L=3 cost per brute) for a negligible-prior extension of an
  already-negative family with no identifiability advantage. Not pursued.

---

## Earlier backlogs — all resolved (kept for the record)

- **R-section (§28 self-audit re-dos):** R1, R2, R3, R5 done (§29 — every
  recalibrated negative held; `controls.py` is the systemic fix). R4 done (§30
  R4a statistical core, §31 R4b attack scripts — three negatives weakened, none
  overturned; two coverage-claim corrections).
- **P1–P3 / items 1–9 (opened 2026-08-21):** all closed —
  literal-ᚠ interrupter (§19), ᚠ-position map (§20), code pages (§21–§22),
  transcription cross-check (§23), squares as a message (§24), GP-sum filter
  (§25), pre-LP2 hints (§26), AN END hash documented (§27), per-page/line resets
  (§34), difference-stream key families (§38), Emerson/Rune Poem (§37), composed
  manglings (§39).

---

## Out of reach — the documented wall

A **high-entropy or truly external keyed pad** (`c = p + K`, §13) is unbreakable
without the key. N6 (§41) sharpened this: a SHORT-seed derived pad IS finite and
beam-recoverable, so the wall is specifically **seed entropy**, not the pad idea —
and thematic low-entropy seeds are already ruled out. The numeric/image content
(N13/N14) is the way *around* the wall, and it sits behind its own keyed pad.

---

## Reusable external assets (from the 2026-08-23 research sweeps)

- `relikd/LiberPrayground/db/` — the finished 29-rune interrupter sweep (N1).
- `Dukotah/cicada3301` — `LEDGER.json` + `PROBLEM.json` + `benchmark/` (N7), and
  `read4.json`, a vision transcription used for N19 (staged gitignored in
  `download/`).
- `mortlach/runeglish-language-model-transition-probabilty-matrices` — an
  independent n-gram scoring model to cross-check our wordfreq LM.
- `krisyotam/cicada3301` `original-onion7/` — 61 provenance-cleanest raw images
  (N13).
- `cicada-solvers/Cicada-DWH-HashcatAttempts` — a ready hash harness (N14).
- Watch: `mortlach/RuneDecrypterPrime` (active, assets in GitHub Releases).

Condensed research reports (all URLs): `results/external_research_2026-08-23_sweep2.md`.
