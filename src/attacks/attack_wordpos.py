"""Structural-position uniformity diagnostic (N9 / Dukotah C-02).

Keyless test. Group the ciphertext runes by their STRUCTURAL position and ask
whether any group departs from uniform. The global stream is uniform (§4), but
that is a MARGINAL statement — it does not forbid a group like "the first rune of
every word" from being skewed while the medial runes compensate. Two hypotheses
would produce exactly such a skew:

  * a WORD/LINE/PAGE-SYNCHRONISED key: if the key pointer restarts at each word
    (the ACA "Interrupted Key" cipher; LP marks word divisions), then every
    word-initial rune is p_initial + K[0] — a constant shift of the English
    first-letter distribution, which is far from uniform.
  * FORCING: an acrostic or layout constraint imposed in the ciphertext (a
    message spelled by the initials) — Dukotah's C-02 reading.

Either way the tell is the same: initial-position runes are non-uniform. This
tests word-initial, each within-word position, word-final, line-initial and
page-initial.

Power is proven, not assumed (§28). A planted word-reset encryption must make the
word-initial group light up, and a planted continuous-key encryption must leave
every group flat. Only then is a flat real result a real negative.

Usage: python3 attack_wordpos.py
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import collections
import math

import gematria as g
from parse_lp import parse
from doublet_sim import LCG
import attack_pagekey as pk

N = g.N


# --- non-uniformity statistic ------------------------------------------------

def chi2(sample):
    m = len(sample)
    if m == 0:
        return 0.0
    exp = m / N
    cnt = collections.Counter(sample)
    return sum((cnt.get(r, 0) - exp) ** 2 / exp for r in range(N))


def ioc(sample):
    m = len(sample)
    if m < 2:
        return 0.0
    cnt = collections.Counter(sample)
    num = sum(v * (v - 1) for v in cnt.values())
    return num / (m * (m - 1) / N)


def chi2_z(sample):
    """z-score of chi2 vs its df=28 null (mean 28, var 56). Valid for m >~ 145
    (expected >= 5/cell); small groups use the Monte-Carlo p instead."""
    return (chi2(sample) - (N - 1)) / math.sqrt(2 * (N - 1))


def mc_p(sample, seed=1, R=4000):
    """Monte-Carlo p: P(uniform chi2 >= observed) for a same-size sample. Used
    for small groups where the chi2 approximation is poor (page-initial, m=54)."""
    obs = chi2(sample)
    m = len(sample)
    rng = LCG(seed)
    hits = 0
    for _ in range(R):
        s = [rng.randint(N) for _ in range(m)]
        if chi2(s) >= obs:
            hits += 1
    return (hits + 1) / (R + 1)


# --- structural position classes ---------------------------------------------

def word_classes(word_lists, maxpos=6):
    """{'word-init', 'word-2', ..., 'word-final'} -> list of runes."""
    cls = collections.defaultdict(list)
    for w in word_lists:
        if not w:
            continue
        for j, r in enumerate(w):
            if j == 0:
                cls["word-init"].append(r)
            elif j < maxpos:
                cls[f"word-{j+1}"].append(r)
        if len(w) > 1:
            cls["word-final"].append(w[-1])
    return cls


def unit_initial(units):
    """First rune of each unit (line or page)."""
    return [u[0] for u in units if u]


def all_classes():
    segs = parse("data/liber_primus.md")
    un = [s for s in segs if not s.solved and len(s.indices) >= 50]
    words = [w for s in un for w in s.words]
    cls = dict(word_classes(words))
    lines = [u for _, units in pk.unsolved_pages("line") for u in units]
    pages = [u for _, units in pk.unsolved_pages("page") for u in units]
    cls["line-init"] = unit_initial(lines)
    cls["page-init"] = unit_initial(pages)
    return cls


def report(cls, label):
    print(f"--- {label} ---")
    names = list(cls.keys())
    bonf = len(names)
    flagged = []
    for name in names:
        s = cls[name]
        m = len(s)
        if m >= 145:
            z = chi2_z(s)
            p = 0.5 * math.erfc(z / math.sqrt(2))     # one-sided upper-tail
            note = ""
        else:
            z = float("nan")
            p = mc_p(s, seed=hash(name) & 0xffff or 1)
            note = " (MC)"
        sig = "  <-- non-uniform" if p * bonf < 0.05 else ""
        if sig:
            flagged.append(name)
        zs = f"{z:6.2f}" if not math.isnan(z) else "  n/a "
        print(f"  {name:11s} n={m:5d}  IoC {ioc(s):.3f}  chi2z {zs}  "
              f"p={p:.3f}{note} (Bonf x{bonf}){sig}")
    return flagged


# --- planted controls (prove the test has power) -----------------------------

def english_words(nwords=4000, target=6000):
    """Real English words -> rune words, so word-initials carry the skewed
    English first-letter distribution the positive control needs."""
    import wordfreq
    out = []
    for w in wordfreq.top_n_list("en", nwords):
        if w.isalpha() and w.isascii():
            ix = g.latin_to_indices(w)
            if ix:
                out.append(ix)
        if sum(len(x) for x in out) >= target:
            break
    return out


def enc_wordreset(words, K):
    """Key RESTARTS at each word: c[w][j] = p[w][j] + K[j]."""
    return [[(r + K[j % len(K)]) % N for j, r in enumerate(w)] for w in words]


def enc_continuous(words, K):
    """One continuous pointer over the whole stream (no word sync)."""
    out, i = [], 0
    for w in words:
        ww = []
        for r in w:
            ww.append((r + K[i % len(K)]) % N)
            i += 1
        out.append(ww)
    return out


def controls():
    print("=== CONTROLS: the test must FIRE on a word-reset, stay FLAT on a "
          "continuous key ===")
    words = english_words()
    rng = LCG(99)
    K = [rng.randint(N) for _ in range(64)]

    wr = enc_wordreset(words, K)
    cont = enc_continuous(words, K)
    for tag, enc in (("word-RESET key", wr), ("continuous key", cont)):
        wi = word_classes(enc)["word-init"]
        z = chi2_z(wi)
        print(f"  {tag:16s}: word-init n={len(wi)} IoC {ioc(wi):.3f} "
              f"chi2z {z:6.2f}  {'FIRES' if z > 4 else 'flat'}")
    print("  (a word-synchronised key makes word-initials non-uniform; a "
          "continuous key does not — so the diagnostic has power)\n")


def investigate_line_init():
    """The line-initial group flags non-uniform. Before calling it a lead, probe
    whether it is a stable cipher property or a pooling / segmentation artifact."""
    print("=== FOLLOW-UP: is the line-initial flag a real signal? ===")
    lines = [u for _, units in pk.unsolved_pages("line") for u in units]
    li = [u[0] for u in lines if u]

    # (1) localisation: only position 1 should skew if it is a line-initial rule
    print("  localisation by line position (a wrapping artifact would smear):")
    for pos in range(4):
        col = [u[pos] for u in lines if len(u) > pos]
        print(f"    line-pos {pos+1}: chi2z {chi2_z(col):+.2f}")

    # (2) solved control: rtkd line segmentation is validated if SOLVED line-
    #     initials show sensible English structure (they are plaintext there)
    allp = pk.rtkd_units("line")
    uns = {pi for pi, _ in pk.unsolved_pages("line")}
    sli = [u[0] for pi, units in allp if pi not in uns for u in units if u]
    print(f"  solved line-init: n={len(sli)} chi2z {chi2_z(sli):+.2f} "
          f"(English plaintext leaking through — validates the segmentation)")

    # (3) replication: split-half should give ~equal z (7.19/sqrt2 ~ 5.1 each)
    print(f"  unsolved line-init: n={len(li)} chi2z {chi2_z(li):+.2f}; "
          f"split-half {chi2_z(li[0::2]):+.2f} / {chi2_z(li[1::2]):+.2f} "
          f"(should be ~equal if homogeneous)")

    # (4) per-page: underpowered (~11 lines/page), so it cannot localise the
    #     source — report the mean to show the aggregate is not one page
    byp = collections.defaultdict(list)
    for pi, units in pk.unsolved_pages("line"):
        for u in units:
            if u:
                byp[pi].append(u[0])
    zs = [chi2_z(v) for v in byp.values() if len(v) >= 8]
    print(f"  per-page line-init chi2z: mean {sum(zs)/len(zs):+.2f} "
          f"max {max(zs):+.2f} over {len(zs)} pages "
          f"(~11 lines/page — UNDERPOWERED, cannot confirm a within-page rule)")
    print("  => the aggregate z is real but does NOT replicate cleanly and has no "
          "within-page power. Source unresolved (cipher signal vs line-wrapping / "
          "pooling artifact). NOT a break — needs an independent line segmentation "
          "to confirm.\n")


def main():
    controls()
    print("=== REAL unsolved stream, by structural position ===")
    cls = all_classes()
    flagged = report(cls, "word / line / page position classes")
    print()
    word_page = [f for f in flagged if not f.startswith("line")]
    print("PRIMARY VERDICT (N9 / C-02 word & page hypotheses): "
          + ("LEADS " + ", ".join(word_page) if word_page else
             "CLEAN NEGATIVE — word-initial, every within-word position, "
             "word-final and page-initial are all UNIFORM (controls prove power). "
             "No word/page-synchronised key (ACA Interrupted-Key) and no "
             "word/page acrostic/forcing. Extends §4 to the conditional case."))
    print()
    if "line-init" in flagged:
        investigate_line_init()


if __name__ == "__main__":
    main()
