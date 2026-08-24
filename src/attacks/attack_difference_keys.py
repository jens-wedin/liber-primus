"""§12 remainder: word keys and running-key texts on the DIFFERENCE stream.

§12 tested the cumulative/chained-cipher family `c[i] = c[i-1] + m[i]` by working
in difference space, `d[i] = c[i] - c[i-1]`: if the cipher is cumulative then d IS
the message stream m. It covered keyless, repeating-key Vigenere (period <= 40)
and prime/totient on d — all negative — and explicitly left two open:

  "Untested (lower prior): a running-key text or word-key-with-skip on the
   difference stream."

This closes both, with the controls §12 did not have (§31 found it has no matched
ceiling at all and its own controls never enable the no-repeat notch):

  WORD KEYS  : the Cicada vocabulary + common words, through the key-skip beam,
               applied to d instead of c.
  BOOK KEYS  : the candidate running-key texts, through the same coarse-scan +
               confirm pipeline as §6/§9, applied to d.

Rationale for the hypothesis: if `c[i] = c[i-1] + p[i] + k[i]`, then d = p + k and
every ordinary key attack should work on d — so a negative here closes the
cumulative variant of the word-key and book-key families in one pass.

Usage: python3 attack_difference_keys.py [--mode words|books] [--head 60]
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

import numpy as np

import gematria as g
import keytexts
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext
from no_repeat_model import enc_key_skip
from attack_vigenere_skip import attack_segment, load_key_words, CICADA_WORDS
from attack_running_text import trigram_table, best_over_windows
from controls import detection_floor, matched_ceiling, verdict, random_runes

N = g.N


def diff(ix):
    """d[i] = c[i] - c[i-1] mod 29 — the message stream of a cumulative cipher."""
    return [(ix[i] - ix[i - 1]) % N for i in range(1, len(ix))]


def run_words(segs, model, args):
    keys = load_key_words(args.nwords, 4, 16)
    real = [s for s in segs if not s.solved and len(s.indices) >= 50]
    print(f"WORD KEYS on the difference stream: {len(keys)} keys, "
          f"head {args.head}, key-skip <= {args.max_skip}\n")

    pt = english_plaintext(segs)[:args.head]
    kmap = dict(keys)
    plants = [n for n, _ in keys[:12]]

    def plant(name):
        k = kmap[name]
        reps = len(pt) * (args.max_skip + 1) // len(k) + 4
        return enc_key_skip(pt, k * reps)     # a planted d = p + k

    def recover(ct):
        sc, nm, sign, dec, _ = attack_segment(ct, keys, model, args.head,
                                              args.beam, args.max_skip)
        acc = sum(1 for a, b in zip(dec, pt) if a == b) / len(pt)
        return sc, nm, acc

    floor, covered, uncovered, _ = detection_floor(
        plants, plant, recover, label="word key")

    ceil = matched_ceiling(
        lambda ct: attack_segment(ct, keys, model, args.head, args.beam,
                                  args.max_skip)[0],
        args.head, trials=len(real), seed=9500, extra=4)
    print(f"=== MATCHED CHANCE CEILING ({len(real)} trials): {ceil:.2f} ===\n")

    overall = None
    for s in real:
        d = diff(s.indices)
        sc, nm, sign, dec, _ = attack_segment(d, keys, model, args.head,
                                              args.beam, args.max_skip)
        print(f"  {s.section[:30]:30s} key '{nm[:16]:16s}' "
              f"{'c-k' if sign < 0 else 'c+k'} {sc:6.2f}")
        if overall is None or sc > overall[0]:
            overall = (sc, s.section, nm, dec)
    print(f"\nbest on {overall[1][:26]} (key '{overall[2]}')")
    print(f"      {g.indices_to_latin(overall[3])[:76]}")
    print(verdict(overall[0], floor, ceil, len(covered), len(plants),
                  label="word keys"))


def run_books(segs, model, args):
    T = trigram_table(model)
    real = [s for s in segs if not s.solved and len(s.indices) >= 50]
    print(f"BOOK KEYS on the difference stream: {args.key}\n")
    K = np.array(keytexts.get(args.key), dtype=np.int16)

    # floor: plant a running key from this text into English, difference-style
    pt = english_plaintext(segs)[:args.length]
    off0 = len(K) // 3
    ct = [(pt[i] + int(K[(off0 + i) % len(K)])) % N for i in range(len(pt))]
    bl, sign, off, w, dec = best_over_windows(
        ct, K, T, model, args.scan_head, args.step, args.conf_len, args.top,
        args.beam, args.max_skip)
    acc = sum(1 for a, b in zip(dec, pt[w:]) if a == b) / max(1, len(dec))
    print(f"  floor control: planted offset {off0}, recovered {off} "
          f"score {bl:.2f}, {acc*100:.0f}% of its window "
          f"-> {'PASS' if abs(off - off0) < 64 else 'FAIL'}")
    floor = bl

    ceil = matched_ceiling(
        lambda c: best_over_windows(c, K, T, model, args.scan_head, args.step,
                                    args.conf_len, args.top, args.beam,
                                    args.max_skip)[0],
        args.length, trials=len(real), seed=9600)
    print(f"  matched ceiling ({len(real)} trials): {ceil:.2f}\n")

    overall = None
    for s in real:
        d = diff(s.indices)[:args.length]
        if len(d) < args.scan_head:
            continue
        bl, sign, off, w, dec = best_over_windows(
            d, K, T, model, args.scan_head, args.step, args.conf_len,
            args.top, args.beam, args.max_skip)
        print(f"  {s.section[:30]:30s} @{off:8d} "
              f"{'c-k' if sign < 0 else 'c+k'} {bl:6.2f}")
        if overall is None or bl > overall[0]:
            overall = (bl, s.section, off, dec)
    print(f"\nbest on {overall[1][:26]} (key offset {overall[2]})")
    print(f"      {g.indices_to_latin(overall[3])[:76]}")
    print(verdict(overall[0], floor, ceil, 1, 1, label="planted book key"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("words", "books"), default="words")
    ap.add_argument("--key", default="runepoem_oe")
    ap.add_argument("--nwords", type=int, default=400)
    ap.add_argument("--head", type=int, default=60)
    ap.add_argument("--beam", type=int, default=100)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--length", type=int, default=200)
    ap.add_argument("--scan-head", type=int, default=28)
    ap.add_argument("--step", type=int, default=24)
    ap.add_argument("--conf-len", type=int, default=44)
    ap.add_argument("--top", type=int, default=200)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(3)
    if args.mode == "words":
        run_words(segs, model, args)
    else:
        run_books(segs, model, args)


if __name__ == "__main__":
    main()
