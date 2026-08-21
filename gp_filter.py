"""P2.5 — a GP-sum plausibility filter (tie-breaker for candidate decrypts).

§18 found the solved parable plaintext carries the signature: two ADJACENT
prime-length rune-runs whose Gematria-Primus sums hit 3301 and 1033 (with a ±2
literal-ᚠ knob). §18's base-rate control also showed a *single* themed hit is not
rare — so the only discriminating quantity is the **conjunction** (both themed
totals, adjacent, prime lengths). This builds that detector and control-validates
it: it must FIRE on the parable plaintext and stay QUIET on random text of the
same length. If it discriminates, it is a usable (weak) tie-breaker to fold into
future attacks beside the n-gram English score; if not, we say so.

Usage: python3 gp_filter.py
"""

import gematria as g
from parse_lp import parse
from doublet_sim import english_plaintext, LCG

P = g.IDX_TO_PRIME
N = g.N
TARGETS = (3301, 1033)
SLACK = 2                      # the literal-ᚠ (GP value 2) ± knob


def is_prime(n):
    return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))


def prime_lengths(lo=5, hi=80):
    return [n for n in range(lo, hi) if is_prime(n)]


def themed_runs(pt, target, lengths):
    """(start, length) of prime-length windows whose GP sum is within SLACK of
    target. Uses a prefix-sum over the GP values."""
    gpv = [P[i] for i in pt]
    pref = [0] * (len(gpv) + 1)
    for i, v in enumerate(gpv):
        pref[i + 1] = pref[i] + v
    out = []
    for ln in lengths:
        for a in range(0, len(gpv) - ln + 1):
            if abs((pref[a + ln] - pref[a]) - target) <= SLACK:
                out.append((a, ln))
    return out


def signature_count(pt, lengths):
    """Number of ADJACENT (3301-run, 1033-run) pairs, in either order, that abut
    within the ±SLACK boundary tolerance (one run ends ~where the next begins)."""
    r3301 = themed_runs(pt, 3301, lengths)
    r1033 = themed_runs(pt, 1033, lengths)
    end3301 = {a + ln for a, ln in r3301}
    start3301 = {a for a, ln in r3301}
    cnt = 0
    for a, ln in r1033:
        # a 1033-run immediately after a 3301-run, or immediately before one
        if any(abs((a) - e) <= SLACK for e in end3301):
            cnt += 1
        elif any(abs((a + ln) - s) <= SLACK for s in start3301):
            cnt += 1
    return cnt


def main():
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)             # solved plaintext (contains §18 parable)
    lengths = prime_lengths()
    n = len(pt)
    print(f"solved plaintext: {n} runes; prime run-lengths {lengths[0]}..{lengths[-1]}")

    print("\n=== CONTROL: fire on the parable, quiet on random? ===")
    real = signature_count(pt, lengths)
    print(f"  solved plaintext (has the §18 3301+1033 signature): "
          f"count = {real}")
    counts = []
    for d in range(200):
        rng = LCG(2000 + d)
        rp = [rng.randint(N) for _ in range(n)]
        counts.append(signature_count(rp, lengths))
    mean = sum(counts) / len(counts)
    hi = sorted(counts)[int(len(counts) * 0.95)]
    frac0 = sum(1 for c in counts if c == 0) / len(counts)
    print(f"  random plaintext (n={n}): mean {mean:.2f}, 95th pct {hi}, "
          f"P(count=0) = {frac0*100:.0f}%")
    p_ge_real = sum(1 for c in counts if c >= real) / len(counts)
    print(f"  P(random >= {real}) = {p_ge_real*100:.1f}%")

    if real > hi and p_ge_real < 0.05:
        print("  -> DISCRIMINATES: the parable signature is rare under random "
              "text. Usable as a weak tie-breaker beside the n-gram score.")
    else:
        print("  -> does NOT cleanly discriminate at this length/tolerance: the "
              "adjacent-conjunction still arises in random text often enough that "
              "the filter is at best a very soft prior. Consistent with §18's "
              "verdict that the GP-sum signal is weak on its own.")

    print("\nUse: as a TIE-BREAKER only — add a small bonus to a candidate decrypt "
          "whose signature count exceeds the random 95th percentile; never as the "
          "primary signal (a real break must first read as English).")


if __name__ == "__main__":
    main()
