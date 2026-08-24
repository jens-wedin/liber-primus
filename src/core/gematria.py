"""Gematria Primus — the rune/letter/prime table used throughout Cicada 3301's
Liber Primus. 29 runes (Anglo-Saxon futhorc order), each mapped to a letter
value and a prime number.

Index order is the canonical one used by the community:
F U TH O R C G W H N I J EO P X S T B E M L NG OE D A AE Y IA EA
"""

RUNES = [
    ("ᚠ", "F", 2),
    ("ᚢ", "U", 3),
    ("ᚦ", "TH", 5),
    ("ᚩ", "O", 7),
    ("ᚱ", "R", 11),
    ("ᚳ", "C", 13),
    ("ᚷ", "G", 17),
    ("ᚹ", "W", 19),
    ("ᚻ", "H", 23),
    ("ᚾ", "N", 29),
    ("ᛁ", "I", 31),
    ("ᛄ", "J", 37),
    ("ᛇ", "EO", 41),
    ("ᛈ", "P", 43),
    ("ᛉ", "X", 47),
    ("ᛋ", "S", 53),
    ("ᛏ", "T", 59),
    ("ᛒ", "B", 61),
    ("ᛖ", "E", 67),
    ("ᛗ", "M", 71),
    ("ᛚ", "L", 73),
    ("ᛝ", "NG", 79),
    ("ᛟ", "OE", 83),
    ("ᛞ", "D", 89),
    ("ᚪ", "A", 97),
    ("ᚫ", "AE", 101),
    ("ᚣ", "Y", 103),
    ("ᛡ", "IA", 107),
    ("ᛠ", "EA", 109),
]

N = len(RUNES)  # 29

RUNE_TO_IDX = {r: i for i, (r, _, _) in enumerate(RUNES)}
IDX_TO_RUNE = [r for r, _, _ in RUNES]
IDX_TO_LETTER = [l for _, l, _ in RUNES]
IDX_TO_PRIME = [p for _, _, p in RUNES]

# Letter-sequence -> index, longest-first so TH/NG/EA/... win over T/N/E.
LETTER_TO_IDX = {l: i for i, (_, l, _) in enumerate(RUNES)}
# Common aliases used in plaintexts
LETTER_TO_IDX.update({"K": 5, "V": 1, "Z": 15, "Q": 5, "ING": 21, "IO": 27})

RUNE_SET = set(RUNE_TO_IDX)


def runes_to_indices(text):
    """Extract the rune stream (list of 0..28 indices), dropping punctuation."""
    return [RUNE_TO_IDX[ch] for ch in text if ch in RUNE_SET]


def runes_to_words(text):
    """Split rune text into words (lists of indices). Word separators are
    anything that isn't a rune, except that a bare newline inside a line-wrap
    still separates. • and whitespace both count as separators."""
    words, cur = [], []
    for ch in text:
        if ch in RUNE_SET:
            cur.append(RUNE_TO_IDX[ch])
        else:
            if cur:
                words.append(cur)
                cur = []
    if cur:
        words.append(cur)
    return words


def indices_to_latin(indices, sep=""):
    return sep.join(IDX_TO_LETTER[i] for i in indices)


def words_to_latin(words):
    return " ".join(indices_to_latin(w) for w in words)


def latin_to_indices(s):
    """Greedy longest-match transliteration of A-Z text into rune indices."""
    s = "".join(c for c in s.upper() if c.isalpha())
    out, i = [], 0
    multi = ("ING", "TH", "NG", "OE", "AE", "IA", "IO", "EO", "EA")
    while i < len(s):
        matched = False
        for m in multi:
            if s.startswith(m, i):
                out.append(LETTER_TO_IDX[m])
                i += len(m)
                matched = True
                break
        if not matched:
            out.append(LETTER_TO_IDX[s[i]])
            i += 1
    return out


def latin_text_to_indices(text):
    """Transliterate a multi-word text word by word, so digraphs (EA, TH, ...)
    never form across word boundaries."""
    out = []
    for w in text.split():
        out.extend(latin_to_indices(w))
    return out
