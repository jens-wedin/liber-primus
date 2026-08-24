"""N-gram language model over Gematria Primus rune indices.

The bigram model used earlier was trained on ~1,875 runes of solved plaintext
— far too little for trigrams (29^3 ~ 24k cells). This builds a proper model

from a large English base: the `wordfreq` 50k-word English frequency list,
each word transliterated to rune indices with Cicada's conventions and its
n-grams counted *weighted by the word's frequency*. Word-frequency weighting
gives realistic letter statistics without needing a running-text corpus.

Scoring uses Stupid Backoff (Brants et al. 2007): if an n-gram is unseen,
back off to the (n-1)-gram times a fixed penalty. It is not normalised to a
true probability, but it ranks candidates well and is cheap and robust —
exactly what a beam search needs.

Cache: the counts are built once and pickled to model_cache/ so downstream
attacks start instantly.
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import math
import os
import pickle

import gematria as g

N = g.N
CACHE_DIR = os.path.join(os.path.dirname(__file__), "model_cache")
BACKOFF = 0.4  # Stupid Backoff discount


def _iter_english_words(n_words):
    import wordfreq
    for w in wordfreq.top_n_list("en", n_words):
        if w.isalpha() and w.isascii():
            yield w, wordfreq.word_frequency(w, "en")


def build_counts(order=3, n_words=50000):
    """Return {k: Counter-like dict} for k=1..order over rune indices,
    frequency-weighted. Boundaries are not modeled (Cicada • separators mean
    within-word n-grams dominate); each word is scored in isolation."""
    from collections import defaultdict
    counts = [defaultdict(float) for _ in range(order + 1)]
    for word, freq in _iter_english_words(n_words):
        ix = g.latin_to_indices(word)
        w = freq * 1e6  # scale so counts are comfortably > 1
        for k in range(1, order + 1):
            for i in range(len(ix) - k + 1):
                counts[k][tuple(ix[i:i + k])] += w
    return [dict(c) for c in counts]


class NGramModel:
    def __init__(self, counts, order):
        self.counts = counts
        self.order = order
        self.total = sum(counts[1].values())
        # precompute context totals for the top order via bigram/unigram sums
        self._uni_logfloor = math.log(0.5 / self.total)

    def logscore_next(self, context, nxt):
        """Stupid-Backoff log-score of `nxt` (index) given a context tuple
        (most recent last). Uses up to order-1 context runes."""
        ctx = tuple(context[-(self.order - 1):]) if self.order > 1 else ()
        penalty = 0.0
        while True:
            k = len(ctx) + 1
            gram = ctx + (nxt,)
            num = self.counts[k].get(gram, 0.0)
            if num > 0:
                if k == 1:
                    return penalty + math.log(num / self.total)
                den = self.counts[k - 1].get(ctx, 0.0)
                if den > 0:
                    return penalty + math.log(num / den)
            # back off
            if not ctx:
                return penalty + self._uni_logfloor
            ctx = ctx[1:]
            penalty += math.log(BACKOFF)

    def score_sequence(self, ix):
        if len(ix) < 2:
            return 0.0
        s = 0.0
        for i in range(1, len(ix)):
            s += self.logscore_next(ix[:i], ix[i])
        return s / (len(ix) - 1)


def get_model(order=3, n_words=50000):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"ngram_o{order}_w{n_words}.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            counts = pickle.load(f)
    else:
        counts = build_counts(order, n_words)
        with open(path, "wb") as f:
            pickle.dump(counts, f)
    return NGramModel(counts, order)


if __name__ == "__main__":
    # Discrimination test: how well does each order separate real English
    # from uniform-random rune text? Higher gap = more attack power.
    import statistics
    from parse_lp import parse
    from doublet_sim import english_plaintext, LCG

    segs = parse("data/liber_primus.md")
    real = english_plaintext(segs)
    rng = LCG(42)
    rand = [rng.randint(N) for _ in range(len(real))]

    print("order  English-score  random-score  separation")
    for order in (2, 3, 4):
        m = get_model(order)
        # score in windows to get a stable mean
        def windows(seq, w=60):
            return [seq[i:i + w] for i in range(0, len(seq) - w, w)]
        er = statistics.mean(m.score_sequence(x) for x in windows(real))
        rr = statistics.mean(m.score_sequence(x) for x in windows(rand))
        print(f"  {order}     {er:8.3f}      {rr:8.3f}     {er - rr:6.3f}")
    print("\n(bigram separation was ~0.9; trigram/4-gram should be larger, "
          "which is the power gain the running-key test needed.)")
