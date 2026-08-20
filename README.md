# Liber Primus toolkit

Cryptanalysis tooling for the unsolved sections of Cicada 3301's *Liber
Primus*, working from the rune transcription in
[scream314/cicada3301](https://github.com/scream314/cicada3301/blob/master/liber_primus.md)
(vendored at `data/liber_primus.md`).

Findings so far are in [REPORT.md](REPORT.md). A one-page visual overview is
published at **<https://jens-wedin.github.io/liber-primus/>** (source in
`index.html`).

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
| `keytexts.py` | Loads/caches candidate running-key texts (KJV from the `bible-kjv` npm package; any plain-text file, ASCII-folded so non-English texts don't crash) as rune streams. |
| `attack_running_text.py` | Tests any book as the running key against the key-skip hypothesis: trigram coarse scan → key-skip beam confirm, with a planted positive control (planted at the key's midpoint, so short texts work too). |
| `attack_vigenere_skip.py` | Short word key (Vigenère) + key-skip desync: beam-decodes Cicada/common word keys, with a planted positive control. `--mangle` also tests coined/mangled variants (the FIRFUMFERENFE=CIRCUMFERENCE family). |
| `mangle.py` | Coined/mangled key-word generator (consonant-collapse, atbash, reversal, vowel-rotation), self-checked to reproduce CIRCUMFERENCE→FIRFUMFERENFE. |
| `attack_shortbrute.py` | Exhaustive very-short (len 2..L) key brute + key-skip, judged against a random-ciphertext chance ceiling (short keys are underpowered under key-skip — see below). |
| `probe_shortkey_id.py` | Measures how identifiable a length-L key is under key-skip (ranks a planted key against random ones). |
| `download/` | Candidate key texts (Liber AL, Mabinogion, Blake — public domain) + the research briefing, with provenance. |
| `docs/` | Background briefing on Cicada 3301, the runes, and the ciphers. |
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
`wordfreq`, and `attack_running_text.py` also needs `numpy` —
`pip install -r requirements.txt`. Models are cached under `model_cache/`
(gitignored) and rebuild in ~3s on first use.

The KJV key stream for `attack_running_text.py` is built once from the
`bible-kjv` npm package (Project Gutenberg is often network-blocked):

```bash
npm pack bible-kjv && tar xzf bible-kjv-*.tgz          # gives package/dist/
python3 keytexts.py --build-kjv package/dist           # caches keytext_cache/kjv.u8
python3 attack_running_text.py --key kjv               # runs the attack + control
```

Any other candidate key text works too:
`python3 keytexts.py --add-textfile mybook.txt mybook` then
`--key mybook`. The public-domain texts Cicada is documented to have used or
referenced (Crowley's *Liber AL*, the *Mabinogion*, Blake) are vendored under
`download/` — all tested and ruled out (see [REPORT.md](REPORT.md) §9).

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
