# download/ — candidate running-key texts & research

Source material gathered for the running-key attack (`attack_running_text.py`)
and the background briefing. All texts here are **public domain**. The `.u8`
rune-index caches under `keytext_cache/` (gitignored) are rebuilt from these
files via `python3 keytexts.py --add-textfile <path> <name>`.

## Candidate key texts

Cicada 3301 is documented to have used specific literary/esoteric works as
book-cipher keys (see `cicada-3301-background.md` §4). These are the highest-
prior candidates for a running key on the unsolved *Liber Primus*:

| File | Work | Cicada link | Source | Runes cached |
| --- | --- | --- | --- | --- |
| `liber_al_vel_legis.txt` | Crowley, *Liber AL vel Legis* (The Book of the Law) | **2013 book-cipher key** (strongest prior) | sacred-texts.com/oto/engccxx.htm (via firecrawl) | 22,045 |
| `mabinogion.txt` | *The Mabinogion* (Guest translation) | **2012 book-cipher key** | Project Gutenberg #5160 | 425,501 |
| `blake_marriage_of_heaven_and_hell.txt` | Blake, *The Marriage of Heaven and Hell* | heavily referenced 2012 | Project Gutenberg #45315 | 33,195 |
| `kjv_gutenberg.txt` | *King James Bible* | community heuristic; the §6 candidate | Project Gutenberg #10 | 3,007,380 |

`liber_al_vel_legis_source.md` is the raw firecrawl markdown; the `.txt` is that
with markdown link/image syntax and bare URLs stripped, before transliteration.

**KJV restored 2026-08-22.** The §31 audit found §6 was not reproducible: its
`keytext_cache/kjv.u8` is gitignored and was absent, so the KJV run could not be
repeated or extended (e.g. reversed). Rebuilt from Project Gutenberg #10 via
`python3 keytexts.py --add-textfile download/kjv_gutenberg.txt kjv`. Honest
caveat: this edition yields **3,007,380** runes where the original §6 run reports
~3.16M, so §6's exact numbers are NOT byte-reproducible — a different KJV edition
or boilerplate. The attack is runnable again, which is what matters.

Rune counts are after ASCII-folding (Æ→AE, accents dropped) and Gematria Primus
transliteration. Project Gutenberg boilerplate is left in the Mabinogion/Blake
files; being ordinary English it adds only harmless key material and does not
create false running-key hits.

## Transcription cross-check (not public domain — attributed)

| File | What | Source | License |
| --- | --- | --- | --- |
| `rtkd_liber_primus_transcription.txt` | An independent master transcription of the Liber Primus runes (with word/line/page delimiters and the two-char code pages) | github.com/rtkd/iddqd, `liber-primus__transcription--master/` | CC-BY-SA (community asset) |

Used by `compare_transcriptions.py` (§23/P2.4) to cross-check the vendored
scream314 stream: it establishes that the 86 unsolved doublets are reproduced by
an independent transcription (i.e. real, not copy noise). Unmodified from source.

## Research

`cicada-3301-background.md` — briefing on the history of Cicada 3301, the runes
and Gematria Primus, the documented cipher schemes, and the candidate key-text
list (canonical copy lives at `../docs/cicada-3301-background.md`). Sources are
cited inline.

## Not included (couldn't obtain a clean public-domain copy here)

- **Gibson, *Agrippa (A Book of the Dead)*** — 2012 QR-poster poem, but **not**
  public domain (living author), so it is not vendored.
- **Emerson, *Self-Reliance*** and the **Old English Rune Poem** — reachable at
  wikisource if wanted as further candidates.
