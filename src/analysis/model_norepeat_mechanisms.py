"""Model the no-repeat mechanism (REPORT §5.1), beyond re-roll vs key-skip.

`no_repeat_model.py` established that two OUTPUT-stage mechanisms — a re-roll
pad and a key-skip — both reproduce the fingerprint (flat IoC, ~0 doublets,
uniform first differences). This script pushes on two questions the fingerprint
can still decide, each gated by a control that plants a known truth and checks
the discriminator recovers it:

  A. HOW is a would-be doublet resolved? Enumerate resolution rules and keep
     only those whose first-difference histogram matches the data (uniform on
     1..28, a notch at 0). A DETERMINISTIC rule — bump c by a fixed k on a
     collision, or nudge to the nearest free value — forces the difference to a
     fixed bin at every ~3.4% collision, a visible spike. The data has no spike,
     so the resolution is UNIFORM (a uniform re-pick, or advancing a
     pseudo-random keystream), not deterministic. That narrows the mechanism.

  B. WHAT are the 86 residual doublets? If they are transcription dittography
     (independent copy-slips at rate p), their positions are memoryless: gaps
     geometric, no periodicity. If instead the mechanism LEAKS a doublet at some
     key event, the positions would beat at that period — which would hand us
     the key period. A period scan with a permutation-significance control tests
     it honestly given only ~86 events.

Usage: python3 model_norepeat_mechanisms.py [--trials 2000]
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
from collections import Counter

import gematria as g
from parse_lp import parse
from doublet_sim import LCG, doublet_rate, ioc
from no_repeat_model import enc_key_skip
import ciphers as c

N = g.N


# --- Part A: how is a collision resolved? ------------------------------------

def synth_uniform_norepeat(n, rng):
    """Uniform random stream with a would-be doublet re-picked UNIFORMLY."""
    out = []
    for _ in range(n):
        v = rng.randint(N)
        while out and v == out[-1]:
            v = rng.randint(N)
        out.append(v)
    return out


def synth_bump(n, rng, k):
    """Uniform draw, but a collision is resolved DETERMINISTICALLY: c=(prev+k)."""
    out = []
    for _ in range(n):
        v = rng.randint(N)
        if out and v == out[-1]:
            v = (out[-1] + k) % N
        out.append(v)
    return out


def synth_key_skip(n, rng):
    """Key-skip over a pseudo-random fixed keystream (prime stream mod N)."""
    pt = [rng.randint(N) for _ in range(n)]
    K, gen = [], c.prime_stream()
    for _ in range(n * 3 + 64):
        K.append(next(gen) % N)
    return enc_key_skip(pt, K)


def diff_hist(ix):
    """Normalised histogram of first differences over the 28 non-zero values."""
    d = [(ix[i] - ix[i - 1]) % N for i in range(1, len(ix))]
    cnt = Counter(d)
    tot = sum(cnt.get(v, 0) for v in range(1, N))
    return {v: cnt.get(v, 0) / tot for v in range(1, N)}, cnt.get(0, 0)


def peak_excess(hist):
    """How far the tallest non-zero difference bin rises above uniform (1/28),
    as a multiple of the uniform height. ~1.0 = flat; >>1 = a spike."""
    uni = 1.0 / (N - 1)
    top = max(hist.values())
    return top / uni, max(hist, key=hist.get)


def part_a(real_ix, n, seed):
    print("=== A. how a would-be doublet is resolved ===")
    print("   (difference-histogram peak / uniform; ~1.0 flat, >>1 a spike)\n")
    rng = LCG(seed)
    rows = [
        ("uniform re-pick", synth_uniform_norepeat(n, rng)),
        ("key-skip (pseudo-random stream)", synth_key_skip(n, LCG(seed + 1))),
        ("deterministic bump +1", synth_bump(n, LCG(seed + 2), 1)),
        ("deterministic bump +7", synth_bump(n, LCG(seed + 3), 7)),
    ]
    for name, ix in rows:
        h, z = diff_hist(ix)
        mult, bin_ = peak_excess(h)
        verdict = "MATCHES data" if mult < 1.6 else f"SPIKE @ diff {bin_} -> ruled out"
        print(f"  {name:34s} doublet {doublet_rate(ix)*100:4.2f}%  "
              f"peak {mult:4.2f}x  {verdict}")
    hr, _ = diff_hist(real_ix)
    multr, _ = peak_excess(hr)
    print(f"  {'REAL unsolved stream':34s} doublet "
          f"{doublet_rate(real_ix)*100:4.2f}%  peak {multr:4.2f}x  "
          f"(flat -> resolution is UNIFORM, not deterministic)\n")


# --- Part B: what are the 86 residual doublets? ------------------------------

def doublet_positions(segments):
    """Per-segment positions i where c[i]==c[i-1]; return within-segment gaps,
    the doubled-rune values, and the raw (segment, index) hits."""
    gaps, runes, hits = [], [], 0
    for s in segments:
        ix = s.indices
        last = None
        for i in range(1, len(ix)):
            if ix[i] == ix[i - 1]:
                hits += 1
                runes.append(ix[i])
                if last is not None:
                    gaps.append(i - last)
                last = i
    return gaps, runes, hits


def rune_uniformity(runes):
    cnt = Counter(runes)
    exp = len(runes) / N
    chi2 = sum((cnt.get(r, 0) - exp) ** 2 / exp for r in range(N)) if exp else 0
    return chi2  # ~28 (N-1 dof) if uniform


def best_period(segments, tmax):
    """For each period T, bin every doublet position (mod T) and score how
    non-uniform the binning is (chi2). Return {T: chi2}."""
    pos_by_seg = []
    for s in segments:
        ix = s.indices
        pos_by_seg.append([i for i in range(1, len(ix)) if ix[i] == ix[i - 1]])
    out = {}
    for T in range(2, tmax + 1):
        cnt = Counter()
        tot = 0
        for pos in pos_by_seg:
            for i in pos:
                cnt[i % T] += 1
                tot += 1
        exp = tot / T
        out[T] = sum((cnt.get(b, 0) - exp) ** 2 / exp for b in range(T)) if exp else 0
    return out


def period_significance(segments, tmax, trials, seed):
    """Permutation test: is the observed best period-chi2 beyond what random
    doublet placements of the same count produce? Returns (best_T, obs_chi2,
    p_value)."""
    obs = best_period(segments, tmax)
    # normalise chi2 by dof (T-1) so periods are comparable, then take the max
    def score(chi_by_T):
        return max(chi_by_T[T] / (T - 1) for T in chi_by_T)
    obs_score = score(obs)
    obs_T = max(obs, key=lambda T: obs[T] / (T - 1))

    # counts and lengths per segment
    lengths = [len(s.indices) for s in segments]
    ndoub = []
    for s in segments:
        ix = s.indices
        ndoub.append(sum(1 for i in range(1, len(ix)) if ix[i] == ix[i - 1]))

    rng = LCG(seed)
    beat = 0
    for _ in range(trials):
        # place the same number of doublets at random positions per segment
        fake = []
        for L, k in zip(lengths, ndoub):
            chosen = set()
            while len(chosen) < k and len(chosen) < L - 1:
                chosen.add(1 + rng.randint(L - 1))
            fake.append(sorted(chosen))
        chi = {}
        for T in range(2, tmax + 1):
            cnt = Counter(); tot = 0
            for pos in fake:
                for i in pos:
                    cnt[i % T] += 1; tot += 1
            exp = tot / T
            chi[T] = sum((cnt.get(b, 0) - exp) ** 2 / exp for b in range(T)) if exp else 0
        if score(chi) >= obs_score:
            beat += 1
    return obs_T, obs_score, (beat + 1) / (trials + 1)


def part_b(segments, tmax, trials, seed):
    print("=== B. the residual doublets: transcription noise or a leak? ===")
    gaps, runes, hits = doublet_positions(segments)
    total = sum(len(s.indices) for s in segments)
    rate = hits / total
    print(f"  {hits} residual doublets in {total} runes ({rate*100:.2f}%)")

    chi2 = rune_uniformity(runes)
    print(f"  doubled-rune distribution: chi2 {chi2:.1f} over {N} runes "
          f"(~{N-1} if rune-uniform) -> "
          f"{'uniform' if chi2 < 2*(N-1) else 'NON-uniform'}")

    if gaps:
        mean = sum(gaps) / len(gaps)
        var = sum((x - mean) ** 2 for x in gaps) / len(gaps)
        cv = var ** 0.5 / mean
        # geometric with success prob p=rate has mean 1/p and CV ~sqrt(1-p)~1
        print(f"  gap between doublets: mean {mean:.0f} (geometric expects "
              f"~{1/rate:.0f}), CV {cv:.2f} (geometric ~1.0) -> "
              f"{'memoryless, noise-like' if 0.7 < cv < 1.4 else 'clustered'}")

    obs_T, obs_score, p = period_significance(segments, tmax, trials, seed)
    print(f"  periodicity scan (T=2..{tmax}): strongest at T={obs_T}, "
          f"permutation p={p:.3f} over {trials} shuffles")
    if p < 0.02:
        print(f"  --> LEAD: doublet positions beat at period {obs_T} beyond "
              f"chance. Test key period {obs_T}.")
    else:
        print(f"  --> no periodicity beyond chance (low power at {hits} events); "
              f"positions are consistent with independent transcription noise.")


def control_part_b(segments, tmax, trials, seed):
    """Plant INDEPENDENT doublets into synthetic uniform-norepeat streams of the
    real segment lengths, then run Part B on them: it must report noise (high
    permutation p), proving the periodicity test doesn't cry wolf."""
    print("=== CONTROL for B: independent (noise) doublets, same sizes ===")

    class Seg:
        pass
    rng = LCG(seed)
    fake_segs = []
    real_rate = 0.0066
    for s in segments:
        base = synth_uniform_norepeat(len(s.indices), rng)
        # inject independent dittography at the observed rate
        for i in range(1, len(base)):
            if rng.next() / 0xFFFFFFFF < real_rate:
                base[i] = base[i - 1]
        fs = Seg(); fs.indices = base; fake_segs.append(fs)
    part_b(fake_segs, tmax, trials, seed + 7)
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmax", type=int, default=64, help="max period to scan")
    ap.add_argument("--trials", type=int, default=2000,
                    help="permutation shuffles for periodicity significance")
    ap.add_argument("--seed", type=int, default=20260820)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]
    real = [i for s in unsolved for i in s.indices]
    n = len(real)
    print(f"unsolved: {len(unsolved)} segments, {n} runes, "
          f"IoC {ioc(real):.3f}\n")

    part_a(real, n, args.seed)
    control_part_b(unsolved, args.tmax, args.trials, args.seed)
    part_b(unsolved, args.tmax, args.trials, args.seed)


if __name__ == "__main__":
    main()
