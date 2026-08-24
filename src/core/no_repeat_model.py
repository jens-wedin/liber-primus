"""Model the no-adjacent-repeat mechanism behind the doublet anomaly.

Established in the previous step (see REPORT.md §4):
- ciphertext IoC 1.000; first differences uniform on {1..28} with a sharp
  notch at 0; doublet rate 0.66% vs 3.45% random — a pure lag-1 effect;
- the suppression is equal within-word (0.63%) and across-word (0.80%), so
  the rule runs over the continuous rune stream, not per word.

This script asks: *which generative mechanism* produces exactly this
fingerprint (flat IoC, near-zero doublets, uniform ~0.66% leak), and what
does that mechanism imply for decryption?

Two mechanism classes preserve flat IoC while suppressing doublets, because
both enforce the no-repeat constraint at the cipher's OUTPUT stage:

  RE-ROLL:  c[i] = p[i] + k[i]; if c[i] == c[i-1], choose a different key
            value for position i (the keystream is a free/random pad).
  KEY-SKIP: c[i] = p[i] + K[j]; if that equals c[i-1], advance the pointer
            j into a FIXED keystream K (primes, totients, a text) and retry.
            This is an interrupter keyed on "would-be doublet".

They are statistically identical (both → flat IoC, ~0 doublets) but have
opposite consequences for an attacker:

  - RE-ROLL keeps the keystream in lock-step with position, so a *known*
    keystream is still testable position-by-position.
  - KEY-SKIP DESYNCHRONISES the keystream: every avoided doublet consumes an
    extra, invisible key value. This alone defeats crib-dragging and every
    periodicity test — which is exactly what we observe on the real text.

The residual 0.66% (86 rune-uniform doublets) is consistent either with
imperfect enforcement or with community transcription error (~0.66% over
~13k hand-copied runes is very plausible); both predict a rune-uniform,
boundary-independent leak, which is what the data shows.
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

from collections import Counter

import ciphers as c
import gematria as g
from parse_lp import parse
from doublet_sim import ioc, doublet_rate, english_plaintext, LCG

N = g.N


def diff(ix, lag=1):
    return [(ix[i] - ix[i - lag]) % N for i in range(lag, len(ix))]


# --- generative mechanisms ---------------------------------------------------

def enc_reroll(p, rng):
    out = []
    for pi in p:
        ci = (pi + rng.randint(N)) % N
        if out and ci == out[-1]:
            ci = (ci + 1 + rng.randint(N - 1)) % N  # any other value
        out.append(ci)
    return out


def enc_key_skip(p, K):
    """Fixed keystream K, pointer advances an extra step to dodge a doublet."""
    out, j = [], 0
    for pi in p:
        ci = (pi + K[j % len(K)]) % N
        j += 1
        while out and ci == out[-1]:
            ci = (pi + K[j % len(K)]) % N
            j += 1
        out.append(ci)
    return out


def enc_soft(p, K, p_keep, rng):
    """SOFT anti-repeat rule (Dukotah/cicada3301's model, N7). A would-be doublet
    is KEPT with probability p_keep and otherwise resolved to a uniform other
    value. p_keep=0 is the hard no-repeat rule (0 doublets); p_keep=1 is no rule.

    This is ORTHOGONAL to §11's finding: §11 fixed HOW a rejected doublet is
    resolved (uniform, not a deterministic bump); this fixes WHETHER it is
    rejected. The two compose, and the observed 0.66% doublet rate fits
    p_keep ~ 0.19 (see `fit_p_keep`), which reframes the 86 residual doublets as
    the filter's acceptance leak — signal — rather than transcription noise."""
    out = []
    for pi in p:
        ci = (pi + K[len(out) % len(K)]) % N
        if out and ci == out[-1] and (rng.next() / 0xFFFFFFFF) >= p_keep:
            ci = (ci + 1 + rng.randint(N - 1)) % N   # uniform other value
        out.append(ci)
    return out


def fit_p_keep(segments):
    """Fit the soft-rule acceptance probability from the observed doublet rate:
    p_keep = observed doublets / expected pre-filter collisions (pairs / 29).
    Returns (p_keep, observed, pairs)."""
    pairs = sum(len(s.indices) - 1 for s in segments)
    obs = sum(1 for s in segments for i in range(1, len(s.indices))
              if s.indices[i] == s.indices[i - 1])
    return obs / (pairs / N), obs, pairs


def add_dittography(ix, rng, rate):
    """Model the residual leak as transcription dittography: with probability
    `rate`, a rune is accidentally copied equal to its predecessor. This is
    the classic hand-copy slip and directly yields a rune-uniform doublet
    leak of ~rate."""
    out = []
    for x in ix:
        if out and rng.next() / 0xFFFFFFFF < rate:
            out.append(out[-1])
        else:
            out.append(x)
    return out


def signature(ix):
    d = diff(ix)
    dc = Counter(d)
    tot = len(d)
    nz = [dc.get(k, 0) for k in range(1, N)]
    en = sum(nz) / (N - 1)
    chi2 = sum((o - en) ** 2 / en for o in nz) if en else 0
    return ioc(ix), doublet_rate(ix) * 100, ioc(d), chi2


def main():
    segs = parse("data/liber_primus.md")
    un = [s for s in segs if not s.solved and len(s.indices) >= 50]
    allc = [i for s in un for i in s.indices]
    pt = english_plaintext(segs)

    print("target (real unsolved):")
    io, db, dio, chi2 = signature(allc)
    print(f"  c-IoC {io:.3f}  doublet {db:.2f}%  d-IoC {dio:.3f}  "
          f"d-nonzero-chi2 {chi2:.1f} (uniform ~27)\n")

    print("mechanism reproductions (English plaintext, matched length):")
    primes = []
    gen = c.prime_stream()
    for _ in range(len(pt) + 50):
        primes.append(next(gen) % N)

    for name, enc in [
        ("re-roll pad, no leak", lambda: enc_reroll(pt, LCG(7))),
        ("re-roll pad + 0.66% dittography",
         lambda: add_dittography(enc_reroll(pt, LCG(7)), LCG(3), 0.0066)),
        ("key-skip primes, no leak", lambda: enc_key_skip(pt, primes)),
        ("key-skip primes + 0.66% dittography",
         lambda: add_dittography(enc_key_skip(pt, primes), LCG(3), 0.0066)),
    ]:
        io, db, dio, chi2 = signature(enc())
        print(f"  {name:30s} c-IoC {io:.3f}  doublet {db:.2f}%  "
              f"d-IoC {dio:.3f}  chi2 {chi2:.1f}")

    # How many extra key values does key-skip consume? (the desync magnitude)
    skips = count_skips(pt, primes)
    print(f"\nkey-skip desync: over {len(pt)} runes the pointer advanced "
          f"{len(pt)+skips} times ({skips} hidden skips, "
          f"{skips/len(pt)*100:.1f}% extra) — this is why fixed-position "
          f"keystream attacks fail.")

    print("\nleak as transcription noise: 86 doublets / 12934 pairs = 0.66%. "
          "A 0.66% independent copy-error rate over hand-transcribed runes "
          "gives a rune-uniform, boundary-independent doublet leak — matching "
          "the observed distribution.")

    # --- SOFT-REJECTION reconciliation with Dukotah/cicada3301 (N7) ----------
    p_keep, obs, pairs = fit_p_keep(un)
    print(f"\nsoft-rejection fit (N7, vs Dukotah's ~0.18): the 86 doublets as a "
          f"SIGNAL, not noise.")
    print(f"  observed {obs} doublets / {pairs} pairs; expected pre-filter "
          f"collisions {pairs/N:.0f} -> fitted p_keep = {p_keep:.3f}")
    for pk in (0.0, round(p_keep, 2), 0.34):
        io, db, dio, chi2 = signature(enc_soft(pt, primes, pk, LCG(5)))
        tag = ("hard no-repeat" if pk == 0 else
               "fitted" if abs(pk - round(p_keep, 2)) < 1e-9 else "no rule/29")
        print(f"  p_keep={pk:.2f} ({tag:14s}) c-IoC {io:.3f}  doublet {db:.2f}%  "
              f"d-chi2 {chi2:.1f}")
    print("  => a soft rule that KEEPS a would-be doublet w.p. ~0.19 (and "
          "resolves the rest UNIFORMLY, per §11) reproduces flat IoC AND the "
          "0.66% rate. This is ORTHOGONAL to §11 (which fixed the resolution "
          "distribution), and it makes the 86 doublets the filter's acceptance "
          "leak — agreeing with §23's 'real doublets favoured'.")


def count_skips(p, K):
    j, skips = 0, 0
    out = []
    for pi in p:
        ci = (pi + K[j % len(K)]) % N
        j += 1
        while out and ci == out[-1]:
            ci = (pi + K[j % len(K)]) % N
            j += 1
            skips += 1
        out.append(ci)
    return skips


if __name__ == "__main__":
    main()
