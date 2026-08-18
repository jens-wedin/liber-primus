# Liber Primus toolkit

Cryptanalysis tooling for the unsolved sections of Cicada 3301's *Liber
Primus*, working from the rune transcription in
[scream314/cicada3301](https://github.com/scream314/cicada3301/blob/master/liber_primus.md)
(vendored at `data/liber_primus.md`).

Findings so far are in [REPORT.md](REPORT.md).

## Layout

| File | Purpose |
| --- | --- |
| `gematria.py` | The Gematria Primus table (29 runes ↔ letters ↔ primes) and transliteration both ways, including digraph handling (TH, ING, EA, …). |
| `parse_lp.py` | Parses the markdown into segments (section, key annotation, rune text). Run directly for an inventory. |
| `ciphers.py` | Cipher ops in rune-index space mod 29: shifts, atbash (reversed gematria), Vigenère, prime/totient keystreams — encrypt and decrypt, with Cicada's literal-ᚠ rule. |
| `validate_solved.py` | Reproduces every known solved page. Keyed pages are verified by *forward-encrypting* the known plaintext and comparing rune-for-rune. |
| `analyze_unsolved.py` | Statistics (IoC, periodic IoC, doublet rate) plus a battery of simple attacks over all unsolved segments. |
| `attack_autokey.py` | Brute force of plaintext- and ciphertext-autokey with short primers. |
| `crib_drag.py` | Word-aligned crib-dragging with the literal-ᚠ filter; tests implied keystreams for structure. `--selftest` recovers known keys. |
| `doublet_sim.py` | Simulates cipher families and measures which reproduce the observed (IoC 1.000, doublet 0.66%) signature. |
| `no_repeat_model.py` | Models the no-adjacent-repeat mechanism (re-roll vs key-skip) and quantifies the keystream desync. |
| `attack_keyskip.py` | Beam-search attack on the key-skip hypothesis over prime/totient streams. `--selftest` proves 98% recovery when the hypothesis holds. |
| `attack_runningkey.py` | Key-text-free running-key attack (joint English-ness of plaintext and key). Self-calibrates and reports when it is underpowered. |
| `language_model.py` | Frequency-weighted n-gram model (order 2–4) over rune indices, built from the `wordfreq` English list with Stupid Backoff. Run directly for the English-vs-random discrimination test. |
| `attack_keycrib.py` | Candidate-key attacks: self-referential running keys via key-skip (Part A) and a common-word key crib with a random-ciphertext false-positive control (Part B). |
| `results/` | Archived run outputs, dated. |

## Usage

```bash
cd liber-primus
python3 parse_lp.py          # segment inventory
python3 validate_solved.py   # should print 9/9 checks passed
python3 analyze_unsolved.py  # statistics + simple-attack battery
python3 attack_autokey.py    # autokey brute force (a few minutes)
```

Most scripts need only the Python 3 standard library. The n-gram model
(`language_model.py`, and the `--order` paths of the beam attacks) needs
`wordfreq` — `pip install -r requirements.txt`. The model is cached under
`model_cache/` (gitignored) and rebuilds in ~3s on first use.

## The cipher conventions (verified, not assumed)

All of these are proven by exact-match forward encryption in
`validate_solved.py`:

- Encryption is `c = (p + k) mod 29` in Gematria Primus index space; the
  "shift up/down" wording in community notes refers to direction conventions,
  and the key numbers quoted there are often `29 − index`.
- **Literal-F rule**: every plaintext F is written as ᚠ *unencrypted* and does
  not consume a key value. Crucially, ordinary encryption can also produce ᚠ
  (e.g. M+I ≡ 0 in "WELCOME"), so a ciphertext ᚠ is ambiguous when
  decrypting — which is why validation encrypts forward instead.
- Digraphs are transliterated per word (TH, ING before NG, EA, AE, OE, IA/IO,
  EO), never across word boundaries. K→C, V→U, Q→CW.
