"""Identifiability probe: can a very-short key be recovered under key-skip?

Before brute-forcing short keys (`attack_shortbrute.py`) it is worth asking
whether a short key is even *identifiable* once the doublet-avoidance key-skip
is in play. The key-skip lets the decoder choose 0..max_skip extra key
advances per position, which is a lot of freedom relative to a 2- or 3-rune
key — so many wrong short keys can be bent to look English.

This measures it directly: plant a random length-L key, encrypt English with
key-skip, then score the TRUE key and `nrand` random length-L keys through the
same key-skip beam. The true key's rank among the random ones (rank 1 = it
beats them all) is the identifiability. A rank far above 1 means a full brute
would surface chance keys, i.e. the brute is underpowered at that length.

RESULT SUPERSEDED (audit, 2026-08-21). The original run reported "rank ~6/1500 at
L=2, NOT identifiable" and REPORT §10 / CLAUDE.md concluded that short-key brute
force was intrinsically underpowered. That was a RANKING BUG, not a property of
the cipher — see `probe()`. With distinct distractors, the true key's sign-mirror
excluded and ties counted separately, short keys ARE identifiable. Re-run this
script for the current numbers.

Usage: python3 probe_shortkey_id.py [--nrand 800] [--trials 3]
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
import random

import gematria as g
from parse_lp import parse
from language_model import get_model
from attack_keyskip import beam_decode
from no_repeat_model import enc_key_skip
from doublet_sim import english_plaintext

N = g.N


def score_key(model, ct, key, head, beam, max_skip=2):
    """Best trigram (over both signs) for decoding ct[:head] with `key`."""
    reps = head * (max_skip + 1) // len(key) + 4
    best = None
    for sign in (-1, +1):
        sc, dec = beam_decode(ct[:head], key * reps, 0, sign, model, beam, max_skip)
        bl = sc / max(1, head - 1)
        if best is None or bl > best[0]:
            best = (bl, sign, dec)
    return best


def probe(model, pt_full, L, head, beam, nrand, trials, rng):
    """Rank the true key against DISTINCT distractor keys.

    AUDIT FIX. The original counted `score >= true` over `nrand` keys redrawn
    INDEPENDENTLY each time, which inflated the rank three ways and produced the
    bogus "L<=4 is not identifiable" result:
      1. keys were drawn WITH REPLACEMENT from a space of only N^L (841 at L=2),
         so the TRUE key itself was redrawn ~1.8 times per trial and counted as
         beating itself;
      2. `score_key` maximises over both signs, so a key's sign-mirror
         ((-k) mod 29) decodes to the identical plaintext and ALWAYS ties — and
         was always counted as a beat;
      3. `>=` counted ties as beats.
    Ground truth (exhaustive L=2 in `attack_shortbrute.py`): the true key ranks
    strictly first of 841. So we now draw DISTINCT distractors, exclude the true
    key and its sign-mirror, and count STRICT betters; ties are reported apart.
    """
    pt = pt_full[:head]
    ranks, accs, ties_seen = [], [], []
    for _ in range(trials):
        key = [rng.randint(0, N - 1) for _ in range(L)]
        while len(set(key)) < 2:                 # constant key can't key-skip
            key = [rng.randint(0, N - 1) for _ in range(L)]
        reps = head * 3 // len(key) + 4
        ct = enc_key_skip(pt, key * reps)
        tb = score_key(model, ct, key, head, beam)
        accs.append(sum(1 for a, b in zip(tb[2], pt) if a == b) / len(pt))

        mirror = tuple((-k) % N for k in key)    # decodes identically by symmetry
        seen = {tuple(key), mirror}
        distract, space = [], N ** L
        while len(distract) < nrand and len(seen) < space:
            cand = tuple(rng.randint(0, N - 1) for _ in range(L))
            if cand in seen:
                continue
            seen.add(cand)
            distract.append(cand)
        better = ties = 0
        for d in distract:
            sc = score_key(model, ct, list(d), head, beam)[0]
            if sc > tb[0]:
                better += 1
            elif sc == tb[0]:
                ties += 1
        ranks.append(better + 1)
        ties_seen.append(ties)
    return ranks, accs, ties_seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nrand", type=int, default=800,
                    help="random distractor keys per trial")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--beam", type=int, default=100)
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    model = get_model(args.order)
    pt = english_plaintext(parse("data/liber_primus.md"))
    rng = random.Random(args.seed)

    def line(L, head):
        ranks, accs, ties = probe(model, pt, L, head, args.beam, args.nrand,
                                  args.trials, rng)
        import statistics as st
        space = N ** L
        print(f"L={L} head={head} beam={args.beam}: true-key rank "
              f"~{st.mean(ranks):.1f} of {min(args.nrand, space - 2) + 1} distinct "
              f"(want 1), acc ~{st.mean(accs)*100:.0f}%, ties ~{st.mean(ties):.1f} "
              f"| ranks {ranks}")

    print(f"identifiability of length-L keys under key-skip "
          f"({args.nrand} distractors x {args.trials} trials):")
    for L in (2, 3, 4, 5, 6):
        line(L, 30)
    print("--- longer head (more constraint per key value) ---")
    for L in (2, 3, 4):
        line(L, 60)


if __name__ == "__main__":
    main()
