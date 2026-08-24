"""Per-page / per-line key resets — the last untested rune-side idea (BACKLOG 9).

REPORT §5.3 flagged this years-deep in the backlog and it was never run, because
our vendored transcription bundles several .jpg pages into one segment and has no
line marks. rtkd/iddqd's transcription (vendored for the §23 cross-check) carries
explicit delimiters — `%` page, `/` line — so the structure is now available.

The hypothesis. Every whole-stream keystream attack has failed (§3, §4). If the
key pointer RESETS at each page (or each line), then no whole-stream attack could
ever work, however good the keystream guess: the effective unknown is only one
page/line long. This is the one structural variant that would explain the
uniform failure of §3 without requiring an unbreakable pad.

Three schedules, all reusing the SAME key material (no per-unit search freedom —
that would just overfit, as §33 showed):
  none    : one continuous pointer over the whole segment (= §3's baseline)
  reset0  : the pointer returns to K[0] at every unit boundary
  reset_i : unit i starts at K[i] (a "page-numbered" key)

x {page, line} units x {prime, totient, DIVINITY, FIRFUMFERENFE} streams
x both signs x {with, without} the §4 key-skip.

Control-validated through `controls.py`: each schedule is planted and must be
recovered (that is the detection floor), and the chance ceiling is drawn from an
independent length-matched null. Per §33, a verdict is only issued when coverage
is adequate — otherwise the run reports NO EVIDENCE rather than a false lead.

Usage: python3 attack_pagekey.py [--unit page|line] [--head 200]
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

import ciphers as c
import gematria as g
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext
from controls import detection_floor, matched_ceiling, verdict

N = g.N
RTKD = "download/rtkd_liber_primus_transcription.txt"


# --- structure from the rtkd transcription -----------------------------------

def rtkd_units(unit="page"):
    """[(page_index, [unit_rune_lists...])] for every page carrying runes."""
    text = open(RTKD, encoding="utf-8").read()
    out = []
    for pi, page in enumerate(text.split("%")):
        runes = [g.RUNE_TO_IDX[ch] for ch in page if ch in g.RUNE_SET]
        if not runes:
            continue
        if unit == "page":
            out.append((pi, [runes]))
        else:
            lines = []
            for ln in page.split("/"):
                r = [g.RUNE_TO_IDX[ch] for ch in ln if ch in g.RUNE_SET]
                if r:
                    lines.append(r)
            out.append((pi, lines))
    return out


def unsolved_pages(unit="page"):
    """rtkd pages whose runes sit inside our UNSOLVED stream.

    Decided empirically (by containment) rather than by page numbering, because
    the two sources number pages differently (LP1 filenames vs LP2 indices).
    """
    segs = parse("data/liber_primus.md")
    un = [i for s in segs if not s.solved and len(s.indices) >= 50
          for i in s.indices]
    hay = ",".join(map(str, un))
    keep = []
    for pi, units in rtkd_units(unit):
        flat = [x for u in units for x in u]
        probe = ",".join(map(str, flat[:40]))          # 40 runes pins it
        if probe and probe in hay:
            keep.append((pi, units))
    return keep


# --- keystreams ---------------------------------------------------------------

def streams(length):
    out = {}
    for name, gen in (("prime", c.prime_stream), ("totient", c.totient_stream)):
        it = gen()
        out[name] = [next(it) % N for _ in range(length)]
    for w in ("DIVINITY", "FIRFUMFERENFE"):
        ix = g.latin_to_indices(w)
        out[w] = [ix[i % len(ix)] for i in range(length)]
    return out


def key_positions(units, schedule, K):
    """Yield, per unit, the starting index into K."""
    pos, starts = 0, []
    for i, u in enumerate(units):
        if schedule == "none":
            starts.append(pos)
            pos += len(u)
        elif schedule == "reset0":
            starts.append(0)
        else:                                   # reset_i
            starts.append(i % max(1, len(K) - 64))
    return starts


def decode(units, K, schedule, sign, skip):
    """Decrypt each unit from its scheduled key start; `skip` applies the §4
    doublet-avoidance advance (pointer moves an extra step after a repeat)."""
    out = []
    for start, u in zip(key_positions(units, schedule, K), units):
        j, prev = start, None
        for ci in u:
            p = (ci + sign * K[j % len(K)]) % N
            j += 1
            if skip and prev is not None and ci == prev:
                j += 1
            out.append(p)
            prev = ci
    return out


def encode(units, K, schedule, sign, skip):
    """Inverse of `decode` along the identical pointer path (for planting)."""
    out, flat = [], [x for u in units for x in u]
    idx = 0
    for start, u in zip(key_positions(units, schedule, K), units):
        j, prev = start, None
        for _ in u:
            p = flat[idx]; idx += 1
            ci = (p - sign * K[j % len(K)]) % N
            j += 1
            if skip and prev is not None and ci == prev:
                j += 1
            out.append(ci)
            prev = ci
    return out


def build_grid():
    grid = []
    for sname in ("prime", "totient", "DIVINITY", "FIRFUMFERENFE"):
        for sched in ("none", "reset0", "reset_i"):
            for sign in (-1, +1):
                for skip in (False, True):
                    grid.append((sname, sched, sign, skip))
    return grid


def mech(m):
    s, sched, sign, skip = m
    return f"{s}/{sched}/{'c+k' if sign < 0 else 'c-k'}{'/skip' if skip else ''}"


def search(units, S, model):
    best = None
    for m in build_grid():
        sname, sched, sign, skip = m
        dec = decode(units, S[sname], sched, sign, skip)
        sc = model.score_sequence(dec)
        if best is None or sc > best[0]:
            best = (sc, m, dec)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", choices=("page", "line"), default="page")
    ap.add_argument("--head", type=int, default=200,
                    help="max runes per page analysed")
    args = ap.parse_args()

    model = get_model(3)
    segs = parse("data/liber_primus.md")
    eng = model.score_sequence(english_plaintext(segs)[:400])
    S = streams(4096)
    pages = unsolved_pages(args.unit)
    grid = build_grid()
    nunits = sum(len(u) for _, u in pages)
    print(f"unsolved rtkd pages: {len(pages)}; {args.unit} units: {nunits}; "
          f"grid: {len(grid)} mechanisms")
    print(f"English reference {eng:.2f}\n")
    if not pages:
        print("no unsolved pages matched — aborting.")
        return

    # --- detection floor: plant each schedule, must recover it ---------------
    pt_units = []
    ptf = english_plaintext(segs)
    k = 0
    for _, units in pages[:6]:
        block = []
        for u in units:
            block.append(ptf[k:k + len(u)]); k += len(u)
        pt_units.append(block)
    plant_units = [u for b in pt_units for u in b]
    names = [m for m in grid if m[1] != "none"]      # the new hypotheses

    def plant(m):
        sname, sched, sign, skip = m
        return encode(plant_units, S[sname], sched, sign, skip)

    def recover(ct):
        # re-chunk the ciphertext to the same unit shape, then search
        chunks, i = [], 0
        for u in plant_units:
            chunks.append(ct[i:i + len(u)]); i += len(u)
        sc, m, dec = search(chunks, S, model)
        flat = [x for u in plant_units for x in u]
        acc = sum(1 for a, b in zip(dec, flat) if a == b) / max(1, len(flat))
        return sc, m, acc

    floor, covered, uncovered, _ = detection_floor(
        names, plant, recover, label="reset schedule")

    # --- matched ceiling at the real analysed length -------------------------
    real_units = [u[:args.head] for _, units in pages for u in units]
    L = sum(len(u) for u in real_units)

    def score_random(seq):
        chunks, i = [], 0
        for u in real_units:
            chunks.append(seq[i:i + len(u)]); i += len(u)
        return search(chunks, S, model)[0]

    ceil = matched_ceiling(score_random, L, trials=13, seed=7700)
    print(f"=== MATCHED CHANCE CEILING (independent null, L={L}, 13 trials): "
          f"{ceil:.2f} ===\n")

    sc, m, dec = search(real_units, S, model)
    print(f"REAL unsolved text, per-{args.unit} key resets:")
    print(f"  best mechanism {mech(m)}  trigram {sc:.2f}")
    print(f"      {g.indices_to_latin(dec)[:76]}")
    print()
    print(verdict(sc, floor, ceil, len(covered), len(names),
                  label="reset schedules"))


if __name__ == "__main__":
    main()
