# Cicada 3301 & *Liber Primus* — Cryptanalysis Background Briefing

> **Purpose.** Background research for a cryptanalysis project targeting the unsolved runic book *Liber Primus* (LP). This document collects what is *verified* about Cicada 3301's history, its runic alphabet (Gematria Primus), and every documented cipher scheme, and then — the part that feeds our running‑key attack — enumerates the external texts Cicada is documented to have referenced, with public‑domain status and directly‑downloadable URLs.
>
> **Sourcing conventions.** Claims are cited inline. I distinguish **[VERIFIED]** (multiple reputable sources agree, or it is a reproducible cryptographic fact), **[COMMUNITY]** (well‑established in the solver community / wikis but single‑sourced or secondary), and **[LEGEND/DISPUTED]** (rumor, speculation, or contested). Cicada's *own* statements are only trustworthy when carried in an OpenPGP message signed by key ID `7A35090F` — everything else, including copycats, is unverified by design.
>
> **Primary sources used:** Wikipedia (<https://en.wikipedia.org/wiki/Cicada_3301>); Uncovering Cicada wiki (<https://uncovering-cicada.fandom.com>); CicadaSolvers (<https://www.cicadasolvers.com>); Boxentriq guides (<https://www.boxentriq.com>); community archives `scream314/cicada3301` and `rtkd/iddqd` on GitHub. Journalistic write‑ups: The Guardian and The Daily Telegraph (cited below).

---

## 1. History of Cicada 3301

Cicada 3301 is the signature attached to **three sets of public cryptographic puzzles posted in 2012, 2013, and 2014**, each beginning on/around **January 4** of its year, plus a small number of later signed messages. The stated intent was to *"recruit intelligent individuals."* The identity and purpose of the group remain unverified. [VERIFIED — <https://en.wikipedia.org/wiki/Cicada_3301>]

### Timeline

| When | Event | Status |
|---|---|---|
| **4 Jan 2012** (image widely seen **5 Jan**) | First puzzle posted to 4chan's /x/ (Paranormal) board. A JPEG with the text *"We are looking for highly intelligent individuals. To find them, we have devised a test."* | [VERIFIED] Date discrepancy: Wikipedia says posting began Jan 4; Boxentriq's walkthrough shows the image dated Jan 5 (timezone/thread‑bump ambiguity). <https://en.wikipedia.org/wiki/Cicada_3301>, <https://www.boxentriq.com/guides/cicada-3301-first-puzzle-walkthrough> |
| Jan 2012 | Puzzle 1 chain (see below): OutGuess steganography → Caesar cipher → Reddit → **book ciphers** (Mabinogion/Bulfinch; William Gibson's *Agrippa*) → prime‑number image clue → a **phone number** → `845145127.com` → **physical QR‑code posters in ~14 cities across several countries** → a Tor hidden service that asked solvers to submit email addresses. | [VERIFIED/COMMUNITY] |
| ~9 Jan 2012 (end) | Those who reached the end got a message that Cicada had *"found the individuals we sought"*; the onion closed. A few recruits later spoke publicly (see "Recruitment vs. hoax"). | [COMMUNITY] |
| **4 Jan 2013** | Second round begins with a new image (`232.jpg`), now **PGP‑signed** — introducing signature verification as the anti‑hoax mechanism. | [VERIFIED — <https://en.wikipedia.org/wiki/Cicada_3301>] |
| 2013 | Puzzle 2 chain: steganography → a **book cipher keyed to Aleister Crowley's *Liber AL vel Legis* (The Book of the Law)** (references of the form chapter\:line\:word) → an MP3, **"The Instar Emergence" (`761.mp3`)** → XOR of the 2013 Twitter data with the MP3 yields the **Gematria Primus** rune table → a bootable **"CicadaOS" Linux image** → telephone numbers / onion services. | [COMMUNITY — <https://uncovering-cicada.fandom.com/wiki/Gematria_Primus>, <https://uncovering-cicada.fandom.com/wiki/What_Happened_Part_1_(2013)>] |
| **4–5 Jan 2014** | Third round announced via Twitter. It leads relatively quickly to the **Liber Primus**, a codex written entirely in Gematria Primus runes. | [VERIFIED — <https://en.wikipedia.org/wiki/Cicada_3301>] |
| **May 2014** | Cicada releases a file dump containing the Liber Primus pages as JPEGs (the LP2 pages carry consecutive numeric names defined in this dump). | [COMMUNITY — <https://www.cicadasolvers.com/quickstart/>] |
| **4 Jan 2015** | **No new puzzle.** | [VERIFIED] |
| **2015 / 5 Jan 2016** | Later Twitter messages posted. The **6 Jan 2016 "Liber Primus is the way"** message encodes a prime/Fibonacci algorithm (Fibonacci terms subtracted cumulatively from 464 — 3301's prime index — then used as a prime index). | [COMMUNITY — <https://www.cicadasolvers.com/quickstart/>] |
| **~29 Apr 2017** | **Last verified OpenPGP‑signed message:** *"Beware false paths. Always verify PGP signature from 7A35090F. 3301."* Nothing verified since. | [VERIFIED — <https://en.wikipedia.org/wiki/Cicada_3301>, <https://www.boxentriq.com/guides/cicada-3301-first-puzzle-walkthrough>] |

### What each round involved (mechanics)

- **2012:** classical/CTF crypto and steganography (OutGuess, Caesar), **book ciphers** into public‑domain literature, prime‑number trivia (the source image is 509×503 px — both prime — and 509 × 503 × 3301 = 845145127 → a `.com`), a recorded **phone message**, worldwide **physical QR posters**, and a Tor recruitment site. A MIDI "musical cryptogram" also appears in this chain. [VERIFIED — <https://www.boxentriq.com/guides/cicada-3301-first-puzzle-walkthrough>]
- **2013:** everything above **plus** PGP‑signed comms, a Crowley book cipher, the "The Instar Emergence" MP3, the **birth of Gematria Primus**, and a custom Linux distro. [COMMUNITY]
- **2014 →:** the **Liber Primus** itself — a ~74/75‑page runic book. Only a preface set was ever solved; the bulk remains unsolved. Wikipedia flatly states *"the third puzzle remains unsolved."* [VERIFIED]

### Recruitment vs. hoax — theories

- **Stated purpose:** recruiting "intelligent individuals." [VERIFIED — Cicada's own text]
- **Speculation** (none confirmed): NSA/CIA/FBI/MI6/GCHQ recruiting tool; a cypherpunk collective or "secret society"; a privacy/anonymity software group; a cult; an alternate‑reality game (ARG); marketing; or an elaborate hoax. Boxentriq and Wikipedia both catalog these as *unconfirmed*. [LEGEND/DISPUTED — <https://www.boxentriq.com/guides/cicada-3301-first-puzzle-walkthrough>]
- **Recruit testimony:** A handful of solvers have said publicly that after finishing 2012 they were emailed and asked to collaborate on **privacy/anonymity software**, then contact went quiet; the best‑known named account is Marcus Wanner (covered by Rolling Stone and others). These are individual testimonies, not Cicada‑signed statements. [COMMUNITY/DISPUTED — see The Guardian, Alex Hern, *"Cicada 3301: I tried the hardest puzzle on the internet and failed spectacularly,"* 10 Jan 2014, <https://www.theguardian.com/technology/2014/jan/10/cicada-3301-i-tried-the-hardest-puzzle-on-the-internet-and-failed-spectacularly>]
- **Anti‑hoax rule:** From 2013 on, only content in an OpenPGP message signed by Cicada's key is authentic; the 2017 message exists precisely to disown copycats and "false paths." [VERIFIED]
- **First solver / press:** Michael Grothaus, *"Meet The Man Who Solved The Mysterious Cicada 3301 Puzzle"* (Fast Company, 25 Nov 2014, <https://www.fastcompany.com/3025785/meet-the-man-who-solved-the-mysterious-cicada-3301-puzzle>); The Daily Telegraph, *"The internet mystery that has the world baffled"* (2013).

### Current status

- **Liber Primus is mostly unsolved.** Modern solver summaries split it into **LP1 (17 pages, all solved)** and **LP2 (58 pages, only 2 solved — `56.jpg` and `57.jpg` — leaving 56 unsolved).** [VERIFIED/COMMUNITY — <https://www.cicadasolvers.com/quickstart/>]
- No verified Cicada activity since April 2017. Winners of the three rounds have never publicly disclosed what they found. [VERIFIED]
- **Legacy:** the US Navy's 2014 recruitment challenge "Project Architeuthis"; the *Person of Interest* episode "Nautilus" (2014); the film *Dark Web: Cicada 3301* (2021). [VERIFIED — <https://en.wikipedia.org/wiki/Cicada_3301>]

---

## 2. The Runes & Gematria Primus

### The alphabet

The Liber Primus is written in runes drawn from the **Anglo‑Saxon futhorc**, encoded via **Gematria Primus**, a **29‑rune alphabet** where each rune maps to (a) an English letter or digraph and (b) a **prime number**, the primes running in ascending order (2, 3, 5, …, 109). [VERIFIED — <https://uncovering-cicada.fandom.com/wiki/Gematria_Primus>]

Gematria Primus is *nearly identical to the Old English rune poem's* futhorc ordering; the community view is that 3301 took a real, prime‑length (29‑letter) historical alphabet and grafted a prime‑number gematria onto it. [COMMUNITY — <https://uncovering-cicada.fandom.com/wiki/Gematria_Primus>; cf. <https://en.wikipedia.org/wiki/Old_English_rune_poem>]

**Relation to historical runic alphabets:**
- **Elder Futhark** (~2nd–8th c.): 24 runes — the common ancestor.
- **Anglo‑Saxon futhorc** (~5th–11th c., England/Frisia): an *expanded* Elder Futhark of ~29–33 runes, adding letters for the sounds of Old English (e.g. *os*, *ac*, *æsc*, *yr*, *ear*, *ior*). Gematria Primus is a 29‑rune selection from this futhorc.
- **Younger Futhark** (Scandinavia): 16 runes — *not* the basis here.

Each futhorc rune historically carries a **name/meaning** from the rune poems — e.g. ᚠ *feoh* = wealth/cattle, ᚢ *ur* = aurochs, ᚦ *thorn* = thorn, ᚩ *os* = god/mouth, ᚱ *rad* = riding, ᚳ *cen* = torch, ᚷ *gyfu* = gift, ᚹ *wynn* = joy, and so on. Cicada leans on these connotations thematically (e.g. *feoh*/wealth in "Amass great wealth… never become attached to what you own").

### Gematria Primus table (29 runes) [VERIFIED]

Sourced from the Uncovering Cicada wiki and Boxentriq (identical). "Decimal value" is the 0–28 index used for modular arithmetic; "Prime value" is the gematria weight.

| # | Rune | Latin value | Decimal (0–28) | Prime |
|---|------|-------------|----------------|-------|
| 1 | ᚠ | F | 0 | 2 |
| 2 | ᚢ | U / V | 1 | 3 |
| 3 | ᚦ | TH | 2 | 5 |
| 4 | ᚩ | O | 3 | 7 |
| 5 | ᚱ | R | 4 | 11 |
| 6 | ᚳ | C / K | 5 | 13 |
| 7 | ᚷ | G | 6 | 17 |
| 8 | ᚹ | W | 7 | 19 |
| 9 | ᚻ | H | 8 | 23 |
| 10 | ᚾ | N | 9 | 29 |
| 11 | ᛁ | I | 10 | 31 |
| 12 | ᛄ | J | 11 | 37 |
| 13 | ᛇ | EO | 12 | 41 |
| 14 | ᛈ | P | 13 | 43 |
| 15 | ᛉ | X | 14 | 47 |
| 16 | ᛋ | S / Z | 15 | 53 |
| 17 | ᛏ | T | 16 | 59 |
| 18 | ᛒ | B | 17 | 61 |
| 19 | ᛖ | E | 18 | 67 |
| 20 | ᛗ | M | 19 | 71 |
| 21 | ᛚ | L | 20 | 73 |
| 22 | ᛝ | NG / ING | 21 | 79 |
| 23 | ᛟ | OE | 22 | 83 |
| 24 | ᛞ | D | 23 | 89 |
| 25 | ᚪ | A | 24 | 97 |
| 26 | ᚫ | AE | 25 | 101 |
| 27 | ᚣ | Y | 26 | 103 |
| 28 | ᛡ | IA / IO | 27 | 107 |
| 29 | ᛠ | EA | 28 | 109 |

Sources: <https://uncovering-cicada.fandom.com/wiki/How_the_solved_pages_of_the_Liber_Primus_were_solved>, <https://www.boxentriq.com/guides/cicada-3301-liber-primus>.

**Consequences for cryptanalysis:**
- Some runes are **digraphs** (TH, EO, NG, OE, AE, IA, EA) and one letter can have ambiguous transcription (e.g. NG vs. ING, IA vs. IO) — a known source of transcription error. The canonical transcription is rtkd's: <https://raw.githubusercontent.com/rtkd/iddqd/master/liber-primus__transcription--master/liber-primus__transcription--master.txt>.
- Decoded plaintext is **"Runeglish"** — English spelled with only these 29 tokens, so U/V collapse (V for U), C/K collapse (C for K), and Q/K→C substitutions appear (e.g. `COAN` = koan, `CNOW` = know, `SEEC` = seek).

### Gematria / isopsephy

Because each rune has a prime value, any word has a **gematria sum**. Cicada uses this as a signature/consistency device: [COMMUNITY — <https://uncovering-cicada.fandom.com/wiki/Gematria_Primus>]
- **"The Instar Emergence" = 761** — mirrored in the MP3 filename `761.mp3` and its 167‑second length.
- **"Patience is a virtue" = 761.**
- **3301** itself is the **464th prime** (its "prime index," 464), a number Cicada reuses in the 2016 prime/Fibonacci algorithm. [COMMUNITY — <https://www.cicadasolvers.com/quickstart/>]

> Note: solvers report the *gematria sums themselves have not yet cracked any unsolved LP page* — they function more as thematic/verification signals than as a direct key. [COMMUNITY]

---

## 3. The Cryptography

### 3a. Outer‑puzzle toolbox (2012–2013)

Every classical technique in the outer puzzles, and where it applied: [VERIFIED/COMMUNITY — <https://www.boxentriq.com/guides/cicada-3301-first-puzzle-walkthrough>]

- **Steganography — OutGuess:** hidden payloads in JPEGs (the very first step). Also **`stegdetect`/`steghide`‑style** hidden bytes and **image metadata/appended data** (binary analysis).
- **Caesar cipher:** the invitation text (shift 4; flagged by "TIBERIVS CLAVDIVS CAESAR").
- **Book ciphers:** numeric references indexing into a specific public‑domain text (see §4): the **Mabinogion / Bulfinch "The Lady of the Fountain"** (2012) and **Crowley's *Liber AL vel Legis*** (2013). References like `I:1:6` = chapter 1, line 1, 6th character.
- **Prime‑number puzzles:** image dimensions as primes; multiply to form a domain.
- **Telephony:** a recorded phone message delivering the next clue.
- **Physical steganography:** QR‑code **posters** in ~14 cities; QR payloads were passages from **Gibson's *Agrippa*** plus a book code.
- **Musical cryptogram:** a **MIDI** file whose (pitch, duration) pairs map to letters → a substitution cryptogram; and the **"The Instar Emergence" MP3** carrying data (XORed with Twitter text to reveal Gematria Primus).
- **Mayan numerals:** used as a numeric‑encoding step in the puzzle chain. [COMMUNITY]
- **Magic squares:** appear both in the outer material and inside Liber Primus (a symmetric/near‑magic numeric grid sits on the solved "An instruction" page — see below — and larger magic squares appear on later pages, where row/column sums tie into the prime/totient theme). [COMMUNITY]
- **OpenPGP:** used from 2013 on to *sign* Cicada's messages; verifying the signature (key `7A35090F`) is the only authenticity test.

### 3b. Liber Primus cipher schemes (the solved pages)

All LP arithmetic is **modulo 29** on the decimal (0–28) rune indices. The **ᚠ (F) interrupter / "F‑skip" rule** is pervasive: at certain ciphertext positions carrying the literal rune **ᚠ (F, decimal 0)**, the **key position does not advance** (the F acts as an unencrypted interrupter / null). Getting these skip indices right is essential; they are usually given explicitly per page. [VERIFIED — <https://www.boxentriq.com/guides/cicada-3301-liber-primus>, <https://uncovering-cicada.fandom.com/wiki/How_the_solved_pages_of_the_Liber_Primus_were_solved>]

**Per‑page methods for the SOLVED pages** (LP1 preface + the two solved LP2 pages). Plaintext excerpts shown as decoded "Runeglish":

| Page (name) | Method | Notes |
|---|---|---|
| **A Warning** | **Atbash** (`d[i] = 28 − d[i]`) | *"A WARNING. BELIEVE NOTHING FROM THIS BOOK EXCEPT WHAT YOU KNOW TO BE TRUE … DO NOT EDIT OR CHANGE THIS BOOK … FOR ALL IS SACRED."* |
| **Welcome** (`03/04.jpg`) | **Vigenère, key `DIVINITY`** (`ᛞᛁᚢᛁᚾᛁᛏᚣ`) + F‑skips at indices 48,74,84,132,159,160,250,421,443,465,514 | *"WELCOME PILGRIM TO THE GREAT JOURNEY TOWARD THE END OF ALL THINGS…"* The key is self‑referentially recovered from the first three (skip‑free) lines. |
| **Some Wisdom** | Direct (plain runes) | *"AMASS GREAT WEALTH. NEVER BECOME ATTACHED TO WHAT YOU OWN. BE PREPARED TO DESTROY ALL THAT YOU OWN."* |
| **Koan 1** | **Atbash, then Caesar shift +3** (`d[i] = (28 − d[i] + 3) mod 29`) | *"A KOAN. A MAN DECIDED TO GO AND STUDY WITH A MASTER…"* |
| **The Loss of Divinity** | Direct (plain runes, no cipher) | *"THE LOSS OF DIVINITY. THE CIRCUMFERENCE PRACTICES THREE BEHAVIOURS… CONSUMPTION, PRESERVATION, ADHERENCE…"* |
| **Koan 2** | **Vigenère, key `FIRFUMFERENFE`** (`ᚠᛁᚱᚠᚢᛗᚠᛖᚱᛖᚾᚠᛖ`) + F‑skips at 49,56 | *"…THE I IS THE VOICE OF THE CIRCUMFERENCE…"* (Note the key is itself F‑laden — "FIRFUMFERENFE" ≈ "circumference" written through the F‑rule.) |
| **An Instruction** | Direct + numeric grid | *"QUESTION ALL THINGS. DISCOVER TRUTH INSIDE YOURSELF. FOLLOW YOUR TRUTH. IMPOSE NOTHING ON OTHERS."* Followed by a **5×5 symmetric number square** (434 1311 312 278 966 / …) — a magic‑square‑like table. |
| **`0.jpg`–`55.jpg`** | **UNSOLVED** | The bulk of LP2. |
| **An End** (`56.jpg`) | **φ / totient keystream:** subtract `primes[i] − 1` in order, mod 29 (`d[i] = (d[i] − (p_i − 1)) mod 29`), where `φ(p)=p−1` | *"AN END. WITHIN THE DEEP WEB THERE EXISTS A PAGE THAT HASHES TO 36367763ab…2a8b4. IT IS THE DUTY OF EVERY PILGRIM TO SEEK OUT THIS PAGE."* |
| **Parable** (`57.jpg`) | Direct (plain runes) | *"PARABLE. LIKE THE INSTAR TUNNELLING TO THE SURFACE, WE MUST SHED OUR OWN CIRCUMFERENCES. FIND THE DIVINITY WITHIN AND EMERGE."* |

Source for all rows: <https://uncovering-cicada.fandom.com/wiki/How_the_solved_pages_of_the_Liber_Primus_were_solved> (cross‑checked against Boxentriq's guide). 

**Summary of confirmed LP techniques:**
1. **Atbash** (reversed Gematria: `28 − d`), sometimes composed with a **Caesar shift** (e.g. +3).
2. **Vigenère over the 29‑rune alphabet** with **rune keys** (`DIVINITY`, `FIRFUMFERENFE`), decrypt = subtract key index mod 29.
3. The **ᚠ (F) interrupter / F‑skip rule** modulating key advancement.
4. A **prime/totient keystream**: subtract `φ(pᵢ)=pᵢ−1` per position (the "An End" page).
5. **Plaintext pages** with no cipher at all ("direct translation").

### 3c. What is believed about the UNSOLVED pages

- The unsolved LP2 pages resist the above simple keys, implying **longer/aperiodic keys** — i.e. a **running key** (a long key stream drawn from a *text*), a more elaborate **prime/Fibonacci stream**, or an unknown transform. Solvers consider LP2 **the hardest puzzle of the digital age**, unsolved for over a decade, yet with statistical indications it is solvable. [COMMUNITY — <https://www.cicadasolvers.com/quickstart/>, <https://www.cicadasolvers.com/solvability/>]
- 3301 demonstrably enjoys **meshing prime and Fibonacci sequences** (2016 message; "An End" totient stream), so the **prime/Fibonacci space** is a documented attack surface. [COMMUNITY]
- The **running‑key hypothesis** motivates §4: if a natural‑language text is the key stream, it is very likely one Cicada already pointed at.

---

## 4. Candidate Running‑Key Texts  ← **most important for us**

For each text: **(a)** evidence Cicada referenced it, **(b)** public‑domain status, **(c)** a concrete, directly‑downloadable plain‑text/HTML URL. Project Gutenberg is often network‑blocked, so I prefer **archive.org / sacred‑texts.com / wikisource / hermetic.com**. URLs marked **[fetch‑verified]** were confirmed live and text‑bearing during this research.

### Tier 1 — Directly documented as *used inside a Cicada cipher*

1. **Aleister Crowley — *Liber AL vel Legis* (The Book of the Law), sub figura CCXX**
   - **(a) Evidence:** The **2013 puzzle's book cipher was keyed to this text** (references of the form *chapter\:line\:character*, e.g. `I:1:6`). Listed by Wikipedia's "See also" as *"a book used in the puzzle."* [VERIFIED — <https://en.wikipedia.org/wiki/Cicada_3301>; <https://uncovering-cicada.fandom.com/wiki/What_Happened_Part_1_(2013)>]
   - **(b) Public domain:** Crowley d. 1947 → **PD in UK/EU (life+70, since 2018)**; US status is disputed but the text is universally mirrored. Treat as freely usable for analysis.
   - **(c) Download:** **[fetch‑verified]** sacred‑texts (full 3 chapters, HTML): <https://sacred-texts.com/oto/engccxx.htm> · Wikisource: <https://en.wikisource.org/wiki/Liber_AL_vel_Legis> · scanned PDF: <https://archive.org/details/CrowleyTheBookOfTheLaw>. *(Note: hermetic.com mirrors exist but returned HTTP 403 to automated fetches — avoid for scripted download.)*

2. **The *Mabinogion* — via Thomas Bulfinch's *Mythology*, "The Lady of the Fountain"**
   - **(a) Evidence:** The **2012 book cipher decodes against Bulfinch's rendering of the Mabinogion tale "The Lady of the Fountain"** (King Arthur / Holy Grail cycle). Wikipedia "See also" lists the *Mabinogion* as *"another poem used in the puzzle."* Watch for **double spaces** in the source text — they shift book‑cipher indices. [VERIFIED — <https://www.boxentriq.com/guides/cicada-3301-first-puzzle-walkthrough>; <https://en.wikipedia.org/wiki/Cicada_3301>]
   - **(b) Public domain:** **Yes** — Lady Charlotte Guest's translation (1877) and Bulfinch (1855–63) are long PD.
   - **(c) Download:** Exact Bulfinch text used (HTML): <https://www.bartleby.com/lit-hub/king-arthur-and-his-knights-the-mabinogeon/the-lady-of-the-fountain/> · Full Mabinogion (Guest tr., chapter HTML) **[fetch‑verified index]**: <https://sacred-texts.com/neu/celt/mab/index.htm> (the tale is `mab13.htm` … verify chapter) · Bulfinch's *Mythology* (Age of Chivalry) full text: <https://sacred-texts.com/cla/bulf/> and <https://archive.org/details/bulfinchsmytholo00bulf>.

3. **Aleister Crowley** — see #1 (single most important documented cipher key text).

### Tier 2 — Documented as *referenced / quoted*, strong running‑key candidates

4. **William Blake — *The Marriage of Heaven and Hell*** (incl. "The Proverbs of Hell" and "A Song of Liberty," plate 27)
   - **(a) Evidence:** Repeatedly cited across the 2012 puzzle; community sources tie clues to **"A Song of Liberty" (plate 27)** and to the line **"For every thing that lives is Holy."** Blake is the puzzle's signature philosophical source. [COMMUNITY — <https://en.wikipedia.org/wiki/The_Marriage_of_Heaven_and_Hell>; solver write‑ups]
   - **(b) Public domain:** **Yes** (Blake d. 1827).
   - **(c) Download:** **[fetch‑verified]** Wikisource (full text; EPUB export button): <https://en.wikisource.org/wiki/The_Marriage_of_Heaven_and_Hell> · plaintext OCR: <https://archive.org/stream/marriageofheaven00blak/marriageofheaven00blak_djvu.txt>.

5. **William Gibson — *Agrippa (A Book of the Dead)*** (the "self‑erasing" 1992 poem)
   - **(a) Evidence:** The **QR‑code posters in the 2012 puzzle carried passages from Gibson's *Agrippa***, which (via a book code) directed solvers onward. Wikipedia "See also": *"a poem used in the puzzle."* [VERIFIED/COMMUNITY — <https://en.wikipedia.org/wiki/Cicada_3301>; <https://agrippa.english.ucsb.edu/>]
   - **(b) Public domain:** **NO** — Gibson is a living author; the poem is under copyright (text is archived/mirrored for scholarship). Use with that caveat; it is short.
   - **(c) Download:** The Agrippa Files (UC Santa Barbara), transcribed poem: <https://agrippa.english.ucsb.edu/the-poem/> (category: <https://agrippa.english.ucsb.edu/category/the-book-subcategories/the-poem>) · author's page: <https://www.williamgibsonbooks.com/source/agrippa.asp>.

6. **Ralph Waldo Emerson — *Self‑Reliance*** (Essays: First Series, 1841)
   - **(a) Evidence:** Multiple secondary write‑ups state Emerson's *Self‑Reliance* was **the answer/solution to one 2012 challenge**, and its themes (self‑sufficiency, "question all things," "impose nothing on others") pervade Liber Primus. **This is secondary‑sourced — treat as plausible but not Cicada‑confirmed.** [DISPUTED/COMMUNITY]
   - **(b) Public domain:** **Yes** (Emerson d. 1882).
   - **(c) Download:** Wikisource essay: <https://en.wikisource.org/wiki/Essays:_First_Series/Self-Reliance> (landing/disambiguation **[fetch‑verified]**: <https://en.wikisource.org/wiki/Self-Reliance>) · plaintext: <https://archive.org/details/essaysfirstserie00emer>.

### Tier 3 — Community/heuristic candidates (NOT documented Cicada references)

7. **King James Bible (1611)**
   - **(a) Evidence:** **No documented Cicada citation.** It is a *community‑tested* running‑key candidate because of its length and availability, and because LP's diction is scriptural/aphoristic. **Note for our project: KJV as a running key was tested and *ruled out* in this repo (control‑validated).** [DISPUTED — heuristic only]
   - **(b) Public domain:** **Yes.**
   - **(c) Download:** sacred‑texts (by book, HTML): <https://sacred-texts.com/bib/kjv/index.htm> · plaintext whole‑Bible: <https://archive.org/details/kingjamesbible_202007> (Gutenberg #10 exists but is frequently network‑blocked).

8. **The Old English Rune Poem** (basis of the Gematria Primus ordering)
   - **(a) Evidence:** Gematria Primus is *nearly identical* to this poem's futhorc — structurally load‑bearing, though **used as the alphabet, not (so far) as a running key.** [COMMUNITY — <https://uncovering-cicada.fandom.com/wiki/Gematria_Primus>]
   - **(b) Public domain:** **Yes.**
   - **(c) Download:** Wikisource: <https://en.wikisource.org/wiki/Anglo-Saxon_Rune_Poem> · text/translation: <https://en.wikipedia.org/wiki/Anglo-Saxon_rune_poem>.

> **Practical note for the running‑key attack.** For key material you want the **continuous letter stream** of each text (strip punctuation/spaces, fold to the 29‑token Runeglish alphabet, decide U↔V and C↔K folding up front, and try both original and reversed/Atbash‑composed streams). The **highest‑prior candidates are the ones Cicada *already used as cipher keys*** — *Liber AL vel Legis* (#1) and the *Mabinogion/Bulfinch* text (#2) — followed by Blake's *Marriage of Heaven and Hell* (#4). Emerson (#6) and KJV (#7) are lower‑prior; KJV is already excluded in this repo.

---

## 5. Open questions / uncertainties to keep flagged

- **First‑puzzle date:** Jan 4 (Wikipedia) vs. Jan 5 (image timestamp) 2012 — timezone artifact, not a real contradiction.
- **Round attribution of texts:** *Mabinogion/Bulfinch* and *Agrippa* are 2012; *Liber AL vel Legis* is the 2013 book cipher — consistent across sources, but a few popular retellings blur the rounds; trust the wikis/Boxentriq over listicles.
- **Emerson *Self‑Reliance*:** widely repeated but only secondary‑sourced as an actual puzzle solution — verify against a primary solver log before weighting it heavily.
- **Crowley copyright:** clean PD in UK/EU; US status is genuinely murky. Fine for private cryptanalysis; be careful about redistribution.
- **Recruit testimonies / "who is behind it":** entertaining but unverifiable; nothing beyond Cicada's own signed text is authoritative, and the last signed word was April 2017.
- **Page numbering:** LP1/LP2 splits and per‑page filenames differ between archives (`scream314/cicada3301` vs. the fandom vs. CicadaSolvers). Pin transcriptions to rtkd's master file to avoid off‑by‑one book‑cipher/keystream errors.

---

### Addendum 2026-08-21 — Uncovering-Cicada wiki sweep + external corroboration

Pulled via the context-mode fetcher (the fandom WAF 403s direct/datacenter
fetches) and left in the local knowledge base, searchable with `ctx_search` in
future sessions:
- Frequency Analysis Unsolved Pages: <https://uncovering-cicada.fandom.com/wiki/Frequency_Analysis_Unsolved_Pages>
- Liber Primus Unsolved Pages (page-by-page image index): <https://uncovering-cicada.fandom.com/wiki/Liber_Primus_Unsolved_Pages>
- Possible hints never used: <https://uncovering-cicada.fandom.com/wiki/Possible_hints_never_used>
- Wiki portal / hub: <https://uncovering-cicada.fandom.com/wiki/Uncovering_Cicada_Wiki>

**Independent corroboration of REPORT §4 (the main result).** The wiki's
Frequency Analysis page runs n-gram counts on the same unsolved stream and finds
it statistically indistinguishable from random: bigrams 840 unique / 12952
total-repeated (random ≈ 841 / ≈ 12955); quadgram repeats 255 (random ≈ 235,
~1σ). An independent replication of our "uniform random stream" finding.
- We verified their "840 not 841" locally: the single absent bigram is **B–B**
  (ᛒᛒ); 28/29 doublet types occur. This is *not* an extra constraint — expected
  B–B count at the 0.66% doublet rate is ~3, so drawing 0 is an ordinary ~5%
  Poisson fluctuation, fully inside the doublet-suppression story (§4/§11). Their
  count is right; reading it as a "banned bigram" is not warranted.

**Cross-check for REPORT §18 (r/cicada GP-sum finding).** The "pilgrim / SEEK
OUT / parable / instar" run is the SOLVED "AN END" page (LP2 56.jpg ≈ scream314
73.jpg), decrypted by the φ(prime) totient stream; its transliteration is "IT IS
THE DVTY OF EVERY PILGRIM TO SEEC OVT THIS PAGE" (C→K, V→U) — i.e. the "awkward
SEEK OUT phrasing" the GP-sum post flagged is just the C/V transliteration.
Confirms §18 sits on genuinely-solved plaintext.

**Additional vetted tools / transcriptions (external):**
- rtkd/iddqd — canonical LP transcription; worth diffing against the vendored
  scream314 transcription to bound the transcription-error hypothesis in §4/§11.
- mortlach/lp-decrypter — general LP decryption tool.
- 58 pages in runes (pastebin `vGMK330j`); rune-frequency web tool
  (ether8unny.shinyapps.io/cickada); CyberChef (opensource.cicada.gq).

**Untried hints (low prior; 2012–2015 artifacts, pre-LP2).** "Possible hints
never used" collects prime-indexed whitespace sequences (0,2,3,5,7,11,13,… from
a 2012 OutGuess message) and emirp-looking cookie ids (167 / 761). Thematically
adjacent to the §18 emirp/prime motif but not tied to the unsolved runic pages —
noted, not prioritised.

---

### Source index (primary)
- Wikipedia — Cicada 3301: <https://en.wikipedia.org/wiki/Cicada_3301>
- Uncovering Cicada wiki — Gematria Primus: <https://uncovering-cicada.fandom.com/wiki/Gematria_Primus>
- Uncovering Cicada wiki — How the solved pages were solved: <https://uncovering-cicada.fandom.com/wiki/How_the_solved_pages_of_the_Liber_Primus_were_solved>
- Uncovering Cicada wiki — Liber Primus: <https://uncovering-cicada.fandom.com/wiki/Liber_Primus>
- CicadaSolvers — Liber Primus Cryptanalysis Briefing (quickstart): <https://www.cicadasolvers.com/quickstart/>
- Boxentriq — First Puzzle Walkthrough: <https://www.boxentriq.com/guides/cicada-3301-first-puzzle-walkthrough>
- Boxentriq — Liber Primus Guide: <https://www.boxentriq.com/guides/cicada-3301-liber-primus>
- The Guardian (Alex Hern, 2014): <https://www.theguardian.com/technology/2014/jan/10/cicada-3301-i-tried-the-hardest-puzzle-on-the-internet-and-failed-spectacularly>
- Community archives: <https://github.com/scream314/cicada3301>, <https://github.com/rtkd/iddqd>

*Compiled 2026‑08‑20 for the Liber Primus cryptanalysis project.*
