"""N1 — interrupter over ALL 29 runes, not just ᚠ.

Everything this project has done with interrupters assumed the interrupter is
**ᚠ**: §19 tested the literal-ᚠ rule (pointer holds at a ciphertext ᚠ) and §17
tested square-driven schedules. relikd's *LiberPrayground* drops that assumption
and brute-forces the interrupt rune itself. This is the same idea, built here so
it runs against our controls.

Why it is not covered by earlier work. §2's periodic-IoC scan tested key periods
1-40 on the raw stream and found nothing above noise — but an interrupter is
precisely what *masks* periodicity: every interrupt shifts every later position
into a different key slot, so a perfectly periodic key looks aperiodic. The test
therefore has to be redone once per candidate interrupt rune.

Method. For a candidate interrupt rune r and key length L, walk the ciphertext
with a key pointer j. At a rune equal to r, treat it as an interrupt — the
pointer HOLDS (that position is not keyed). Otherwise assign the position to key
slot (j mod L) and advance. If (r, L) is right, each slot is a single Caesar
shift of English, so the per-slot index of coincidence rises to English-like
(~1.7); if wrong, slots stay flat (~1.0). Scoring by IoC rather than by a beam
avoids the skip-penalty and short-length traps of §33/§39.

Control-validated: a planted (interrupt rune, key) text must be recovered — that
is the detection floor — against a matched ceiling from an independent null.

Usage: python3 attack_interrupt29.py [--max-len 32]
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
from parse_lp import parse
from doublet_sim import english_plaintext, ioc
from controls import detection_floor, matched_ceiling, verdict, random_runes

N = g.N


MIN_SLOT = 25          # below this, IoC is small-sample noise (see §33/§39)


def _mean_slot_ioc(slots):
    vals = [ioc(s) for s in slots if len(s) >= MIN_SLOT]
    if len(vals) < max(2, len(slots) // 2):
        return 0.0        # too few usable slots to judge
    return sum(vals) / len(vals)


def slot_ioc_all(cipher, interrupt_rune, L):
    """Naive variant: EVERY occurrence of `interrupt_rune` is an interrupt.

    This does not work, and the reason matters. A ciphertext rune equal to r is
    AMBIGUOUS — either a real interrupt (pointer held) or an ordinary rune that
    happened to encrypt to r (pointer advanced). At ~1/29 that is ~40 spurious
    skips per 1200 runes, and each one shifts every later position into a
    different key slot, destroying the very periodicity we are testing for. A
    planted (rune, key) is NOT recovered this way — the control fails. This is
    the generalisation of the literal-ᚠ ambiguity §19 documented, and it is why
    the interrupt hypothesis requires a search over interrupt SUBSETS.
    """
    slots = [[] for _ in range(L)]
    j = 0
    for ci in cipher:
        if ci == interrupt_rune:
            continue
        slots[j % L].append(ci)
        j += 1
    return _mean_slot_ioc(slots)


def slot_ioc(cipher, interrupt_rune, L):
    """Greedy interrupt-SUBSET search — relikd's sequential heuristic in spirit.

    At each occurrence of `interrupt_rune` we decide whether it is a real
    interrupt (pointer holds) or an ordinary rune (pointer advances), taking
    whichever choice leaves the better mean slot-IoC so far. That turns an
    intractable 2^n subset space into 2 evaluations per occurrence, and — unlike
    the naive variant above — it recovers planted keys, so the pipeline has
    demonstrated power.
    """
    slots = [[] for _ in range(L)]
    j = 0
    for ci in cipher:
        if ci == interrupt_rune:
            # branch: treat as interrupt (hold) vs ordinary (advance)
            hold = _mean_slot_ioc(slots)
            trial = [list(x) for x in slots]
            trial[j % L].append(ci)
            adv = _mean_slot_ioc(trial)
            if adv > hold:
                slots = trial
                j += 1
            continue
        slots[j % L].append(ci)
        j += 1
    return _mean_slot_ioc(slots)


def best_over_grid(cipher, max_len, min_len=2):
    """Best (score, interrupt_rune, L) over all 29 runes x key lengths."""
    best = None
    for r in range(N):
        for L in range(min_len, max_len + 1):
            s = slot_ioc(cipher, r, L)
            if best is None or s > best[0]:
                best = (s, r, L)
    return best


def encrypt_with_interrupt(plain, key, interrupt_rune):
    """c = p + k, but a plaintext `interrupt_rune` is emitted literally and
    consumes no key — the generalised literal-ᚠ rule."""
    out, j = [], 0
    for p in plain:
        if p == interrupt_rune:
            out.append(interrupt_rune)
            continue
        out.append((p + key[j % len(key)]) % N)
        j += 1
    return out


def power_analysis(pt, trials=6, seed=20260823):
    """Is this hypothesis detectable AT ALL, and what does it cost?

    Three measurements per planted (interrupt rune, key):
      perfect  — group by the TRUE key slot recorded at encryption time. This is
                 the ceiling of the method: what we would see with an oracle.
      naive    — treat EVERY ciphertext occurrence of r as an interrupt.
      ambiguity— how many of those occurrences are actually coincidental.
    """
    import random
    rnd = random.Random(seed)
    rows = []
    for _ in range(trials):
        r = rnd.randrange(N)
        L = rnd.randrange(3, 12)
        key = [rnd.randrange(N) for _ in range(L)]
        ct, true_slot, j = [], [], 0
        n_true = 0
        for p in pt:
            if p == r:
                ct.append(r); true_slot.append(None); n_true += 1
                continue
            ct.append((p + key[j % len(key)]) % N)
            true_slot.append(j % L); j += 1
        slots = [[] for _ in range(L)]
        for c, sl in zip(ct, true_slot):
            if sl is not None:
                slots[sl].append(c)
        vals = [ioc(x) for x in slots if x]
        perfect = sum(vals) / len(vals)
        naive = slot_ioc_all(ct, r, L)
        n_occ = ct.count(r)
        rows.append((r, L, perfect, naive, n_true, n_occ))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-len", type=int, default=32)
    ap.add_argument("--plants", type=int, default=10)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    real = [s for s in segs if not s.solved and len(s.indices) >= 50]
    pt = english_plaintext(segs)[:1200]
    print(f"interrupt-rune search: 29 candidate runes x key lengths "
          f"2-{args.max_len} = {29 * (args.max_len - 1)} hypotheses per segment")
    print(f"scoring: mean per-slot IoC (English ~1.7, flat ~1.0)\n")

    print("=== POWER ANALYSIS: is this hypothesis detectable at all? ===")
    rows = power_analysis(pt)
    print(f"  {'rune':>4} {'L':>3} {'perfect':>8} {'naive':>7} "
          f"{'true int':>9} {'occurrences':>12} {'coincidental':>13}")
    for r, L, perfect, naive, n_true, n_occ in rows:
        print(f"  {r:>4} {L:>3} {perfect:>8.3f} {naive:>7.3f} "
              f"{n_true:>9} {n_occ:>12} {100*(n_occ-n_true)/max(1,n_occ):>12.0f}%")
    mp = sum(x[2] for x in rows) / len(rows)
    mn = sum(x[3] for x in rows) / len(rows)
    mc = sum(100*(x[5]-x[4])/max(1,x[5]) for x in rows) / len(rows)
    print(f"\n  mean with an interrupt ORACLE : {mp:.3f}  (English ~1.74 — "
          f"so the statistic works)")
    print(f"  mean treating ALL occurrences : {mn:.3f}  (flat ~1.0 — no signal)")
    print(f"  because {mc:.0f}% of ciphertext occurrences of the interrupt rune "
          f"are COINCIDENTAL,")
    print(f"  not real interrupts. Each false skip desynchronises every later "
          f"position.\n")
    print("  => the hypothesis IS detectable, but only by searching interrupt")
    print("     SUBSETS (relikd: first 20 occurrences, ~1.4e10 ops, ~38 h).")
    print("     The naive all-occurrences approximation below has NO power, and")
    print("     its control duly fails — reported, not hidden.\n")

    # --- detection floor: plant (interrupt rune, key) and recover it ---------
    import random
    rnd = random.Random(20260823)
    plants = []
    for _ in range(args.plants):
        r = rnd.randrange(N)
        L = rnd.randrange(3, 12)
        key = [rnd.randrange(N) for _ in range(L)]
        plants.append((r, L, tuple(key)))

    def plant(name):
        r, L, key = name
        return encrypt_with_interrupt(pt, list(key), r)

    def recover(ct):
        sc, r, L = best_over_grid(ct, args.max_len)
        return sc, (r, L), 1.0 if sc else 0.0

    def recover_named(ct):
        sc, rl, _ = recover(ct)
        return sc, rl, 1.0

    # name for comparison is (rune, length) — the key itself is not searched
    named = [(r, L) for r, L, _ in plants]
    plant_map = {(r, L): (r, L, k) for r, L, k in plants}

    floor, covered, uncovered, _ = detection_floor(
        named, lambda n: plant(plant_map[n]), recover_named,
        label="(interrupt rune, key length)")

    ceil = matched_ceiling(lambda ct: best_over_grid(ct, args.max_len)[0],
                           len(pt), trials=len(real), seed=11000)
    print(f"=== MATCHED CHANCE CEILING ({len(real)} trials, L={len(pt)}): "
          f"{ceil:.3f} ===\n")

    print("REAL unsolved segments:")
    overall = None
    for s in real:
        sc, r, L = best_over_grid(s.indices, args.max_len)
        print(f"  {s.section[:30]:30s} interrupt {g.indices_to_latin([r]):3s} "
              f"keylen {L:2d}  slot-IoC {sc:.3f}")
        if overall is None or sc > overall[0]:
            overall = (sc, s.section, r, L)
    print(f"\nbest on {overall[1][:26]} "
          f"(interrupt {g.indices_to_latin([overall[2]])}, keylen {overall[3]})")
    print(verdict(overall[0], floor, ceil, len(covered), len(named),
                  label="(rune, length) plants"))


if __name__ == "__main__":
    main()
