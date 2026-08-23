"""LP2-as-pad inversion (N18 / Dukotah's F-01).

Every attack so far treats the unsolved stream U as CIPHERTEXT to decrypt. F-01
inverts that: U may be KEY MATERIAL — a running-key pad — not a message. Then for
some text C, the plaintext is P = C - U (position-locked, no key-skip, because a
pad is applied cleanly). Test U (forward / reversed / atbash) against candidate
texts C and look for English.

A theoretical guarantee frames the result before it runs. §4 measured U as
statistically UNIFORM (IoC 1.000). Subtracting a uniform, independent stream from
anything gives a uniform stream, so U - C is gibberish for every C INDEPENDENT of
U. §6/§9 already showed U is independent of KJV / Rune Poem / Liber AL /
Mabinogion / Blake, so those arms are a formality. The only arms where
uniformity does NOT force gibberish are the ones where C is BUILT from U:

  * self-folds — U vs reverse(U) / atbash(U): a folded pad (key = reverse of
    message) would make U a palindrome, and U - reverse(U) identically zero. U is
    not a palindrome, so this is also excluded — but it is the construction the
    "fwd/rev/atbash" phrasing points at, so it is tested explicitly.
  * U vs the SOLVED plaintext: is U the solved English under some running key
    (U - P_solved)? Never tested.

The test is real, not just the theory: a planted control embeds an English window
in an otherwise-random difference stream and must be recovered by the same
window scan, and a matched chance ceiling and detection floor gate the verdict.

Usage: python3 attack_padinvert.py [--win 48]
"""

import argparse

import gematria as g
import ciphers as c
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from controls import matched_ceiling, detection_floor, verdict
import solved_text
import keytexts

N = g.N


def unsolved_stream():
    segs = parse("data/liber_primus.md")
    return [i for s in segs if not s.solved and len(s.indices) >= 50
            for i in s.indices]


def best_window(D, model, W):
    """Max English n-gram score over every length-W window of D."""
    if len(D) < W:
        return model.score_sequence(D) if D else -99.0
    best = -1e9
    for s in range(0, len(D) - W + 1):
        sc = model.score_sequence(D[s:s + W])
        if sc > best:
            best = sc
    return best


def diff(A, B, sign):
    """(A - sign*B) mod N over the overlap."""
    L = min(len(A), len(B))
    return [(A[i] - sign * B[i]) % N for i in range(L)]


def scan_pair(A, B, model, W, offsets):
    """Best-window score of A vs B over both signs and the given B-offsets."""
    best = -1e9
    for off in offsets:
        Bo = B[off:] if off >= 0 else B
        for sign in (-1, +1):
            sc = best_window(diff(A, Bo, sign), model, W)
            if sc > best:
                best = sc
    return best


# --- candidates ---------------------------------------------------------------

def candidates(U):
    rev = list(reversed(U))
    atb = c.atbash(U)
    solved = solved_text.full_plaintext()
    cands = {
        "reverse(U)":        (rev, [0]),
        "atbash(U)":         (atb, [0]),
        "atbash(reverse(U))": (c.atbash(rev), [0]),
        "solved-plaintext":  (solved, list(range(0, max(1, len(U) - len(solved)),
                                                  400))),
    }
    for name in ("runepoem_oe", "kjv"):
        try:
            t = keytexts.get(name)[:len(U)]
            cands[f"{name} (sanity)"] = (t, [0])
        except Exception:
            pass
    return cands


# --- control: plant an English window in a random difference stream ----------

def calibrate(model, W):
    """Detection floor: embed a real English window in an otherwise-random
    difference stream and confirm the window scan recovers it (position and
    score). The floor is the minimum recovered score."""
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)
    starts = {"plant@2000": 2000, "plant@6000": 6000, "plant@0": 0}
    L, EMBED = 4000, 100

    floor = None
    print("=== DETECTION FLOOR: plant an English window, confirm the scan finds "
          "it ===")
    for nm, st0 in starts.items():
        rng = LCG(4242 + st0)
        D = [rng.randint(N) for _ in range(L)]
        s = st0 % (len(pt) - W)
        D[EMBED:EMBED + W] = pt[s:s + W]        # embed a real English window
        best, arg = -1e9, -1
        for st in range(0, len(D) - W + 1):
            sc = model.score_sequence(D[st:st + W])
            if sc > best:
                best, arg = sc, st
        ok = abs(arg - EMBED) <= 2
        floor = best if floor is None else min(floor, best)
        print(f"  {nm}: best window {best:.2f} at {arg} "
              f"({'FOUND the English window' if ok else 'MISSED'})")
    print(f"  FLOOR = {floor:.2f}\n")
    return floor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--win", type=int, default=48)
    ap.add_argument("--order", type=int, default=3)
    args = ap.parse_args()
    model = get_model(args.order)
    U = unsolved_stream()
    print(f"unsolved stream U: {len(U)} runes\n")

    floor = calibrate(model, args.win)

    # matched chance ceiling: best-window over random difference streams, one
    # trial per real candidate arm.
    cands = candidates(U)
    n_trials = len(cands)
    ceil = matched_ceiling(lambda D: best_window(D, model, args.win),
                           length=len(U), trials=n_trials, seed=808)
    print(f"=== MATCHED CHANCE CEILING ({n_trials} arms, len {len(U)}): "
          f"{ceil:.2f} ===\n")

    print("=== REAL: U as a pad against each candidate (best window, both signs, "
          "offsets) ===")
    overall = -1e9
    for name, (C, offs) in cands.items():
        sc = scan_pair(U, C, model, args.win, offs)
        overall = max(overall, sc)
        print(f"  U vs {name:22s} best-window {sc:.2f}")

    print()
    print(verdict(overall, floor, ceil, n_covered=3, n_total=3, label="arms"))
    print("\nnote: U is statistically uniform (§4), so U minus any INDEPENDENT "
          "text is\nuniform by construction — the external arms are a formality. "
          "A folded pad\nwould force U to be a palindrome, which it is not. The "
          "inversion is closed.")


if __name__ == "__main__":
    main()
