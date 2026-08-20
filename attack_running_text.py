"""Running-text key attack: test a real book (KJV) as the running key.

The doublet signature says a running key, if used, is combined with no-repeat
enforcement (key-skip). Brute-forcing a 3.16M-rune key at every start offset
with a full beam is infeasible, so we use two stages:

  1. COARSE SCAN (numpy): slide the whole key text past several short windows
     of each segment and score the implied plaintext p = c ∓ k with a dense
     trigram table. A window with no key-skip inside its scan head stays
     aligned, so the true offset — if the key is this text — surfaces near the
     top. Multiple windows per segment make this robust to the ~3% skips.
  2. CONFIRM (beam): at each window's top offsets, run the key-skip beam
     decoder (handles the desync) and score the decode with the trigram model.

A planted positive control (encrypt English with KJV at a known offset via
key-skip, then recover it) proves the pipeline actually finds a real hit, so
a negative on the true ciphertext is meaningful.

Usage: python3 attack_running_text.py [--key kjv] [--scan-head 28] [--step 26]
       [--conf-len 44] [--top 12] [--order 3] [--beam 200]
"""

import argparse
import math

import numpy as np

import gematria as g
from parse_lp import parse
from language_model import get_model
from attack_keyskip import beam_decode
from no_repeat_model import enc_key_skip
from doublet_sim import english_plaintext
import keytexts

N = g.N


def unigram_weights(model):
    w = np.full(N, math.log(0.5 / model.total))
    for gram, cnt in model.counts[1].items():
        if cnt > 0:
            w[gram[0]] = math.log(cnt / model.total)
    return w


def trigram_table(model):
    """Dense 29x29x29 log-score table for the coarse scan (float32, flat)."""
    T = np.empty((N, N, N), dtype=np.float32)
    for a in range(N):
        for b in range(N):
            for c in range(N):
                T[a, b, c] = model.logscore_next((a, b), c)
    return T.reshape(-1)


def coarse_scan(chead, K, Tflat, sign):
    """Trigram-scored offset scan over all key offsets. sign=-1: p=c-k;
    sign=+1: p=c+k. int16 rows + float32 table keep memory traffic low."""
    M = len(chead)
    L = len(K) - M
    NN = N * N
    Kw = K if sign > 0 else -K
    rows = [((int(chead[i]) + Kw[i:i + L]) % N).astype(np.int16)
            for i in range(M)]
    score = np.zeros(L, dtype=np.float32)
    for i in range(M - 2):
        idx = rows[i] * NN + rows[i + 1] * N + rows[i + 2]
        score += Tflat[idx]
    return score


def top_offsets(score, n):
    if len(score) <= n:
        return list(range(len(score)))
    idx = np.argpartition(score, -n)[-n:]
    return idx[np.argsort(score[idx])[::-1]].tolist()


def confirm(cipher_chunk, K, offset, sign, model, beam, max_skip):
    """Beam-decode a chunk of ciphertext with key starting at `offset`."""
    need = len(cipher_chunk) * (max_skip + 1) + 8
    Kslice = K[offset:offset + need].tolist()
    if len(Kslice) < need:
        return -99, []
    sc, dec = beam_decode(cipher_chunk, Kslice, 0, sign, model, beam, max_skip)
    return sc / max(1, len(cipher_chunk) - 1), dec


def best_over_windows(cidx, Karr, T, model, scan_head, step, conf_len, top,
                      beam, max_skip, max_windows=5):
    """Scan up to `max_windows` windows across a ciphertext, localise the key
    per window, and confirm each candidate. Robust to key-skip: a window with
    no skip in its scan head localises the key even if others are corrupted.
    Returns (best_trigram, sign, key_offset, ct_pos, decode)."""
    best = None
    n = len(cidx)
    starts = list(range(0, max(1, n - scan_head), step))[:max_windows]
    for w in starts:
        chead = np.array(cidx[w:w + scan_head], dtype=np.int16)
        if len(chead) < scan_head:
            break
        chunk = cidx[w:w + conf_len]
        for sign in (-1, +1):
            score = coarse_scan(chead, Karr, T, sign)
            for off in top_offsets(score, top):
                bl, dec = confirm(chunk, Karr, off, sign, model, beam, max_skip)
                if best is None or bl > best[0]:
                    best = (bl, sign, off, w, dec)
    return best


def run_key(name, Karr, segs, model, T, scan_head, step, conf_len, top,
            beam, max_skip, eng_ref):
    print(f"\n===== KEY TEXT: {name} ({len(Karr):,} runes) =====")
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]
    overall = None
    for s in unsolved:
        best = best_over_windows(s.indices, Karr, T, model, scan_head, step,
                                 conf_len, top, beam, max_skip)
        bl, sign, off, w, dec = best
        latin = g.indices_to_latin(dec)
        print(f"  {s.section[:38]:38s} {('c-k' if sign<0 else 'c+k')} "
              f"key@{off:>8} ctpos {w:>4} trigram {bl:.2f}")
        print(f"      {latin[:84]}")
        if overall is None or bl > overall[0]:
            overall = (bl, s.section)
    print(f"\n  best {name}: trigram {overall[0]:.2f} on {overall[1][:30]} "
          f"— English ~{eng_ref:.2f}, random ~-6.2 (a real hit lands near English)")
    return overall


def positive_control(Karr, model, T, scan_head, step, conf_len, top, beam,
                     max_skip):
    print("=== POSITIVE CONTROL: plant key text, try to recover ===")
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:150]
    # Plant near the middle of whatever key text this is, so the control works
    # for short texts (Blake, Liber AL) as well as the 3.16M-rune KJV.
    need = len(pt) * (max_skip + 1) + 64
    OFF = max(0, (len(Karr) - need) // 2)
    K_at = Karr[OFF:OFF + need].tolist()
    ct = enc_key_skip(pt, K_at)          # c = p + k  ==> decrypt sign = -1
    best = best_over_windows(ct, Karr, T, model, scan_head, step, conf_len,
                             top, beam, max_skip)
    bl, sign, off, w, dec = best
    # recovered plaintext at window w should match pt[w:]
    truth = pt[w:w + len(dec)]
    acc = sum(1 for a, b in zip(dec, truth) if a == b) / max(1, len(truth))
    ok = bl > -3.9 and acc > 0.8
    print(f"  best window: ct pos {w}, key offset {off} (planted {OFF}), "
          f"trigram {bl:.2f}, recovered {acc*100:.0f}% of that window")
    print(f"  control: {'PASS' if ok else 'FAIL'} "
          f"(pipeline {'finds' if ok else 'MISSES'} a real KJV key)\n")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default="kjv")
    ap.add_argument("--scan-head", type=int, default=28,
                    help="window length for the coarse offset scan")
    ap.add_argument("--step", type=int, default=24, help="window stride")
    ap.add_argument("--conf-len", type=int, default=44,
                    help="ciphertext chunk length for beam confirmation")
    ap.add_argument("--top", type=int, default=200)
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--beam", type=int, default=200)
    ap.add_argument("--max-skip", type=int, default=2)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(args.order)
    T = trigram_table(model)
    Karr = np.array(keytexts.get(args.key), dtype=np.int16)
    eng_ref = model.score_sequence(english_plaintext(segs)[:400])

    positive_control(Karr, model, T, args.scan_head, args.step, args.conf_len,
                     args.top, args.beam, args.max_skip)
    run_key(args.key, Karr, segs, model, T, args.scan_head, args.step,
            args.conf_len, args.top, args.beam, args.max_skip, eng_ref)


if __name__ == "__main__":
    main()
