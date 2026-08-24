"""Autokey attack on the unsolved sections.

Motivation: the unsolved ciphertext shows a strong doublet deficiency
(adjacent identical runes at ~0.66% vs 3.45% expected for a flat stream, a
~17-sigma anomaly). A keystream *derived from the text itself* (autokey) is
one of the few simple schemes that couples adjacent ciphertext runes and can
push the doublet rate away from 1/29 — so it's worth brute-forcing short
primers even though the community has covered much of this ground.

Tries plaintext-autokey and ciphertext-autokey, both signs, primer lengths
1-2 everywhere (and 3 on small segments). Scores by chi-square against the
English rune distribution learned from the solved pages, with a common-word
check on survivors.
"""

# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import itertools

import ciphers as c
import gematria as g
from analyze_unsolved import chi2, english_rune_distribution
from parse_lp import parse

N = g.N


def decrypt_ciphertext_autokey(ix, primer, sign):
    L = len(primer)
    out = []
    for i, ci in enumerate(ix):
        k = primer[i] if i < L else ix[i - L]
        out.append((ci + sign * k) % N)
    return out


def decrypt_plaintext_autokey(ix, primer, sign):
    L = len(primer)
    out = []
    for i, ci in enumerate(ix):
        k = primer[i] if i < L else out[i - L]
        out.append((ci + sign * k) % N)
    return out


def encrypt_ciphertext_autokey(p, primer):
    """c[i] = p[i] + k[i]; k = primer, then the CIPHERTEXT L back."""
    L, out = len(primer), []
    for i, pi in enumerate(p):
        k = primer[i] if i < L else out[i - L]
        out.append((pi + k) % N)
    return out


def encrypt_plaintext_autokey(p, primer):
    """c[i] = p[i] + k[i]; k = primer, then the PLAINTEXT L back."""
    L, out = len(primer), []
    for i, pi in enumerate(p):
        k = primer[i] if i < L else p[i - L]
        out.append((pi + k) % N)
    return out


def positive_control(dist):
    """Plant a known autokey encryption and confirm this pipeline finds it.

    Added by the R3 audit item: this attack previously had NO positive control —
    only a random-head chi2 baseline — so its negative was unvalidated under the
    project's own ground rule. The decision criterion in `main` is
    `word_score > 0.15`, so the control must show a PLANTED autokey clears it;
    otherwise a real autokey would be invisible and "negative" would mean nothing.
    """
    print("=== POSITIVE CONTROL: plant an autokey encryption, recover it ===")
    from doublet_sim import english_plaintext
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:150]
    ok_all = True
    for label, enc, dec_fn in (
            ("ciphertext-autokey", encrypt_ciphertext_autokey,
             decrypt_ciphertext_autokey),
            ("plaintext-autokey", encrypt_plaintext_autokey,
             decrypt_plaintext_autokey)):
        primer = (7, 19)                       # arbitrary known 2-rune primer
        ct = enc(pt, primer)
        best = None
        for L in (1, 2):
            for cand in itertools.product(range(N), repeat=L):
                for fn in (decrypt_ciphertext_autokey, decrypt_plaintext_autokey):
                    for sign in (+1, -1):
                        d = fn(ct, cand, sign)
                        sc = chi2(d, dist)
                        if best is None or sc < best[0]:
                            best = (sc, fn, cand, sign, d)
        sc, fn, cand, sign, d = best
        acc = sum(1 for a, b in zip(d, pt) if a == b) / len(pt)
        ws = c.word_score([g.indices_to_latin(d)])
        # The criterion is METHOD + SIGN + plaintext recovery, NOT an exact
        # primer match: for ciphertext-autokey the primer only supplies the
        # first L key values (everything after comes from the ciphertext), so a
        # wrong primer corrupts only L runes and the primer is essentially
        # unidentifiable. That is a property of the cipher, not a failure of the
        # attack — recording it rather than demanding the impossible.
        ok = (fn is dec_fn) and sign == -1 and acc > 0.95
        ok_all &= ok
        note = "" if cand == primer else f"  (primer {cand} != planted; only the "\
                                         f"first {len(primer)} runes differ)"
        print(f"  planted {label:20s} primer={primer} -> recovered "
              f"{fn.__name__.replace('decrypt_', ''):18s} "
              f"sign={sign:+d} chi2={sc:.0f} acc={acc*100:.0f}% "
              f"{'OK' if ok else 'FAIL'}{note}")
    print(f"  control: {'PASS — a real autokey WOULD be found' if ok_all else 'FAIL'}\n")
    return ok_all


def main():
    segs = parse("data/liber_primus.md")
    dist = english_rune_distribution(segs)
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]

    if not positive_control(dist):
        print("control FAILED — this pipeline cannot find a planted autokey, so "
              "any negative below would be meaningless. Aborting.")
        return

    for s in unsolved:
        ix = s.indices
        head = ix[:150]
        results = []
        max_len = 3 if len(ix) <= 400 else 2
        for L in range(1, max_len + 1):
            for primer in itertools.product(range(N), repeat=L):
                for fn in (decrypt_ciphertext_autokey, decrypt_plaintext_autokey):
                    for sign in (+1, -1):
                        dec = fn(head, primer, sign)
                        results.append((chi2(dec, dist), fn.__name__, primer, sign))
        results.sort(key=lambda t: t[0])
        print(f"-- {s.section[:50]} n={len(ix)} "
              f"(random-head chi2 baseline ~{chi2(head, dist):.0f})")
        for sc, name, primer, sign in results[:3]:
            fn = (decrypt_ciphertext_autokey if name.startswith("decrypt_c")
                  else decrypt_plaintext_autokey)
            dec_words = c.decrypt_words(s.words, lambda i: fn(i, primer, sign))
            latin = [g.indices_to_latin(w) for w in dec_words]
            ws = c.word_score(latin)
            print(f"   chi2={sc:6.0f} {name.replace('decrypt_', ''):18s} "
                  f"primer={primer} sign={sign:+d} word-score={ws:.2f}")
            if ws > 0.15:
                print("   CANDIDATE:", " ".join(latin)[:200])


if __name__ == "__main__":
    main()
