# Dukotah/cicada3301 LEDGER cross-diff (N7, 2026-08-23)

Same object: our unsolved stream matches theirs on the first 24 indices
and on per-page lengths (first 10 exact); totals differ by 9 runes
(12,947 vs 12,956 = 0.07%), the known transcription-lineage delta (§23).
Their SHA-256 023312... != ours af63d2...; comparable, not byte-identical.

Their ledger: 57 entries. {"open": 18, "superseded": 1, "in-flight": 1, "negative": 3, "partially-run": 10, "eliminated": 2, "never-run": 21, "inconclusive": 1}

## A. Shared negatives — independent confirmation of our results
- B-21 [partially-run]: Seeded-PRNG pads are eliminated ('do not re-run').
- R12-C1 [negative]: The cipher is unbounded k-history feedback / autokey: key at position i = f(last k already-known runes), decoded left-to-right. The community state of
- VERDICT-OTP-CLASS [open]: LP2 0-54 is OTP-class: a full-length keystream under a soft anti-repeat filter (~83% suppression). The ciphertext is indistinguishable between a TRUE
- R12-D2 [eliminated]: A load-bearing statistic is miscounted (page/segment joins double-counting, interrupters wrongly included/excluded, etc.).
  (B-21 seeded-PRNG = our §13; R12-C1 k-history feedback ⊇ our §12;
   OTP-class verdict = our §13 wall; R12-D2 stat-miscount = our §28/§30.)

## B. They ran it, we had NOT — importable negatives
- B-05 [negative]: The pp49-51 256-byte payload is a PRF seed expanded into a runic keystream (RC4/AES-CTR/SHA-counter/HMAC-DRBG), rather than key material used directly
- R12-A1 [negative]: The author's own CicadaOS binary files (DATA/_560.00/.13/.17, prime_echo, folly/wisdom, 761.mp3) are the pad - period-correct key material Cicada demo
  (B-05 pp49-51 256-byte block as PRF/RC4 seed → runic keystream: NEGATIVE,
   directly relevant to our N2/N6; R12-A1 CicadaOS binaries as keys: NEGATIVE.)

## C. Where OUR rigor exceeds theirs
- B-16 [eliminated]: Every keytext null is unsound because the beam decoder was validated against the key-SKIP mechanism (key desyncs) while Campaigns X/XI pin the mechani
  (They ELIMINATED their own keytext nulls as unsound — the beam-decoder
   validation flaw. We checked ours in N6: attack_running_text.py confirms
   with the key-skip beam and its planted-skip control passes, so OUR
   KJV/Crowley/Mabinogion/Blake negatives STAND where theirs do not.)

## D. Neither ran / both open — candidate next work
- C-02 [never-run]: Line-initial / word-initial / page-initial ciphertext-rune uniformity test — the detector for forcing (an acrostic or layout constraint imposed in cip
- D-03 [open]: Homophonic-downward (surjective 29→k, k=5..26) annealing/EM search. Closed only by an inference from bigram flatness (Campaign XIV P4, +0.81σ); the se
- D-04 [open]: Non-additive ciphertext-feedback coefficient sweep ran on 3 of 55 pages (p0/p5/p20) at orders k≤3 with 3 seeds, then was written up as "closes the las
- B-08 [never-run]: SEED residue — >2³² seeds, other generators, nonzero keystream offset
- B-02 [open]: Keystream offset ≠ 0. Round 8 states its sweep "assumes key index 0 aligns with the first rune of LP2 page 0". An author who enciphered LP1 first, or
- E-01 [never-run]: Payload as an RSA signature/ciphertext under known Cicada moduli: compute `pow(s,e,n)` in both endiannesses for every published 3301 modulus and patte
- F-01 [never-run]: LP2-as-pad inversion — the unsolved pages are key material, not a message. Use the 12,956-rune stream (fwd/rev, ±, Atbash) as a running key against ev
- D-01 [never-run]: Generator-fingerprint suite items (1)+(2): conditional next-rune distribution after each rune value, and a windowed χ² under-dispersion sweep, plus mo
  (C-02 = our N9 line/word/page-initial uniformity; D-04 = our N12 non-additive;
   B-08 extends our N6 to >2^32 seeds + offsets; D-03 homophonic-downward is the
   Z340 method; F-01 'LP2 IS the key not the message' = our N2 pp49-51 inversion.)

## E. Their B-04 (in-flight) == our N6
- B-04 [in-flight]: The LP2 keystream is a cryptographic keystream derived from a short, Cicada-flavoured seed (MD5/SHA-1/SHA-256/SHA-512 chain or counter, HMAC counter-K
  (Derived short-seed keystream dictionary. We ran a slice (N6/§41): thematic
   passphrase hash-CTR seeds NEGATIVE, floor −3.73. Their B-04 stays in-flight.)

## F. No-repeat mechanism reconciliation
Their model: SOFT anti-repeat, ~83% suppression (p_keep≈0.18). Our §11: UNIFORM
resolution. Orthogonal + compatible. Fitted on our stream: p_keep = 86/(12934/29)
= 0.193 ≈ their 0.18. Simulation (p_keep=0.19) reproduces flat IoC + 0.66% doublet.
Reframes the 86 doublets as the filter's acceptance LEAK (signal), agreeing with §23.
