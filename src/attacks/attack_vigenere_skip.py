"""Short repeating-key (Vigenère) WITH the key-skip desync.

Gap this closes: the solved pages use short word keys (DIVINITY,
FIRFUMFERENFE) plus an interrupter (the literal ᚠ). Earlier tests covered
short repeating keys *without* desync (periodic-IoC scan, crib-dragging, all
negative) and the desync *only* with prime/totient streams (negative). The
one combination never tried is a **short word key repeated, plus the
doublet-avoidance key-skip** — precisely what the solved-page scheme, plus
the observed no-repeat signature (REPORT.md §4), together suggest.

Key space = the Cicada vocabulary plus the top-N English words (wordfreq),
transliterated to runes. A cheap straight-decode filter does NOT work here: a
short repeating key desynchronises after the first key-skip, so straight
decoding never aligns (verified — the true key ranks ~4000/14000). So we
key-skip beam-decode EVERY candidate key directly. This bounds the key space
to a few hundred thematic/common words (the solved-page keys — DIVINITY,
FIRFUMFERENFE — are that kind of word), which is honest coverage, not
exhaustive.

A planted positive control (encrypt English with a known word key + key-skip,
recover it) proves the pipeline finds a real word key.

Usage: python3 attack_vigenere_skip.py [--nwords 400] [--head 30]
       [--order 3] [--beam 100]
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
from language_model import get_model
from attack_keyskip import beam_decode
from no_repeat_model import enc_key_skip
from doublet_sim import english_plaintext
from mangle import mangle_words, selfcheck as mangle_selfcheck
import ciphers as c

N = g.N

CICADA_WORDS = [
    "DIVINITY", "CIRCUMFERENCE", "FIRFUMFERENFE", "INSTAR", "MOBIUS", "CABAL",
    "TOTIENT", "PRIMES", "SACRED", "WISDOM", "PILGRIM", "ENLIGHTENMENT",
    "PARABLE", "KOAN", "SHADOWS", "AETHEREAL", "BUFFERS", "OBSCURA",
    "MOURNFUL", "PRESERVATION", "ADHERENCE", "PROGRAM", "REALITY", "DECEPTION",
    "CONSUMPTION", "EMERGENCE", "INTUS", "WITHIN", "TRUTH", "SELF",
]


def load_key_words(nwords, min_len, max_len):
    import wordfreq
    seen, keys = set(), []
    for w in CICADA_WORDS:
        ix = tuple(g.latin_to_indices(w))
        if min_len <= len(ix) <= max_len and ix not in seen:
            seen.add(ix); keys.append((w, list(ix)))
    for w in wordfreq.top_n_list("en", nwords):
        if not (w.isalpha() and w.isascii()):
            continue
        ix = tuple(g.latin_to_indices(w))
        if min_len <= len(ix) <= max_len and ix not in seen:
            seen.add(ix); keys.append((w.upper(), list(ix)))
    return keys


def confirm(cipher_head, key, model, sign, beam, max_skip):
    reps = len(cipher_head) * (max_skip + 1) // len(key) + 4
    K = (key * reps)
    sc, dec = beam_decode(cipher_head, K, 0, sign, model, beam, max_skip)
    return sc / max(1, len(cipher_head) - 1), dec


def attack_segment(cidx, keys, model, head, beam, max_skip):
    chead = cidx[:head]
    best = None
    for name, key in keys:
        for sign in (-1, +1):
            bl, dec = confirm(chead, key, model, sign, beam, max_skip)
            if best is None or bl > best[0]:
                best = (bl, name, sign, dec, key)
    return best


def add_mangled(keys, base_words, min_len, max_len):
    """Extend `keys` with coined/mangled variants of the thematic base words,
    deduped against the words already present and held to the length bounds.
    Returns the number of variants added."""
    have = {tuple(k) for _, k in keys}
    added = 0
    for name, ix in mangle_words(base_words):
        t = tuple(ix)
        if min_len <= len(ix) <= max_len and t not in have:
            have.add(t)
            keys.append((name, ix))
            added += 1
    return added


def positive_control(keys, model, head, beam, max_skip):
    print("=== POSITIVE CONTROL: plant a word key + key-skip ===")
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:head]
    key = g.latin_to_indices("CIRCUMFERENCE")
    reps = len(pt) * (max_skip + 1) // len(key) + 4
    ct = enc_key_skip(pt, key * reps)      # c = p + k  ==> decrypt sign -1
    best = attack_segment(ct, keys, model, head, beam, max_skip)
    bl, name, sign, dec, _ = best
    acc = sum(1 for a, b in zip(dec, pt) if a == b) / len(pt)
    ok = name == "CIRCUMFERENCE" and acc > 0.8
    print(f"  recovered key '{name}' sign {sign}, trigram {bl:.2f}, "
          f"{acc*100:.0f}% of plaintext")
    print(f"  control: {'PASS' if ok else 'FAIL'}\n")
    return ok


def mangle_control(keys, model, head, beam, max_skip):
    """Prove the mangled key space has power: plant a *coined* key that is NOT
    a dictionary or base word (atbash of DIVINITY, a variant the generator
    emits), encrypt English under it + key-skip, and confirm the expanded key
    space recovers that exact key sequence."""
    print("=== MANGLE CONTROL: plant a COINED (non-dictionary) key ===")
    ok_gen = mangle_selfcheck()
    print(f"  generator ground truth (CIRCUMFERENCE->FIRFUMFERENFE): "
          f"{'PASS' if ok_gen else 'FAIL'}")
    from mangle import mangle
    planted = "PRESERVATION~atbash"
    coined = dict(mangle("PRESERVATION"))[planted]
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:head]
    reps = len(pt) * (max_skip + 1) // len(coined) + 4
    ct = enc_key_skip(pt, coined * reps)
    best = attack_segment(ct, keys, model, head, beam, max_skip)
    bl, name, sign, dec, key = best
    acc = sum(1 for a, b in zip(dec, pt) if a == b) / len(pt)
    ok = ok_gen and key == coined and acc > 0.8
    print(f"  planted '{planted}' ({g.indices_to_latin(coined)}); "
          f"recovered '{name}' sign {sign}, trigram {bl:.2f}, {acc*100:.0f}%")
    print(f"  control: {'PASS' if ok else 'FAIL'}\n")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nwords", type=int, default=400)
    ap.add_argument("--min-len", type=int, default=4)
    ap.add_argument("--max-len", type=int, default=16)
    ap.add_argument("--head", type=int, default=30)
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--beam", type=int, default=100)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--mangle", action="store_true",
                    help="also test coined/mangled variants of the thematic "
                         "words (the FIRFUMFERENFE=CIRCUMFERENCE family)")
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(args.order)
    keys = load_key_words(args.nwords, args.min_len, args.max_len)
    if args.mangle:
        added = add_mangled(keys, CICADA_WORDS, args.min_len, args.max_len)
        print(f"key space: {len(keys)} words "
              f"({added} coined/mangled variants added, len "
              f"{args.min_len}-{args.max_len})")
    else:
        print(f"key space: {len(keys)} words (len "
              f"{args.min_len}-{args.max_len})")
    eng_ref = model.score_sequence(english_plaintext(segs)[:400])

    if not positive_control(keys, model, args.head, args.beam, args.max_skip):
        raise SystemExit("control FAILED — aborting rather than reporting an "
                         "unvalidated negative (audit: controls must GATE).")
    if args.mangle:
        mangle_control(keys, model, args.head, args.beam, args.max_skip)

    print("REAL unsolved segments (short word key + key-skip):")
    overall = None
    for s in segs:
        if s.solved or len(s.indices) < 50:
            continue
        best = attack_segment(s.indices, keys, model, args.head,
                              args.beam, args.max_skip)
        bl, name, sign, dec, _ = best
        print(f"  {s.section[:40]:40s} key '{name}' {('c-k' if sign<0 else 'c+k')}"
              f" trigram {bl:.2f}")
        print(f"      {g.indices_to_latin(dec)[:84]}")
        if overall is None or bl > overall[0]:
            overall = (bl, s.section, name)
    print(f"\nbest: trigram {overall[0]:.2f} on {overall[1][:30]} "
          f"(key '{overall[2]}') — English ~{eng_ref:.2f} (a real hit lands there)")


if __name__ == "__main__":
    main()
