"""Candidate-key attacks on the unsolved segments.

The doublet signature rejects a *plain* running key (it would leave 3.45%
doublets, not 0.66%), so any running key must be combined with the no-repeat
enforcement. Two principled, now well-powered (trigram) tests:

PART A — self-referential running keys via key-skip.
  Cicada has form for self-reference. Feed the key-skip beam decoder
  (attack_keyskip) candidate key STREAMS drawn from the corpus itself:
  the solved-pages plaintext, and each unsolved segment's own runes. If any
  page is enciphered with a running key taken from Cicada's own text, the
  beam recovers English.

PART B — key-word crib (running-key, no desync assumed inside a short window).
  For a running key, BOTH plaintext and key are English. Slide common English
  words as candidate KEY fragments over each segment; decode p = c - k; keep
  placements where the resulting PLAINTEXT fragment scores strongly English
  on the trigram model AND contains a dictionary word. A short key word can
  align even under occasional no-repeat skips (if none lands in the window).
  Exhaustive over key words × offsets; coverage is reported honestly.

Usage: python3 attack_keycrib.py [--order 3] [--part A|B|both]
       [--keywords 600] [--head 150]
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import argparse
import math

import ciphers as c
import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG

N = g.N


# ---- Part A: self-referential running keys via key-skip ---------------------

def part_a(segs, model, head, beam, max_skip):
    from attack_keyskip import beam_decode
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]

    # candidate key streams, tagged with a source id so a page is never
    # keyed by its own runes (p = c - c = all F, a degenerate artifact).
    keys = {"solved-plaintext": (None, english_plaintext(segs))}
    for s in unsolved:
        keys[f"runes:{s.section[:18]}"] = (s.section, list(s.indices))

    eng_ref = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(5)
    rand_ref = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"PART A — self-referential running key via key-skip")
    print(f"  refs: English {eng_ref:.2f}, random {rand_ref:.2f}\n")

    best_global = None
    for s in unsolved:
        ix = s.indices[:head]
        best = None
        for kname, (ksrc, K) in keys.items():
            if ksrc == s.section:
                continue  # a page keyed by its own runes is degenerate
            Kx = (K + K)[:len(ix) * (max_skip + 1) + 64]
            if len(Kx) < len(ix) * (max_skip + 1) + 4:
                Kx = (Kx * 3)[:len(ix) * (max_skip + 1) + 64]
            for sign in (-1, +1):
                sc, dec = beam_decode(ix, Kx, 0, sign, model, beam, max_skip)
                bl = sc / max(1, len(ix) - 1)
                if best is None or bl > best[0]:
                    best = (bl, kname, sign, dec)
        bl, kname, sign, dec = best
        latin = g.indices_to_latin(dec)
        print(f"  {s.section[:40]:40s} best key={kname} "
              f"{'+' if sign>0 else '-'} score {bl:.2f}")
        print(f"      {latin[:96]}")
        if best_global is None or bl > best_global[0]:
            best_global = (bl, s.section, kname)
    print(f"\n  best A: score {best_global[0]:.2f} on {best_global[1][:30]} "
          f"(key {best_global[2]}); English ~{eng_ref:.2f}\n")


# ---- Part B: key-word crib --------------------------------------------------

def load_key_words(n, min_len, max_len):
    import wordfreq
    out = []
    for w in wordfreq.top_n_list("en", n * 4):
        if not (w.isalpha() and w.isascii()):
            continue
        ix = g.latin_to_indices(w)
        if min_len <= len(ix) <= max_len:
            out.append((w.upper(), ix))
        if len(out) >= n:
            break
    return out


DICT = {w for w in [
    "THE", "AND", "THAT", "WITH", "YOUR", "THIS", "FOR", "ARE", "YOU", "NOT",
    "ALL", "WITHIN", "SHALL", "FROM", "THEY", "HAVE", "WHICH", "THERE", "THEIR",
    "WILL", "TRUTH", "SACRED", "PRIME", "DIVINITY", "INSTAR", "EMERGE", "SELF",
    "KNOW", "FIND", "PILGRIM", "JOURNEY", "CIRCUMFERENCE", "WISDOM", "MASTER",
    "STUDENT", "REALITY", "COMMAND", "DISCOVER", "PRESERVE", "ADHERE",
]}


def has_dict_word(latin):
    return any(w in latin for w in DICT)


def trigram_window_score(model, p):
    return model.score_sequence(p)


def part_b(segs, model, n_keywords):
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]
    keywords = load_key_words(n_keywords, 6, 10)

    # calibrate a threshold: score short genuine-English vs random windows
    pt = english_plaintext(segs)
    eng = [model.score_sequence(pt[i:i + 8]) for i in range(0, len(pt) - 8, 8)]
    eng.sort()
    thresh = eng[len(eng) // 10]  # 10th percentile of real English windows
    print(f"PART B — key-word crib ({len(keywords)} key words, len 6-10)")
    print(f"  threshold = {thresh:.2f} (10th pct of genuine English windows)\n")

    hits = []
    placements = 0
    for s in unsolved:
        ix = s.indices
        for kw, k in keywords:
            L = len(k)
            for o in range(len(ix) - L + 1):
                placements += 1
                p = [(ix[o + i] - k[i]) % N for i in range(L)]
                sc = trigram_window_score(model, p)
                if sc > thresh:
                    latin = g.indices_to_latin(p)
                    if has_dict_word(latin):
                        hits.append((sc, s.section[:26], o, kw, latin))
    hits.sort(reverse=True)
    print(f"  examined {placements:,} placements; "
          f"{len(hits)} passed English+dictionary filter")
    for sc, sec, o, kw, latin in hits[:25]:
        print(f"    score {sc:.2f}  key '{kw}' @ {sec} off {o}: PLAINTEXT {latin}")
    if not hits:
        print("    (none — no key word yields an English plaintext fragment)")
    print("\n  NOTE: a genuine running-key hit shows a *contiguous* real word "
          "in the plaintext AND the key word being real; scattered near-misses "
          "at this length are expected false positives, not a solution.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--part", choices=["A", "B", "both"], default="both")
    ap.add_argument("--keywords", type=int, default=600)
    ap.add_argument("--head", type=int, default=150)
    ap.add_argument("--beam", type=int, default=200)
    ap.add_argument("--max-skip", type=int, default=2)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(args.order)

    if args.part in ("A", "both"):
        part_a(segs, model, args.head, args.beam, args.max_skip)
    if args.part in ("B", "both"):
        part_b(segs, model, args.keywords)


if __name__ == "__main__":
    main()
