"""Gromark / chain-addition primer brute, WITH the key-skip desync (N10).

The hypothesis. A puzzle-maker working by hand cannot run a CSPRNG, but the ACA
**Gromark** cipher gives a pencil-and-paper keystream: start from a short numeric
**primer** and extend it by CHAIN ADDITION — each new key value is the sum of two
earlier ones, mod the alphabet. Generalised to mod 29:

    k[i] = (k[i-L] + k[i-L+1]) mod 29      for i >= L, primer = k[0..L-1]

This is the untested cell of the seeded-keystream family. §13 covered machine
PRNGs (LCG, xorshift, Mersenne, SHA); §10/§33 brute-forced short REPEATED keys;
neither tested a short primer EXPANDED by a linear recurrence.

Why L is exactly 3 here — an analytic result, not a choice:
  * L=2 chain addition IS the Fibonacci recurrence mod 29. Its Pisano period is
    14, so EVERY length-2 primer yields a keystream of period <= 14 — already
    inside §3's period-<=40 Vigenere/key-skip scan. Measured: all 841 L=2 primers
    have period in {1, 7, 14}. So L=2 is not new coverage and is skipped.
  * L=3: 24,388 of 24,389 primers yield period **871** (only the degenerate
    all-equal primer is period 1). 871 exceeds any segment head, so within a
    segment the keystream is effectively aperiodic — genuinely uncovered by §3.

Identifiability (the §33 trap, checked before building this). Repeated L=3 keys
under key-skip were barely identifiable (§33: ~1/10 planted survived), because a
period-3 key gives the beam too much freedom. A chain-addition keystream of
period 871 is far more distinctive: a probe planted 5 primers and 0 of 400
random distractors beat the true one (true ~-3.58 vs best distractor ~-4.0). So
this family is identifiable and worth a full brute. The detection floor below
re-checks that against the FULL 24,389-primer space, not a sample.

Everything routes through controls.py: a detection floor (plant a primer, recover
it, read the score a real break gives) and a length- and trial-matched chance
ceiling gate the verdict.

Usage: python3 attack_gromark.py [--head 44] [--beam 50] [--max-skip 2]
       python3 attack_gromark.py --periods   # print the period analysis, exit
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
import json
import os

import gematria as g
from parse_lp import parse
from language_model import get_model
from attack_keyskip import beam_decode
from no_repeat_model import enc_key_skip
from doublet_sim import english_plaintext, LCG
from controls import detection_floor, matched_ceiling, verdict

N = g.N
L = 3  # the only primer length that is new coverage (see module docstring)


# --- chain-addition keystream ------------------------------------------------

def chain(primer, n):
    """Gromark chain addition, mod 29: k[i] = k[i-L] + k[i-L+1]."""
    ln = len(primer)
    k = list(primer)
    while len(k) < n:
        k.append((k[-ln] + k[-ln + 1]) % N)
    return k[:n]


def period(primer, maxp=2000):
    ln = len(primer)
    k = chain(primer, ln + maxp)
    start = tuple(k[:ln])
    for i in range(1, maxp):
        if tuple(k[i:i + ln]) == start:
            return i
    return -1


def primers():
    """All L=3 primers except the degenerate all-equal ones (period 1 =
    constant keystream = a plain shift, ruled out §3)."""
    for t in itertools.product(range(N), repeat=L):
        if len(set(t)) == 1:
            continue
        yield t


# --- brute -------------------------------------------------------------------

def confirm(chead, primer, model, sign, beam, max_skip):
    need = len(chead) * (max_skip + 1) + 16
    sc, dec = beam_decode(chead, chain(primer, need), 0, sign, model, beam,
                          max_skip)
    return sc / max(1, len(chead) - 1), dec


# --- parallel worker (module-level so it pickles under multiprocessing spawn) -
_WORKER_MODEL = None


def _worker_init(order):
    global _WORKER_MODEL
    _WORKER_MODEL = get_model(order)


def _worker_score(task):
    """Score one primer over both signs; return the better (bl, primer, sign,
    dec). Mirrors the serial inner loop exactly (sign -1 tried first)."""
    primer, chead, beam, max_skip = task
    best = None
    for sign in (-1, +1):
        bl, dec = confirm(list(chead), primer, _WORKER_MODEL, sign, beam, max_skip)
        if best is None or bl > best[0]:
            best = (bl, tuple(primer), sign, dec)
    return best


def brute_best(cidx, model, head, beam, max_skip, primer_list=None, workers=1,
               order=3):
    """Best (norm-score, primer, sign, decode) over the L=3 primers, both signs,
    decoded with the key-skip beam from start 0.

    primer_list: primers to test (default: all non-degenerate L=3 primers).
    workers>1 parallelises the primer loop across processes. The result is
    identical to serial — per-primer scores are deterministic and ties break by
    list order — so the checkpoint cache (keyed by ciphertext only) stays valid
    regardless of worker count. `order` seeds each worker's language model.
    """
    chead = cidx[:head]
    plist = list(primer_list) if primer_list is not None else list(primers())
    if workers and workers > 1:
        import multiprocessing as mp
        tasks = [(p, tuple(chead), beam, max_skip) for p in plist]
        chunk = max(1, len(tasks) // (workers * 8))
        with mp.Pool(workers, initializer=_worker_init, initargs=(order,)) as pool:
            results = pool.map(_worker_score, tasks, chunksize=chunk)
        best = None
        for r in results:            # keep FIRST max, matching serial's strict >
            if best is None or r[0] > best[0]:
                best = r
        return best
    best = None
    for p in plist:
        for sign in (-1, +1):
            bl, dec = confirm(chead, p, model, sign, beam, max_skip)
            if best is None or bl > best[0]:
                best = (bl, p, sign, dec)
    return best


# --- checkpointing -----------------------------------------------------------
# Each brute over the 24k-primer space is ~minutes; a whole run is dozens of
# them. An external kill (a background job was stopped ~25 min in) must not throw
# that away, so every brute result is cached by a string key. Re-running resumes
# from the cache; delete the file to start clean.

CKPT = "results/gromark_ckpt.json"


def _load_ckpt():
    if os.path.exists(CKPT):
        with open(CKPT) as f:
            return json.load(f)
    return {}


def cached_brute(key, cidx, model, head, beam, max_skip, ckpt, workers=1, order=3):
    """brute_best, memoised to CKPT by `key`. Stores the decode as rune indices
    (json-safe, and accuracy needs the exact indices — latin is not invertible).
    `workers` only speeds the compute; the cached result is worker-count-independent."""
    if key in ckpt:
        r = ckpt[key]
        return r["score"], tuple(r["primer"]), r["sign"], r["decode"]
    bl, p, sign, dec = brute_best(cidx, model, head, beam, max_skip,
                                  workers=workers, order=order)
    ckpt[key] = {"score": bl, "primer": list(p), "sign": sign, "decode": list(dec)}
    with open(CKPT, "w") as f:
        json.dump(ckpt, f)
    return bl, p, sign, list(dec)


# --- detection floor ---------------------------------------------------------

def gromark_floor(model, head, beam, max_skip, ckpt, samples=5, workers=1, order=3):
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:head]
    rng = LCG(20260823)
    plant_primers = []
    while len(plant_primers) < samples:
        t = tuple(rng.randint(N) for _ in range(L))
        if len(set(t)) >= 2 and t not in plant_primers:
            plant_primers.append(t)

    state = {}

    def plant(p):
        state["key"] = f"floor:{p}"
        return enc_key_skip(pt, chain(p, head * (max_skip + 1) + 16))

    def recover(ct):
        bl, p, sign, dec = cached_brute(state["key"], ct, model, head, beam,
                                        max_skip, ckpt, workers=workers, order=order)
        m = min(len(dec), len(pt))
        acc = sum(1 for a, b in zip(dec[:m], pt[:m]) if a == b) / m
        return bl, p, acc

    return detection_floor(plant_primers, plant, recover, label="primer")


# --- main --------------------------------------------------------------------

def print_periods():
    import collections
    print("period analysis (chain addition mod 29):")
    for ln in (2, 3):
        per = collections.Counter()
        for t in itertools.product(range(N), repeat=ln):
            per[period(t)] += 1
        tot = sum(per.values())
        le40 = sum(v for k, v in per.items() if 0 < k <= 40)
        print(f"  L={ln}: {tot} primers, periods {sorted(k for k in per)} "
              f"-> {le40} ({le40*100//tot}%) have period<=40 (covered by §3)")
    print("  => L=2 is entirely covered by §3; only L=3 (period 871) is new.\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", type=int, default=44)
    ap.add_argument("--beam", type=int, default=50)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2),
                    help="parallel processes for the primer brute (result is "
                         "identical to serial; only faster). Default: cores-2.")
    ap.add_argument("--periods", action="store_true",
                    help="print the period analysis and exit")
    ap.add_argument("--global-only", action="store_true",
                    help="test only the global concatenated stream (1 real "
                         "trial); skip the 13 per-segment brutes. Keeps the run "
                         "small enough to finish under the background-job reaper.")
    args = ap.parse_args()

    if args.periods:
        print_periods()
        return

    model = get_model(args.order)
    segs = parse("data/liber_primus.md")
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]

    print_periods()
    nprimers = N ** L - N   # minus the 29 all-equal degenerates
    print(f"key space: {nprimers} L=3 chain-addition primers x 2 signs, "
          f"key-skip max {args.max_skip}, head {args.head}, beam {args.beam}")
    ckpt = _load_ckpt()
    if ckpt:
        print(f"(resuming from {CKPT}: {len(ckpt)} brutes already cached)")
    print()

    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(5)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"refs: English trigram {eng:.2f}, random {rnd:.2f}\n")

    print(f"workers: {args.workers} (parallel brute; result identical to serial)\n")
    floor, cov, unc, _ = gromark_floor(model, args.head, args.beam,
                                       args.max_skip, ckpt,
                                       workers=args.workers, order=args.order)

    # matched ceiling: independent null, one trial per real run. With
    # --global-only the real run is a single trial (the global stream).
    n_trials = 1 if args.global_only else len(unsolved) + 1
    cstate = {"t": 0}

    def ceil_score(ct):
        bl = cached_brute(f"ceil:{cstate['t']}", ct, model, args.head,
                          args.beam, args.max_skip, ckpt,
                          workers=args.workers, order=args.order)[0]
        cstate["t"] += 1
        return bl
    ceil = matched_ceiling(ceil_score, args.head, trials=n_trials, seed=6100)
    print(f"=== MATCHED CHANCE CEILING ({n_trials} trials): {ceil:.2f} ===\n")

    # GLOBAL: one primer for the whole concatenated unsolved stream
    glob = [i for s in unsolved for i in s.indices][:args.head]
    gbl, gp, gsign, gdec = cached_brute("global", glob, model, args.head,
                                        args.beam, args.max_skip, ckpt,
                                        workers=args.workers, order=args.order)
    print("=== REAL: global keystream (one primer, whole stream) ===")
    print(f"  best primer {gp} {'c-k' if gsign<0 else 'c+k'} score {gbl:.2f}")
    print(f"    {g.indices_to_latin(gdec)[:100]}\n")

    overall = gbl
    if not args.global_only:
        print("=== REAL: per-segment keystream (each page its own primer) ===")
        for s in unsolved:
            bl, p, sign, dec = cached_brute(f"seg:{s.section}", s.indices, model,
                                            args.head, args.beam, args.max_skip,
                                            ckpt, workers=args.workers,
                                            order=args.order)
            overall = max(overall, bl)
            print(f"  {s.section[:34]:34s} primer {str(p):14s} "
                  f"{'c-k' if sign<0 else 'c+k'} {bl:.2f}")
    else:
        print("(per-segment brutes skipped: --global-only; a per-page primer "
              "is a documented coverage limit, carried to BACKLOG N10.)")

    print()
    print(verdict(overall, floor, ceil, n_covered=len(cov),
                  n_total=len(cov) + len(unc), label="primers"))


if __name__ == "__main__":
    main()
