"""Digraphic Hill cipher — 2x2 invertible matrix over GF(29), brute + controls (N22).

From the Swedish paper (`download/Kryptografiska Metoder ...`): rune pairs are
enciphered blockwise,

    (C_{2i}, C_{2i+1})^T  =  [[a, b], [c, d]] . (P_{2i}, P_{2i+1})^T   (mod 29),

with det = ad - bc != 0. This is the one classical cipher class the campaign had
not tested (§48 is the AFFINE, 1x1, cipher). The key is only four numbers, so the
whole invertible-matrix space (682,080 matrices) is brute-forceable.

The paper claims Hill *explains the doublet suppression*. A separate structural
test refutes that (§61): our 86 doublets split 44/42 across the within-block /
between-block position parity — perfectly symmetric — whereas a Hill matrix that
suppresses within-block doublets forces a sharp asymmetry (within ~0%, between
~3.45%). So the suppression is a global lag-1 rule, not a Hill-block effect. This
module adds the control-validated brute for the base-cipher reading: decrypt each
segment head under every invertible matrix and score it, floor and ceiling gated.

Usage: python3 attack_hill.py [--head 60] [--workers N]
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
import itertools
import os

import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from controls import detection_floor, matched_ceiling, verdict

N = g.N


# --- Hill primitives ---------------------------------------------------------

def is_invertible(M):
    a, b, c, d = M
    return (a * d - b * c) % N != 0


def inverse(M):
    a, b, c, d = M
    det = (a * d - b * c) % N
    di = pow(det, -1, N)
    return ((d * di) % N, ((-b) * di) % N, ((-c) * di) % N, (a * di) % N)


def hill_encrypt(pt, M):
    a, b, c, d = M
    out = []
    for i in range(0, len(pt) - 1, 2):
        p0, p1 = pt[i], pt[i + 1]
        out.append((a * p0 + b * p1) % N)
        out.append((c * p0 + d * p1) % N)
    return out


def hill_decrypt(ct, M):
    return hill_encrypt(ct, inverse(M))          # decrypt = encrypt with inverse


def invertible_matrices():
    for M in itertools.product(range(N), repeat=4):
        if (M[0] * M[3] - M[1] * M[2]) % N != 0:
            yield M


# --- brute (parallel; deterministic, so worker-count-independent) ------------

_WORKER_MODEL = None


def _worker_init(order):
    global _WORKER_MODEL
    _WORKER_MODEL = get_model(order)


def _worker_score(task):
    ct, M = task
    dec = hill_decrypt(list(ct), M)
    return (_WORKER_MODEL.score_sequence(dec), M, dec)


def brute_best(cidx, model, head, workers=1, order=3):
    """Best (score, matrix, decode) over all invertible 2x2 matrices."""
    h = head - (head % 2)
    chead = tuple(cidx[:h])
    if workers and workers > 1:
        import multiprocessing as mp
        tasks = ((chead, M) for M in invertible_matrices())
        with mp.Pool(workers, initializer=_worker_init, initargs=(order,)) as pool:
            best = None
            for r in pool.imap_unordered(_worker_score, tasks, chunksize=4096):
                if best is None or r[0] > best[0]:
                    best = r
            return best
    best = None
    for M in invertible_matrices():
        dec = hill_decrypt(list(chead), M)
        sc = model.score_sequence(dec)
        if best is None or sc > best[0]:
            best = (sc, M, dec)
    return best


# --- detection floor ---------------------------------------------------------

def hill_floor(model, head, workers, order, samples=5):
    pt = english_plaintext(parse("data/liber_primus.md"))[:head]
    pt = pt[:len(pt) - (len(pt) % 2)]
    rng = LCG(20260825)
    plants = []
    while len(plants) < samples:
        M = tuple(rng.randint(N) for _ in range(4))
        if is_invertible(M) and M not in plants:
            plants.append(M)

    st = {}

    def plant(M):
        st["M"] = M
        return hill_encrypt(pt, M)

    def recover(ct):
        sc, M, dec = brute_best(ct, model, len(ct), workers, order)
        acc = sum(1 for x, y in zip(dec, pt) if x == y) / len(pt)
        return sc, M, acc

    return detection_floor(plants, plant, recover, label="matrix")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", type=int, default=60)
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--workers", type=int,
                    default=max(1, (os.cpu_count() or 2) - 2))
    args = ap.parse_args()

    model = get_model(args.order)
    segs = parse("data/liber_primus.md")
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]

    ninv = sum(1 for _ in invertible_matrices())
    print(f"key space: {ninv} invertible 2x2 matrices over GF(29), "
          f"head {args.head}, workers {args.workers}")
    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(5)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"refs: English trigram {eng:.2f}, random {rnd:.2f}\n")

    floor, cov, unc, _ = hill_floor(model, args.head, args.workers, args.order)

    cstate = {"t": 0}

    def ceil_score(ct):
        s = brute_best(ct, model, args.head, args.workers, args.order)[0]
        cstate["t"] += 1
        return s
    ceil = matched_ceiling(ceil_score, args.head, trials=len(unsolved), seed=6200)
    print(f"=== MATCHED CHANCE CEILING ({len(unsolved)} trials): {ceil:.2f} ===\n")

    print("=== REAL: unsolved segments (best invertible matrix) ===")
    overall = None
    for s in unsolved:
        sc, M, dec = brute_best(s.indices, model, args.head, args.workers, args.order)
        overall = sc if overall is None else max(overall, sc)
        print(f"  {s.section[:34]:34s} matrix {str(M):18s} {sc:.2f}  "
              f"{g.indices_to_latin(dec)[:40]}")

    print()
    print(verdict(overall, floor, ceil, n_covered=len(cov),
                  n_total=len(cov) + len(unc), label="matrices"))


if __name__ == "__main__":
    main()
