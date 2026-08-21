"""P1.1 — the literal-ᚠ rule as a keystream INTERRUPTER on the unsolved pages.

The solved pages use short keys/streams + the **literal-ᚠ rule**: a plaintext F
is written as an unencrypted ᚠ and consumes NO key value (the pointer holds).
`validate_solved.py` proves this for the solved pages. But NO unsolved-page
attack has ever modelled it: every keystream attack (prime/totient §3,
word/key-skip §7, running keys §6/§9) advanced the key pointer once per rune.

Why this is new coverage, not a rehash of key-skip (§4/attack_keyskip):
  the key-skip beam advances the pointer by 1, 2 or 3 each rune — a FORWARD
  desync. The literal-ᚠ rule advances it by **0** at a ciphertext ᚠ (the pointer
  HOLDS) — a backward desync the key-skip beam cannot express. On decryption
  every ciphertext ᚠ is ambiguous: it is either a literal F (hold, plaintext=F)
  or an ordinary rune that happened to encrypt to ᚠ (advance). We beam over that
  binary choice at each ᚠ, scored by the English trigram model.

Two variants per keystream/sign:
  PURE   : pointer advances 1 per non-ᚠ rune; at each ᚠ, branch {hold F, advance}.
           This is the EXACT solved-page scheme (word key/stream + literal-ᚠ).
  +SKIP  : additionally allow the doublet-avoidance key-skip (0..max_skip extra)
           on the advance branch — literal-ᚠ AND the §4 mechanism together.

Control-validated: plant English (which contains real Fs) encrypted with a known
keystream + the literal-ᚠ rule, and confirm the ᚠ-aware beam recovers it AND the
literal-F positions; a chance ceiling on random text bounds the search. A genuine
break lands near the English trigram (~-3.4); the ceiling is where gibberish sits.

Usage: python3 attack_literal_f.py [--head 80] [--beam 150] [--draws 6]
"""

import argparse
import math

import gematria as g
import ciphers as c
from parse_lp import parse
from language_model import get_model
from doublet_sim import english_plaintext, LCG
from attack_vigenere_skip import CICADA_WORDS
from controls import detection_floor, matched_ceiling, verdict

N = g.N
F = g.latin_to_indices("F")[0]          # ᚠ == rune index 0
SKIP_PEN = math.log(0.03)


# --- keystream construction --------------------------------------------------

def materialize(name, length):
    if name == "prime":
        it = c.prime_stream()
        return [next(it) % N for _ in range(length)]
    if name == "totient":
        it = c.totient_stream()
        return [next(it) % N for _ in range(length)]
    raise ValueError(name)


def word_key(word, length):
    ix = g.latin_to_indices(word)
    return [ix[i % len(ix)] for i in range(length)]


# --- encryption with the literal-ᚠ rule (for the control) --------------------

def enc_litf(plain, K, use_skip):
    """c = p + K with the literal-ᚠ rule: a plaintext F emits ᚠ and consumes no
    key; with use_skip, the pointer also skips to dodge a would-be doublet."""
    out, j = [], 0
    for p in plain:
        if p == F:
            out.append(F)                      # literal ᚠ, pointer holds
            continue
        ci = (p + K[j]) % N
        j += 1
        if use_skip:
            while out and ci == out[-1]:
                ci = (p + K[j]) % N
                j += 1
        out.append(ci)
    return out


# --- the ᚠ-aware beam decoder -----------------------------------------------

def beam_decode_litf(cipher, K, sign, model, beam, max_skip, use_skip):
    """Return (avg_score, plaintext). At a ciphertext ᚠ, branch {hold: p=F,
    pointer stays; advance: p=(c+sign*K)}. Elsewhere advance (with optional
    key-skip). sign=-1 <=> encryption c=p+K."""
    ctx = model.order - 1
    beams = [(0.0, 0, (), ())]                  # (score, ptr, hist, path)
    for ci in cipher:
        nxt = []
        for score, j, hist, path in beams:
            skips = range(max_skip + 1) if use_skip else (0,)
            for sk in skips:                    # normal / advancing branch
                used = j + sk
                p = (ci + sign * K[used]) % N
                s = score + SKIP_PEN * sk + model.logscore_next(hist, p)
                nxt.append((s, used + 1, (hist + (p,))[-ctx:], path + (p,)))
            if ci == F:                         # literal-ᚠ hold branch
                p = F
                s = score + model.logscore_next(hist, p)
                nxt.append((s, j, (hist + (p,))[-ctx:], path + (p,)))
        nxt.sort(key=lambda t: -t[0])
        beams = nxt[:beam]
    best = beams[0]
    return best[0] / max(1, len(cipher) - 1), list(best[3])


# --- candidate keystreams ----------------------------------------------------

def build_configs(head, max_skip):
    """(label, K, sign, use_skip) tuples. Long enough for the worst-case
    pointer (advance 1+max_skip per rune)."""
    L = (max_skip + 1) * head + 64
    cfgs = []
    for name in ("prime", "totient"):
        K = materialize(name, L)
        for sign in (-1, +1):
            cfgs.append((f"{name}", K, sign, False))
            cfgs.append((f"{name}+skip", K, sign, True))
    for w in CICADA_WORDS:                       # the solved-page scheme is word+F
        K = word_key(w, L)
        for sign in (-1, +1):
            cfgs.append((w, K, sign, False))     # pure literal-ᚠ only (periodic)
    return cfgs


def search(cipher, cfgs, model, beam, max_skip):
    best = None
    for label, K, sign, use_skip in cfgs:
        sc, dec = beam_decode_litf(cipher, K, sign, model, beam, max_skip, use_skip)
        if best is None or sc > best[0]:
            best = (sc, label, sign, use_skip, dec)
    return best


# --- controls ----------------------------------------------------------------

def litf_floor(cfgs, model, head, beam, max_skip):
    """Detection floor: plant each keystream config (encrypting English under it
    WITH the literal-ᚠ rule) and recover it through the identical search.

    Replaces a control that (a) judged by `English - 0.5`, wrong for beam scores,
    and (b) at the old default head=80 exercised only ONE literal-ᚠ, so the
    accuracy gate was nearly vacuous for the +SKIP arm (§28/R1). The default head
    is now 120, which carries several ᚠ.
    """
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:head]
    nF = sum(1 for x in pt if x == F)
    print(f"(the planted plaintext contains {nF} literal-ᚠ at head={head})")
    by = {}
    for label, K, sign, use_skip in cfgs:
        by.setdefault((label, use_skip), (K, sign))
    names = list(by)

    def plant(name):
        K, _ = by[name]
        return enc_litf(pt, K, name[1])

    def recover(ct):
        sc, label, sign, us, dec = search(ct, cfgs, model, beam, max_skip)
        acc = sum(1 for a, b in zip(dec, pt) if a == b) / len(pt)
        return sc, (label, us), acc

    return detection_floor(names, plant, recover, label="config")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", type=int, default=120)
    ap.add_argument("--beam", type=int, default=150)
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--draws", type=int, default=6)
    args = ap.parse_args()

    segs = parse("data/liber_primus.md")
    model = get_model(args.order)
    cfgs = build_configs(args.head, args.max_skip)
    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(3)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"literal-ᚠ interrupter: {len(cfgs)} configs "
          f"(prime/totient x pure/+skip + {len(CICADA_WORDS)} word keys), both signs")
    print(f"refs: English trigram {eng:.2f}, random {rnd:.2f}\n")

    floor, covered, uncovered, _ = litf_floor(
        cfgs, model, args.head, args.beam, args.max_skip)
    if floor is None:
        print("no config self-recovers — no demonstrated power; aborting.")
        return

    real = [s for s in segs if not s.solved and len(s.indices) >= 50]
    score_fn = lambda ct: search(ct, cfgs, model, args.beam, args.max_skip)[0]
    ceil = matched_ceiling(score_fn, args.head, trials=len(real), seed=700)
    print(f"=== MATCHED CHANCE CEILING (max over {len(real)} random texts of "
          f"{args.head} runes): {ceil:.2f} ===\n")

    print("REAL unsolved segments (keystream + literal-ᚠ interrupter):")
    overall = None
    for s in segs:
        if s.solved or len(s.indices) < 50:
            continue
        sc, label, sign, us, dec = search(s.indices[:args.head], cfgs, model,
                                          args.beam, args.max_skip)
        flag = "  <-- ABOVE CEILING" if sc > ceil else ""
        print(f"  {s.section[:30]:30s} '{label}' {('c-k' if sign<0 else 'c+k')}"
              f"{'+skip' if us else '':5s} trigram {sc:.2f}{flag}")
        print(f"      {g.indices_to_latin(dec)[:76]}")
        if overall is None or sc > overall[0]:
            overall = (sc, s.section, label)

    print(f"\nbest on {overall[1][:26]} ('{overall[2]}')")
    print(verdict(overall[0], floor, ceil, len(covered), len(covered)+len(uncovered),
                  label="configs"))


if __name__ == "__main__":
    main()
