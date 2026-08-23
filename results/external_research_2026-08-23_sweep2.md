# External research sweep 2 — 2026-08-23

Four parallel research agents ran to completion. This file is the condensed
archive of their reports. The first sweep (2026-08-23, N1–N5) lost 30 of 98
agents; this sweep covered all four planned lanes. Distilled actions live in
BACKLOG.md §N6–N17.

Labels: **verified** = the agent read the page/file/data directly.
**inferred** = from search summaries or README claims. **rumor** = unsupported.

---

## Lane 1 — Solve status 2023 → Aug 2026

- **LP2 stays 2 of 58 solved (56.jpg, 57.jpg); LP1 all 17 solved.** Verified at
  www.cicadasolvers.com/quickstart/ (briefing images Apr 2025). No authentic
  Cicada message since April 2017.
- **No Cicada/LP talk at DEF CON 32 (2024) or 33 (2025).** DEF CON 31 (2023)
  remains the latest. Negative finding, moderate confidence.
- The wiki year page `Liber_Primus_Updates_2025` holds ONE entry — a 2025
  "outguess data on all pages" claim. The wiki's own JFIF-header analysis
  contradicts it. Low credibility.
- Claimed breaks 2023–2026, all non-cryptanalytic on inspection (verified):
  - github.com/leorahross2015-afk/Full-Translation-of-Liber-Primus-Cicada-3301-
    (Sept 2025): channeled creative writing. No method, no key.
  - github.com/Nabilhamidi-cell/Anarchy-0-the-Code-of-Liber-Primus- (Dec 2025):
    a philosophical "conceptual key".
- **Doublet finding independently reproduced.** The wiki's
  Frequency_Analysis_Unsolved_Pages page gives a per-chapter doublet table
  (Cross 0.549% … Hollow 0.977%) and "86 same-rune 2-grams in ~13,000 runes" —
  our exact count. Higher n-grams flat: quadgrams 127 repeated vs 117.2±10.9
  random (~0.9σ). Caveat: shared transcription lineage is likely.
- **Dukotah/cicada3301** (github.com/Dukotah/cicada3301, created 2026-06-18,
  pushed 2026-08-19): a parallel rigor project. Verdict "OTP-class, NOT
  unsolvable". Key claims (README-verified, not reproduced):
  - Models the no-repeat as SOFT rejection sampling: p_keep≈0.18, ~83% doublet
    suppression; the 86 residuals are leak-through. Frames the stream as a
    Smirnov word / Carlitz composition.
  - Rigid-alignment decoding scores a CORRECT key at −6.835 (noise). A
    skip-aware beam recovers the same plant at −4.170, 98.9% char recovery
    (SHA-256 counter mode, seed CICADA3301; wrong seed −7.349).
  - Ships LEDGER.json (57 hypotheses: 2 eliminated, 3 negative, 21 never-run,
    18 open, 10 partial), PROBLEM.json (ciphertext pinned by SHA-256),
    verify_solution.py --selftest, plant-and-recover benchmarks.
  - Side result: authentic Cicada connected prose totals 359 words — below any
    stylometric attribution floor.
- Live community front: the deep-web hash. cicada-solvers org repos
  Cicada-DWH-HashcatAttempts (Oct 2025, hashcat battery incl. Streebog, logged
  negatives), WPCH-3301, lphelper, 3301-hash-alarm.

## Lane 2 — Steganography and hash/OSINT

- **The outguess front is closed, verified first-hand.** The agent pulled
  rtkd/iddqd `lp_outguessed/` (outguess run on all 75 pages) and analyzed the
  outputs itself:
  - Readable payloads come ONLY from intro/instruction pages, and every one is
    a known, consumed 2014 clue (PGP blocks, "Let the text guide you", the
    bigram hint, the magic-squares instruction).
  - The runic pages yield 0 bytes or 58152-byte high-entropy dumps. The agent
    md5-checked the dumps: all differ, ~0.38 printable ratio — the signature of
    null extraction. No hidden text in the unsolved pages.
- **Outguess payloads do not survive re-hosting.** The wiki's
  Outguess_detection_visual_analysis page gives a JFIF fingerprint: genuine
  outguess output has density unit = unknown, X/Y density 1×1. Recompression
  destroys the DCT payload. Only original onion7 JPGs are valid steg targets.
- **Archives.** rtkd/iddqd is the community-standard archive.
  github.com/krisyotam/cicada3301 separates provenance tiers:
  `liber-primus/pages/` (75 JPGs as distributed) and `original-onion7/` (61 raw
  files incl. HTML — provenance-cleanest set). archive.org/details/liber-primus
  is a 2020 fan upload (Liber Primus.zip, 9,086,651 B, md5
  39895a847b9b65c1688a57ffaf9df8f1), not authoritative. No public master table
  of original onion7 file hashes exists.
- **"AN END" SHA-512 hunt: unsolved, judged a dead end.** Algorithm unconfirmed
  (SHA-512 / BLAKE-512 candidates). Tor v2 onions died Oct 2021; if the target
  was a v2 service it is unreachable and possibly archived nowhere.
  martinlindhe/gohash `findhash` ships this hash as its worked example; the
  keyspace is not brute-forceable. No candidate page ever found.
- **Unused hints, curated** (wiki Possible_hints_never_used):
  - 2012 P.S. number (128 digits): 10412790658919985359827898739594318956404425
    10695567564373922695237268242385295908173983439037037447576486341520342349
    935710871363
  - Onion cookies: 167=6941f707ff39d259ff71657a79cb6b54c184d2f0455810109c1a96
    0860bde0e6 and 761=7bc1e7805ccfa518920f0d94fc4e8f7dbd83287a03b337b89109cd
    2287befae5
  - /tmp/wisdom and /tmp/folly (2013 ISO); missing telnet primes; trailing-
    whitespace prime sequences (§26 tested the numeric-prime subset).
- The 1033.jpg collage = four Blake works (Newton, Ancient of Days, two
  Nebuchadnezzars) + a superimposed cicada. Iconography only; no extracted
  ciphertext. Page-reorder theories remain rumor-tier.

## Lane 3 — Solver tooling and datasets

- **relikd/LiberPrayground InterruptDB: the finished 29-rune interrupter sweep
  exists as data** (verified — the agent parsed the raw db files). Format:
  `desc | irp_count | score | interrupt-rune | key_length | positions`;
  ~20,100 rows, key lengths 1–32, first 20 interrupt occurrences, objectives
  db_high (max IoC) and db_norm (toward English 1.7737). Results: unsolved
  sections best db_norm 0.55–0.63 (p0-2: 0.60 @ kl=14; p3-7: 0.63 @ kl=12;
  p54-55: 0.58 @ kl=16). Solved control pages score 0.99–1.00. A large
  independent NEGATIVE for interrupter + polyalphabetic key, and it directly
  de-risks our N1 build: query their db instead of the ~38 h rebuild.
- **mortlach**: key-drag (Cython crib-drag engine over 2-variable cipher
  functions × interrupters × gematria rotations × transpositions),
  lp-decrypter, Liber-Primus-Crib-Assist,
  runeglish-language-model-transition-probabilty-matrices (n-gram matrices
  conditioned on word length + in-word index — reusable independent LM), and
  RuneDecrypterPrime (pushed 2026-08-23, README stub, assets in Releases —
  watch it). Methods published, no results ledger, no positive solve.
- Other repos: krisyotam/cicada3301 (best ecosystem index),
  iBotPeaches/cicada_3301, localavaster/cadrypt (workbench; ships
  mod29_oeis_sequences), cmbsolver/cmbcidada3301, NoxxGames/LiberPrimus-GPU
  (CUDA scaffolding, no kernels yet), RuneSwiss, plus 2026 hypothesis-only
  repos. Nothing with a novel validated result.
- **Word-repeats table** (wiki, verified): 5 repeated multi-rune ciphertext
  sequences book-wide, e.g. ᛞᛄᚢᛒᛖᛁ at 6555 & 12950, ᛒᛗᚱᚾᛗ at 5448 & 12001;
  gaps 1031–6533. Near the random expectation for 5-grams; positions are given.
- **Transcription disputes**: rtkd/iddqd is the de-facto standard (community
  tools derive from it — shared lineage likely, consistent with §23). Dukotah
  flags 6 contested bytes in the pages-49-51 hex (indices 25, 175, 182, 199,
  215, 237) and per-instance O/A/AE disagreements. Words cross page boundaries
  with no delimiter.

## Lane 4 — Academic work and transferable methods

- **No peer-reviewed cryptanalysis of the Liber Primus exists** (Cryptologia,
  arXiv, HistoCrypt, Semantic Scholar searched). Closest template: R. Bean,
  "Cryptodiagnosis of Kryptos K4" (HistoCrypt) — a publishable diagnosis of an
  unsolved cipher. Our REPORT.md appears to be the most rigorous LP treatment
  anywhere.
- **Z340 solve** (arXiv:2403.17350; AZdecrypt): one statistical anomaly defined
  a parametric family of inverse transposition transforms; 655,088 variants
  enumerated; hill-climbing homophonic solver with 6-gram scoring; robust to
  encipherment errors. The pipeline does NOT transfer (LP has no substitution
  residue — flat unigrams). The methodology does, point for point; the LP
  complication is that the key-skip is key-dependent, so any enumeration must
  be joint over (key, skip schedule).
- **Metaheuristics**: Lasry's M-209 work (Cryptologia 42(6), 2018) proves hill
  climbing can attack keystream-generator internals, not just alphabets.
  CryptoCrack has a solver for the ACA "Interrupted Key" cipher — a
  plaintext-synchronized interrupter that restarts the key at word divisions.
- **Neural/LLM decipherment (2018–2026): not applicable.** The entire
  literature targets substitution-class ciphers with retained n-gram
  structure. Nothing published handles a desynchronised or interrupted
  keystream. A neural LM adds nothing when desync kills the score signal for
  any scorer.
- **Output-constraint precedents**: Enigma's no-self-encryption → crib
  impossible-alignment elimination, Bombe constraint propagation, Banburismus
  Bayesian depth scoring. Closer analogue: Lorenz/Tunny irregular ψ-wheel
  stepping, attacked in DIFFERENCE space (Tutte double-delta). Our §12
  difference battery is the Tutte move; its negative says the LP skip does not
  leak that way. No dedicated literature exists for a "no adjacent repeat"
  output rule; the constraint class is Smirnov words / Carlitz compositions.
  The rule leaks ≤ N·log₂(29/28) ≈ 657 bits over 12,956 runes, but only under
  a joint key hypothesis.
- **Unicity**: with redundancy ≈3 bits/rune, a 128-bit seed gives ≈43 runes; a
  256-bit seed ≈85. At 12,956 runes any short-seed scheme is far past unicity —
  unbreakability can only be computational. "OTP-class" (cannot distinguish a
  true pad from a short-seed derived keystream) is the correct formulation;
  nobody argues the OTP case in an academic venue.
