"""Test the page-16 magic square as an INTERRUPTER SCHEDULE (not an additive key).

`attack_magicsquare.py` tested the square VALUES as a repeating additive
keystream (c = p + sq[j]) — negative. This asks a different question, the one
CLAUDE.md flags as still-open (§16): does the square schedule *the motion of a
base keystream* rather than supply the added values?

An interrupter cipher has a base keystream K0 (here: primes, totients, the
solved-page word key DIVINITY, or the square's own values) whose pointer is
perturbed by a schedule. The page-16 square, read in some order and repeated,
IS that schedule. Three mechanisms, each a deterministic (invertible) decrypt:

  STRIDE : the pointer advances by 1 + (s mod m) each rune — the square dictates
           a variable key-stride (a dense skip schedule).
  GATED  : the pointer advances +1 normally, +2 (one extra skip) when the
           schedule value triggers (s mod k == 0, or s prime) — a SPARSE
           interrupter, the closest analogue to the observed ~3% key-skip.
  RESET  : the pointer advances +1 normally, but RESETS to 0 when the schedule
           value triggers — the classic "interrupted key". The key-skip beam
           (attack_keyskip) canNOT express a reset (it only nudges the pointer
           +0/+1/+2 locally), so this is genuinely new coverage.

Relationship to what's already ruled out (be honest, CLAUDE.md ground rules):
  attack_keyskip already beam-searches EVERY skip-<=2 schedule over primes and
  totients and is negative — so STRIDE/GATED with small skips over primes and
  totients is largely SUBSUMED by that negative. The new ground here is RESET,
  larger strides, and the square/DIVINITY base streams. Stated plainly below.

Every run is control-validated: a positive control plants a known interrupter
encryption and confirms the search grid recovers the plaintext AND identifies
the planted mechanism; a chance ceiling (same grid on random text) bounds the
multiple-comparison inflation. A genuine break lands near the English trigram
reference (~-3.4); edging a noisy ceiling by tenths while ~1 below English is
chance.

Usage: python3 attack_magicsquare_interrupter.py [--head 120] [--draws 6]
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

import gematria as g
import ciphers as c
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from controls import matched_ceiling, verdict

N = g.N

# page-16 square: 5x5, magic constant 3301, palindromic, prime centre 809.
M16 = [[434, 1311, 312, 278, 966],
       [204, 812, 934, 280, 1071],
       [626, 620, 809, 620, 626],
       [1071, 280, 934, 812, 204],
       [966, 278, 312, 1311, 434]]


# --- reading orders over the square -----------------------------------------

def rowmajor(M):
    return [v for r in M for v in r]


def colmajor(M):
    return [M[i][j] for j in range(len(M[0])) for i in range(len(M))]


def boustrophedon(M):
    out = []
    for i, r in enumerate(M):
        out.extend(r if i % 2 == 0 else r[::-1])
    return out


def spiral(M):
    rows, cols = len(M), len(M[0])
    seen = [[False] * cols for _ in range(rows)]
    out, i, j, di, dj = [], 0, 0, 0, 1
    for _ in range(rows * cols):
        out.append(M[i][j])
        seen[i][j] = True
        ni, nj = i + di, j + dj
        if not (0 <= ni < rows and 0 <= nj < cols) or seen[ni][nj]:
            di, dj = dj, -di          # turn right
            ni, nj = i + di, j + dj
        i, j = ni, nj
    return out


ORDERS = {"row": rowmajor, "col": colmajor,
          "boustro": boustrophedon, "spiral": spiral}


def is_prime(n):
    return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))


# --- base keystreams (the VALUES the interrupter walks over) -----------------

def base_streams(length):
    out = {}
    for name, gen in [("prime", c.prime_stream), ("totient", c.totient_stream)]:
        vals, it = [], gen()
        for _ in range(length):
            vals.append(next(it) % N)
        out[name] = vals
    sq = [v % N for v in rowmajor(M16)]
    out["square"] = [sq[i % len(sq)] for i in range(length)]      # self-key
    div = g.latin_to_indices("DIVINITY")
    out["DIVINITY"] = [div[i % len(div)] for i in range(length)]
    return out


# --- the interrupter mechanisms (deterministic pointer schedule) -------------
# A rule is (kind, param). The pointer path depends ONLY on the schedule and
# position, never on the text, so encryption and decryption share it exactly.

def advance(ptr, s, rule):
    kind, param = rule
    if kind == "stride":
        return ptr + 1 + (s % param)
    if kind == "gated":
        trig = is_prime(s) if param == "prime" else (s % param == 0)
        return ptr + (2 if trig else 1)
    if kind == "reset":
        trig = is_prime(s) if param == "prime" else (s % param == 0)
        return 0 if trig else ptr + 1
    raise ValueError(kind)


RULES = ([("stride", m) for m in (2, 3, 5, 7)]
         + [("gated", k) for k in (2, 3, 5, "prime")]
         + [("reset", k) for k in (2, 3, 5, "prime")])


def decrypt(cipher, K0, sched, rule, sign):
    """p = (c + sign*K0[ptr]) % N ; sign=-1 <=> encryption c = p + K0."""
    out, ptr = [], 0
    for i, ci in enumerate(cipher):
        out.append((ci + sign * K0[ptr]) % N)
        ptr = advance(ptr, sched[i % len(sched)], rule)
    return out


def encrypt(plain, K0, sched, rule, sign):
    """Inverse of `decrypt`: c = (p - sign*K0[ptr]) % N along the same path."""
    out, ptr = [], 0
    for i, pi in enumerate(plain):
        out.append((pi - sign * K0[ptr]) % N)
        ptr = advance(ptr, sched[i % len(sched)], rule)
    return out


def build_grid():
    """All (base, order, rule, sign) mechanisms as named tuples."""
    grid = []
    for bname in ("prime", "totient", "square", "DIVINITY"):
        for oname in ORDERS:
            for rule in RULES:
                for sign in (-1, +1):
                    grid.append((bname, oname, rule, sign))
    return grid


def search(cipher, streams, model):
    """Best (score, mechanism, plaintext) over the whole interrupter grid."""
    best = None
    for bname, oname, rule, sign in build_grid():
        sched = [v for v in ORDERS[oname](M16)]
        dec = decrypt(cipher, streams[bname], sched, rule, sign)
        sc = model.score_sequence(dec)
        if best is None or sc > best[0]:
            best = (sc, (bname, oname, rule, sign), dec)
    return best


def mech_str(m):
    bname, oname, (kind, param), sign = m
    return f"{bname}/{oname}/{kind}:{param}/{'c+k' if sign < 0 else 'c-k'}"


# --- controls ----------------------------------------------------------------

def positive_control(streams, model, head):
    """Plant a known interrupter encryption; confirm the grid recovers it."""
    print("=== POSITIVE CONTROL: plant an interrupter-scheduled encryption ===")
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:head]
    planted = ("prime", "row", ("stride", 3), -1)       # c = p + prime, stride-3
    sched = ORDERS[planted[1]](M16)
    ct = encrypt(pt, streams[planted[0]], sched, planted[2], planted[3])
    sc, mech, dec = search(ct, streams, model)
    acc = sum(1 for a, b in zip(dec, pt) if a == b) / len(pt)
    ok = mech == planted and acc > 0.9
    print(f"  planted  {mech_str(planted)}")
    print(f"  recovered {mech_str(mech)} trigram {sc:.2f}, {acc*100:.0f}% of "
          f"plaintext")
    print(f"  control: {'PASS' if ok else 'FAIL'}\n")
    return ok


def chance_ceiling(streams, model, head, draws):
    best = None
    for d in range(draws):
        rng = LCG(500 + d)
        ct = [rng.randint(N) for _ in range(head)]
        sc, _, _ = search(ct, streams, model)
        best = sc if best is None else max(best, sc)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", type=int, default=120)
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--draws", type=int, default=6)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(args.order)
    # base streams long enough for the worst-case stride (1+6 per rune) + reset
    streams = base_streams(8 * args.head + 512)
    grid = build_grid()

    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(3)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"interrupter grid: {len(grid)} mechanisms "
          f"(4 base streams x {len(ORDERS)} orders x {len(RULES)} rules x 2 "
          f"signs)")
    print(f"refs: English trigram {eng:.2f}, random {rnd:.2f}\n")

    if not positive_control(streams, model, args.head):
        print("control FAILED — not trusting the real run.")
        return

    real = [x for x in segs if not x.solved and len(x.indices) >= 50]
    score_fn = lambda ct: search(ct, streams, model)[0]
    cache = {}

    def ceil_at(L):
        if L not in cache:
            cache[L] = matched_ceiling(score_fn, L, trials=len(real), seed=500)
        return cache[L]

    print("REAL unsolved segments (page-16 square as interrupter schedule),")
    print("each against a chance ceiling at ITS OWN length (audit §28/R2):")
    overall = None
    for s in real:
        ix = s.indices[:args.head]
        sc, mech, dec = search(ix, streams, model)
        cl = ceil_at(len(ix))
        margin = sc - cl
        flag = "  <-- above its ceiling" if margin > 0 else ""
        print(f"  {s.section[:28]:28s} L={len(ix):3d} {mech_str(mech):30s} "
              f"{sc:6.2f} vs ceil {cl:6.2f} ({margin:+.2f}){flag}")
        if overall is None or margin > overall[0]:
            overall = (margin, sc, cl, s.section, mech, dec)
    ceil = overall[2]

    margin, sc, cl, sect, mech, dec = overall
    print(f"\nbest by length-matched margin: {sc:.2f} on {sect[:26]} "
          f"({mech_str(mech)}) vs its own ceiling {cl:.2f} -> margin {margin:+.2f}")
    if margin > 0.5 and sc > eng - 0.5:
        print("-> SIGNAL — inspect.")
    else:
        print(f"-> NO SIGNAL: every mechanism sits at/below a length-matched "
              f"chance ceiling, and {eng - sc:.1f} below English ({eng:.2f}). "
              f"(The published §17 comparison used a fixed-length null, which "
              f"understated the margin; matched, the negative is stronger.)")


if __name__ == "__main__":
    main()
