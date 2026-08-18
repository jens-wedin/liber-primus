"""Signature simulation: which cipher families reproduce the unsolved text's
statistical fingerprint?

Observed on the unsolved stream: IoC = 1.000 (flat/uniform) and doublet rate
= 0.66% (adjacent identical runes), far below the 3.45% (=1/29) a flat random
stream gives — a ~17sigma deficiency.

We synthesize an English-in-runes plaintext (from the solved pages), encrypt
it with each candidate family under random keys, and measure the resulting
IoC and doublet rate. A family is a viable hypothesis only if it can land
near (IoC 1.00, doublet 0.66%). Most cannot, which is the point: this filters
the search space before any brute force.

Analytic prediction worth stating up front: a **ciphertext-autokey** with lag
1 encrypts c[i] = p[i] + c[i-1] (a running cumulative sum mod 29). Then
c[i] == c[i+1]  iff  p[i+1] == 0, i.e. exactly when the *plaintext* rune is F.
So its doublet rate equals the plaintext F-frequency (a few percent, and low),
and cumulative sums mod 29 flatten toward uniform (IoC -> 1.0). That is
precisely the observed signature — so this simulation predicts ciphertext
autokey is the family most consistent with the data.
"""

import statistics
from collections import Counter

import ciphers as c
import gematria as g
from parse_lp import parse

N = g.N


def ioc(ix):
    n = len(ix)
    if n < 2:
        return 0.0
    counts = Counter(ix)
    return N * sum(v * (v - 1) for v in counts.values()) / (n * (n - 1))


def doublet_rate(ix):
    return sum(1 for a, b in zip(ix, ix[1:]) if a == b) / (len(ix) - 1)


def english_plaintext(segs):
    """Concatenate the solved pages' plaintext into one rune stream."""
    stream = []
    for s in segs:
        if not s.solved:
            continue
        if "Substitution with default" in s.key or s.key.startswith("-"):
            stream.extend(s.indices)
        elif "reversed Gematria" in s.key and "Shift 3" in s.key:
            stream.extend(c.shift(c.atbash(s.indices), 3))
    return stream


class LCG:
    """Deterministic PRNG (Date.now/random are unavailable and we want
    reproducibility). Standard Numerical Recipes constants."""
    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFF

    def next(self):
        self.s = (1664525 * self.s + 1013904223) & 0xFFFFFFFF
        return self.s

    def randint(self, n):
        return self.next() % n


# --- cipher families: each takes (plaintext indices, rng) -> ciphertext ------

def fam_otp(p, rng):
    return [(pi + rng.randint(N)) % N for pi in p]


def fam_vigenere(period):
    def f(p, rng):
        key = [rng.randint(N) for _ in range(period)]
        return [(pi + key[i % period]) % N for i, pi in enumerate(p)]
    return f


def fam_running_key(keytext):
    def f(p, rng):
        off = rng.randint(max(1, len(keytext) - len(p) - 1))
        return [(pi + keytext[(off + i) % len(keytext)]) % N
                for i, pi in enumerate(p)]
    return f


def fam_prime(p, rng):
    ks, gen = [], c.prime_stream()
    skip = rng.randint(200)
    for _ in range(skip):
        next(gen)
    for _ in range(len(p)):
        ks.append(next(gen) % N)
    return [(pi + ks[i]) % N for i, pi in enumerate(p)]


def fam_ciphertext_autokey(lag):
    def f(p, rng):
        primer = [rng.randint(N) for _ in range(lag)]
        c_out = []
        for i, pi in enumerate(p):
            k = primer[i] if i < lag else c_out[i - lag]
            c_out.append((pi + k) % N)
        return c_out
    return f


def fam_plaintext_autokey(lag):
    def f(p, rng):
        primer = [rng.randint(N) for _ in range(lag)]
        c_out = []
        for i, pi in enumerate(p):
            k = primer[i] if i < lag else p[i - lag]
            c_out.append((pi + k) % N)
        return c_out
    return f


def fam_norepeat_otp(p, rng):
    """OTP that resamples the key whenever it would create a doublet — a
    deliberate no-doublet construction, for comparison."""
    c_out = []
    for pi in p:
        while True:
            ci = (pi + rng.randint(N)) % N
            if not c_out or ci != c_out[-1]:
                break
        c_out.append(ci)
    return c_out


FAMILIES = {
    "plaintext (no cipher)": lambda p, rng: list(p),
    "OTP / long random key": fam_otp,
    "Vigenere period 5": fam_vigenere(5),
    "Vigenere period 13": fam_vigenere(13),
    "prime stream mod 29": fam_prime,
    "ciphertext-autokey lag 1": fam_ciphertext_autokey(1),
    "ciphertext-autokey lag 2": fam_ciphertext_autokey(2),
    "ciphertext-autokey lag 3": fam_ciphertext_autokey(3),
    "plaintext-autokey lag 1": fam_plaintext_autokey(1),
    "plaintext-autokey lag 2": fam_plaintext_autokey(2),
    "no-repeat OTP (rejection)": fam_norepeat_otp,
}

OBS_IOC = 1.000
OBS_DOUBLET = 0.0066


def main():
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)
    # running-key needs a second long English text; reuse plaintext doubled
    keytext = pt + pt
    FAMILIES["running key (English text)"] = fam_running_key(keytext)

    print(f"plaintext length {len(pt)} runes, "
          f"F-frequency {Counter(pt)[0]/len(pt)*100:.2f}%")
    print(f"\nOBSERVED unsolved: IoC {OBS_IOC:.3f}  doublet {OBS_DOUBLET*100:.2f}%\n")
    print(f"{'family':30s} {'IoC (mean±sd)':16s} {'doublet% (mean±sd)':20s} fit")

    trials = 40
    rows = []
    for name, fn in FAMILIES.items():
        iocs, dbs = [], []
        for t in range(trials):
            rng = LCG(0x1234 + t * 2654435761)
            ct = fn(pt, rng)
            iocs.append(ioc(ct))
            dbs.append(doublet_rate(ct))
        mi, si = statistics.mean(iocs), statistics.pstdev(iocs)
        md, sd = statistics.mean(dbs), statistics.pstdev(dbs)
        # distance from observed, in each metric's own natural scale
        di = abs(mi - OBS_IOC)
        dd = abs(md - OBS_DOUBLET)
        fit = "  <== MATCH" if (di < 0.03 and dd < 0.010) else ""
        rows.append((di + dd * 5, name, mi, si, md, sd, fit))
        print(f"{name:30s} {mi:.3f}±{si:.3f}     "
              f"{md*100:5.2f}±{sd*100:4.2f}%          {fit}")

    rows.sort()
    print(f"\nbest-fitting family: {rows[0][1]}")


if __name__ == "__main__":
    main()
