"""Shared statistical controls for every attack — the R5 systemic fix.

Why this module exists. The §28 self-audit found the same defects re-implemented
per script, twice in ways that could have HIDDEN a real break:

  1. **Arbitrary verdict thresholds.** Scripts judged a decode by "is it near the
     English trigram score (eng - 0.5)?". For BEAM decoders that is wrong: the
     beam adds a per-skip penalty and normalises by len-1, so a genuine break
     scores ~-4.0, not ~-3.4. `attack_magicsquare.py`'s own planted control
     recovered at -3.90 — *below* its own -3.88 threshold, i.e. the script would
     have called its own successful control "NO SIGNAL".
  2. **Ill-matched chance ceilings.** Ceilings took a max over 6 random draws
     while the real result is a max over 13 segments (biasing the ceiling low),
     and were computed at a fixed length while short segments were scored on
     fewer symbols (shorter sequences score higher).

The fix is to make the *calibrated* thing the default:

  `detection_floor(...)` — plant each hypothesis, recover it through the SAME
  pipeline, and use the minimum score of the hypotheses that actually
  self-recover as the detection threshold. Hypotheses that cannot be recovered
  even when planted are reported as NOT COVERED — no evidence either way —
  rather than silently counted as negatives.

  `matched_ceiling(...)` — a null with the same sequence LENGTH, the same number
  of TRIALS as the real run, and the same scoring function.

  `verdict(...)` — renders the standard conclusion from (best, floor, ceiling)
  so the wording cannot drift from the numbers.

Run `python3 controls.py` for the self-test.
"""

from doublet_sim import LCG

import gematria as g

N = g.N


# --- nulls --------------------------------------------------------------------

def random_runes(length, seed):
    rng = LCG(seed)
    return [rng.randint(N) for _ in range(length)]


def matched_ceiling(score_fn, length, trials, seed=900, extra=0):
    """Max score over `trials` uniform-random sequences of `length` runes.

    `trials` MUST equal the number of real trials the result is a max over
    (usually the number of unsolved segments) — otherwise the ceiling is biased
    low and real results appear to 'beat' it by chance. `length` MUST match the
    real sequence's length, because per-symbol scores rise as length falls.
    `extra` pads the drawn sequence (some pipelines consume a few runes).
    """
    best = None
    for t in range(trials):
        sc = score_fn(random_runes(length + extra, seed + t))
        best = sc if best is None else max(best, sc)
    return best


def shuffled(seq, seed):
    """A permutation of `seq` — the composition-matched null. Use this instead of
    uniform-random draws whenever the real data's symbol mix matters (Gematria
    sums, letter alphabets, prime-valued grids)."""
    rng = LCG(seed)
    s = list(seq)
    for i in range(len(s) - 1, 0, -1):
        j = rng.randint(i + 1)
        s[i], s[j] = s[j], s[i]
    return s


def shuffle_ceiling(score_fn, seq, trials, seed=1700):
    best = None
    for t in range(trials):
        sc = score_fn(shuffled(seq, seed + t * 7919))
        best = sc if best is None else max(best, sc)
    return best


# --- detection floor ----------------------------------------------------------

def detection_floor(names, plant_fn, recover_fn, acc_weak=0.9, label="hypothesis",
                    quiet=False):
    """Calibrate the threshold a REAL break would produce.

    names      : hypothesis identifiers to plant (e.g. key names, mechanisms)
    plant_fn   : name -> ciphertext, encrypting known plaintext under that
                 hypothesis with the scheme under test
    recover_fn : ciphertext -> (score, recovered_name, accuracy)
    acc_weak   : below this plaintext accuracy a recovery is flagged as a weak
                 decode (it still counts toward the floor — see below)

    IDENTIFIABILITY vs DECODE QUALITY are different things and must not be
    conflated (a bug in the first version of this module, and in the first fix to
    `attack_hints.py`):

      * **Identifiable** = when planted, the true hypothesis comes back RANKED
        FIRST. That is what decides whether we would ever SEE it, so it is what
        defines the floor — the score the run would show if the hypothesis were
        true. Imperfect plaintext accuracy does not change that score.
      * **Not identifiable** = a different hypothesis outranks the true one when
        planted. Then a real break would be invisible to this run, so it yields
        NO EVIDENCE either way — never count it as a negative.

    Returns (floor, covered, uncovered, rows). `floor` is the MINIMUM score over
    identifiable hypotheses. Below the floor is a supported negative; at or above
    it is a lead to inspect.
    """
    if not quiet:
        print(f"=== DETECTION FLOOR: plant each {label}, recover it, "
              f"read off the score a real break gives ===")
    covered, uncovered, weak, rows, floor = [], [], [], [], None
    for name in names:
        ct = plant_fn(name)
        score, got, acc = recover_fn(ct)
        identified = (got == name)
        rows.append((name, got, score, acc, identified))
        if not quiet:
            tag = ("identified" if identified else "NOT IDENTIFIABLE")
            if identified and acc < acc_weak:
                tag += " (weak decode)"
            print(f"  plant {str(name)[:28]:28s} -> '{str(got)[:28]:28s}' "
                  f"{score:6.2f} acc {acc*100:3.0f}%  {tag}")
        if identified:
            covered.append(name)
            floor = score if floor is None else min(floor, score)
            if acc < acc_weak:
                weak.append(name)
        else:
            uncovered.append(name)
    if not quiet:
        if floor is None:
            print("  !! NOTHING self-recovered — the pipeline has no demonstrated "
                  "power here; any 'negative' would be meaningless.")
        else:
            print(f"\n  FLOOR = {floor:.2f} (min over {len(covered)}/{len(names)} "
                  f"identifiable {label}s)")
        if weak:
            print(f"  weak decodes (identified, but <{acc_weak*100:.0f}% of "
                  f"plaintext): {', '.join(str(w) for w in weak[:8])}")
        if uncovered:
            print(f"  NOT COVERED ({len(uncovered)}): "
                  f"{', '.join(str(u) for u in uncovered[:8])}"
                  f"{' …' if len(uncovered) > 8 else ''}")
            print(f"  -> a real break with those would be INVISIBLE to this run; "
                  f"no evidence either way.")
        print()
    return floor, covered, uncovered, rows


# --- verdict ------------------------------------------------------------------

def verdict(best, floor, ceiling, n_covered=None, n_total=None,
            label="hypotheses"):
    """Standard conclusion text from the calibrated numbers."""
    out = [f"best real {best:.2f}"]
    if floor is not None:
        out.append(f"detection floor {floor:.2f} (what a real break scores)")
    if ceiling is not None:
        out.append(f"matched chance ceiling {ceiling:.2f}")
    line = "  " + "  vs  ".join(out)
    if floor is None:
        return line + "\n  -> INCONCLUSIVE: no demonstrated power."
    if best >= floor:
        return line + "\n  -> AT/ABOVE the break floor: possible real break — INSPECT."
    cov = ""
    if n_covered is not None and n_total is not None:
        cov = f", with demonstrated power for {n_covered}/{n_total} {label}"
    tail = ""
    if ceiling is not None and best <= ceiling:
        tail = " and at/below the matched chance ceiling"
    return (line + f"\n  -> {floor - best:.2f} BELOW the floor a genuine break "
            f"produces{tail}: NEGATIVE{cov}.")


# --- self-test ----------------------------------------------------------------

def _selftest():
    """Prove the two helpers behave: a planted hypothesis must be recovered (so
    the floor is real), and the ceiling must rise with more trials and with
    shorter sequences (the two biases the audit found)."""
    from parse_lp import parse
    from language_model import get_model
    from doublet_sim import english_plaintext
    from no_repeat_model import enc_key_skip
    from attack_vigenere_skip import attack_segment

    segs = parse("data/liber_primus.md")
    model = get_model(3)
    pt = english_plaintext(segs)[:30]
    keys = [("DIVINITY", g.latin_to_indices("DIVINITY")),
            ("MOBIUS", g.latin_to_indices("MOBIUS")),
            ("CIRCUMFERENCE", g.latin_to_indices("CIRCUMFERENCE"))]
    kmap = dict(keys)

    def plant(name):
        k = kmap[name]
        reps = len(pt) * 3 // len(k) + 4
        return enc_key_skip(pt, k * reps)

    def recover(ct):
        sc, nm, sign, dec, _ = attack_segment(ct, keys, model, 30, 100, 2)
        acc = sum(1 for a, b in zip(dec, pt) if a == b) / len(pt)
        return sc, nm, acc

    floor, cov, unc, _ = detection_floor([n for n, _ in keys], plant, recover,
                                         label="key")
    # a planted key must RANK FIRST; decode accuracy is reported separately
    ok_floor = floor is not None and len(cov) == 3
    print(f"  floor self-test: {'PASS' if ok_floor else 'FAIL'} "
          f"(identified {len(cov)}/3 planted keys)")

    score_fn = lambda ct: attack_segment(ct, keys, model, 30, 100, 2)[0]
    c6 = matched_ceiling(score_fn, 30, trials=6, extra=4)
    c13 = matched_ceiling(score_fn, 30, trials=13, extra=4)
    ok_trials = c13 >= c6            # monotone by construction (nested seeds)
    print(f"  ceiling vs trials: 6 draws {c6:.2f} -> 13 draws {c13:.2f} "
          f"(monotone by construction; the point is to USE the matched count)")

    short = matched_ceiling(score_fn, 20, trials=8, extra=4)
    long_ = matched_ceiling(score_fn, 60, trials=8, extra=4)
    ok_len = short >= long_
    print(f"  shorter sequences score higher: L=20 {short:.2f} vs L=60 "
          f"{long_:.2f} {'PASS' if ok_len else 'FAIL'}  (why ceilings must be "
          f"length-matched)")

    print()
    print(verdict(best=-4.38, floor=floor, ceiling=c13,
                  n_covered=len(cov), n_total=len(keys), label="keys"))
    return ok_floor and ok_trials and ok_len


if __name__ == "__main__":
    raise SystemExit(0 if _selftest() else 1)
