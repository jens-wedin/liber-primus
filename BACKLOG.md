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

Ordered by how actionable they are here. The first two need external inputs; the
rest are runnable but lower-prior than the eleven already closed this campaign.

### N20. Verify the 05.jpg appended blob against an independent copy — LOW
§52 found 72,700 bytes appended after a complete image on scream314's 05.jpg (no
file header, entropy 6.90, ends mid-SOI, on a 400-DPI re-save) — most consistent
with a corrupt/concatenated mirror file. Fetch page 05 from an independent source
(`rtkd/iddqd` or `krisyotam/cicada3301` `original-onion7/`) and compare: if their
copy is clean, it is a scream314 artifact (close); if it also carries the blob,
carve and characterise it. Cheap once the independent image is local.

### N14. Deep-web-hash battery on the verified String-4 bytes — LOW-MED. **OSINT / external.**
The code→byte map half is **DONE (§53)** — see the DONE table. What remains is the
OSINT hash hunt: run the now-verified 256 bytes (and their hex/ASCII renderings)
through the community harness `cicada-solvers/Cicada-DWH-HashcatAttempts`
(SHA-512, Streebog, …), checking their `results/` first for prior coverage. Low
prior — §22 ruled out pad/index/table for these bytes and Dukotah's B-05 could
not separate a keystream derived from the block from the real stream, so the
derived-pad reading is the §13 wall. Still resolve Dukotah's other 5 contested
byte indices (175, 182, 199, 215, 237) from the scans — §53 already resolved
index 25 (`3l → 3I`).
- Sources: `rtkd/iddqd` `byte-strings/byte-strings` (vendored as
  `data/rtkd_string4.hex`); `cicada-solvers/Cicada-DWH-HashcatAttempts`.

### N10-ext. Gromark, remaining cells — LOW, compute-driven.
§42 closed L=3 chain-addition (global, negative) and showed L=2 is Fibonacci
(covered by §3). Untested: the per-segment (per-page primer) L=3 brute, and L≥4
primers / other lags. Low prior given the global negative and the partial
identifiability at head 44.

### N17. Publish the cryptodiagnosis — DRAFT WRITTEN (§ paper/). **Write-up + post, not an attack.**
**DRAFT 2026-08-24 (`paper/liber-primus-cryptodiagnosis.md`).** Full first draft in
the Bean-K4 cryptodiagnosis genre. Remaining: complete references + GP table,
adapt to the venue's LaTeX template, and submit. Below is the original note.
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
| N15 | Unused-hint numerics as keystreams/seeds/primers | NEGATIVE; confirms §26 for exact values | §51 |
| N16 | Doublet-suppressing keystreams (OEIS/arith) | REFUTED in principle + NEGATIVE | §50 |
| N18 | LP2-as-pad inversion (F-01) | NEGATIVE, closed by uniformity | §47 |
| N19 | Line-initial anomaly vs independent segmentation | segmentation/transcription ARTIFACT | §46 |
| N13 | Steg provenance gate on the 75 scans | runic scans are 400-DPI re-saves (steg-dead) | §52 |
| N14a | Code→byte map for pages 66–68 | **SOLVED** — reproduces rtkd's String 4 256/256 (map + 3 l/I fixes) | §53 |
| N3  | mortlach transform space (orientation) | NEGATIVE; rest of the space collapses to covered ground | §54 |
| N1  | 29-rune interrupter (relikd's finished DB) | NEGATIVE; unsolved at floor, solved recover — verified firsthand | §55 |
| N4  | modulo / alternating-alphabet (relikd DB) | NEGATIVE; higher scores are short-slot inflation | §56 |

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
