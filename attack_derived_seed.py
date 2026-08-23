"""Derived-seed keystream + key-skip, recovered by the skip-aware beam (N6).

Why this exists — the gap it fills.
`attack_prng.py` (§13) brute-forced seeded generators, but it decodes with a
POSITION-LOCKED subtract (`p[i] = c[i] - K[i]`) and plants a RE-ROLL pad. That
is correct for the re-roll variant — re-roll keeps K in lock-step with position
— so §13's negative is valid for RE-ROLL pads only. A KEY-SKIP pad (the
mechanism §4/§11 say the data demands) DESYNCHRONISES K: every dodged doublet
consumes an extra, invisible key value, and a position-locked subtract can never
realign. That whole cell was never tested.

The external sweep (2026-08-23, backlog N6) made it concrete: Dukotah/cicada3301
planted a SHA-256 counter-mode keystream from the passphrase seed "CICADA3301"
under an anti-repeat filter. A rigid decoder scored the correct seed as noise
(-6.835); a skip-aware BEAM recovered it (-4.170, 98.9% of the plaintext). So a
short, guessable seed driving a hash keystream is INSIDE resolving power — but
only through the beam. This script is that attack.

What it does:
  - keystream K = hash-counter-mode(seed) for a set of hash generators;
  - decode each unsolved segment with the key-skip beam over K (start 0);
  - seed space = thematic PASSPHRASES (the Cicada vocabulary, notable strings,
    year/number strings, case variants) — the kind a puzzle-maker picks, which
    §13's integer brute never covered as strings.

Honesty caveats (read before trusting any result):
  - This is a CLASS reproduction of Dukotah's control, not a BYTE one: their
    exact counter-mode framing is not published, so we test several plausible
    framings, not their literal bytes.
  - A hash keystream from a HIGH-ENTROPY seed is a one-time pad and is
    unbreakable without the seed (§13 wall). This attack only ever rules out
    LOW-ENTROPY / thematic passphrase seeds — a negative rules out THOSE.

Everything is routed through controls.py: a detection floor (plant a seed,
recover it, read the score a real break gives) and a length- and trial-matched
chance ceiling gate every verdict.

Usage: python3 attack_derived_seed.py [--head 44] [--beam 300] [--max-skip 2]
       python3 attack_derived_seed.py --selftest   # Dukotah reproduction only
"""

import argparse
import hashlib

import gematria as g
from parse_lp import parse
from language_model import get_model
from attack_keyskip import beam_decode
from no_repeat_model import enc_key_skip, count_skips
from doublet_sim import english_plaintext, LCG
from controls import matched_ceiling, detection_floor, verdict
from attack_vigenere_skip import CICADA_WORDS

N = g.N


# --- hash-counter keystream generators ---------------------------------------
# Each maps (seed_string, n) -> n rune indices. They differ only in how the
# seed and counter are framed into the hash input — the framing a puzzle-maker
# picks is unknown, so we cover the plausible ones.

def _sha256_colon(seed, n):
    out = []
    for i in range(n):
        out.append(hashlib.sha256(f"{seed}:{i}".encode()).digest()[0] % N)
    return out


def _sha256_concat(seed, n):
    out = []
    for i in range(n):
        out.append(hashlib.sha256(f"{seed}{i}".encode()).digest()[0] % N)
    return out


def _sha256_bytes(seed, n):
    base = seed.encode()
    out = []
    for i in range(n):
        out.append(hashlib.sha256(base + i.to_bytes(4, "big")).digest()[0] % N)
    return out


def _sha512_colon(seed, n):
    out = []
    for i in range(n):
        out.append(hashlib.sha512(f"{seed}:{i}".encode()).digest()[0] % N)
    return out


GENERATORS = {
    "sha256_colon":  _sha256_colon,
    "sha256_concat": _sha256_concat,
    "sha256_bytes":  _sha256_bytes,
    "sha512_colon":  _sha512_colon,
}


# --- passphrase seed space ---------------------------------------------------

def seed_space():
    """Thematic passphrase strings a puzzle-maker plausibly picks. §13 brute-
    forced integer seeds; the untested cell is STRING seeds through a hash."""
    phrases = set()
    # the vocabulary, in the case variants a seed might use
    for w in CICADA_WORDS:
        phrases.add(w)
        phrases.add(w.lower())
        phrases.add(w.capitalize())
    # notable strings and numbers as strings
    for s in ["CICADA3301", "cicada3301", "Cicada3301", "3301", "1033", "33",
              "761", "167", "LIBERPRIMUS", "LIBER PRIMUS", "LiberPrimus",
              "ANEND", "AN END", "WELCOME", "AWARNING", "PARABLE", "KOAN",
              "INSTAR EMERGENCE", "DIVINITY3301", "WISDOM", "THE LOSS OF DIVINITY",
              "END OF ALL THINGS", "MOBIUS", "EULER", "TOTIENT", "PRIMALITY",
              "2013", "2014", "1595277641", "3", "0"]:
        phrases.add(s)
    return sorted(phrases)


def gen_keystream(gname, seed, n):
    return GENERATORS[gname](seed, n)


# --- brute -------------------------------------------------------------------

def brute(chead, gens, seeds, model, beam, max_skip):
    """Best (norm-score, gen, seed, sign, decode) over generators x seeds x
    signs, decoded with the key-skip beam from start 0."""
    m = len(chead)
    need = m * (max_skip + 1) + 16
    best = None
    for gname in gens:
        for seed in seeds:
            K = gen_keystream(gname, seed, need)
            for sign in (-1, +1):
                sc, dec = beam_decode(chead, K, 0, sign, model, beam, max_skip)
                bl = sc / max(1, m - 1)
                if best is None or bl > best[0]:
                    best = (bl, gname, seed, sign, dec)
    return best


# --- Dukotah reproduction: plant a hash-CTR seed under key-skip, beam-recover -

def reproduce_dukotah(model, head, beam, max_skip):
    print("=== N6 REPRODUCTION: hash-CTR seed + key-skip, recovered by beam ===")
    print("    (class reproduction of Dukotah/cicada3301's planted control)\n")
    # A fixed, longer plant so the key-skip actually fires: over 44 runes this
    # seed happens to produce 0 skips (rigid == beam, no demonstration); 200
    # runes carry ~3 skips, enough to desync the rigid decode.
    REPRO_LEN = 200
    beam = max(beam, 500)
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:REPRO_LEN]
    seed = "CICADA3301"
    gname = "sha256_colon"
    need = len(pt) * (max_skip + 1) + 16
    K = gen_keystream(gname, seed, need)
    ct = enc_key_skip(pt, K)

    # (1) rigid / position-locked decode — the §13-style subtract, should FAIL
    rigid = [(ct[i] - K[i]) % N for i in range(len(ct))]
    n = min(len(rigid), len(pt))
    rigid_acc = sum(1 for a, b in zip(rigid[:n], pt[:n]) if a == b) / n
    rigid_sc = model.score_sequence(rigid[:n])

    # (2) skip-aware beam decode over the same K — should RECOVER
    sc, dec = beam_decode(ct, K, 0, -1, model, beam, max_skip)
    bl = sc / max(1, len(ct) - 1)
    m = min(len(dec), len(pt))
    beam_acc = sum(1 for a, b in zip(dec[:m], pt[:m]) if a == b) / m

    print(f"  planted seed '{seed}' via {gname}, key-skip encrypted "
          f"{len(pt)} runes")
    print(f"  rigid position-locked decode (a la attack_prng §13): "
          f"score {rigid_sc:.2f}, {rigid_acc*100:.0f}% recovered  <- FAILS")
    print(f"  skip-aware beam decode:                              "
          f"score {bl:.2f}, {beam_acc*100:.0f}% recovered  <- RECOVERS")
    print(f"  ({count_skips(pt, K)} hidden key-skips over {len(pt)} runes "
          f"desync the rigid decode)")
    ok = beam_acc > 0.9 and (beam_acc - rigid_acc) > 0.2
    print(f"  reproduction: {'PASS' if ok else 'FAIL'} "
          f"(beam recovers, rigid desyncs)\n")
    return ok


# --- detection floor: plant several seeds, recover through the full brute ----

def calibrate_floor(model, head, beam, max_skip, seeds):
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)[:head]

    # plant a handful of real seeds under the default generator
    plant_gen = "sha256_colon"
    plant_names = [(plant_gen, s) for s in
                   ["CICADA3301", "DIVINITY", "3301", "wisdom", "PARABLE"]]

    def plant(name):
        gname, seed = name
        need = len(pt) * (max_skip + 1) + 16
        return enc_key_skip(pt, gen_keystream(gname, seed, need))

    def recover(ct):
        bl, gname, seed, sign, dec = brute(ct, GENERATORS, seeds, model,
                                           beam, max_skip)
        m = min(len(dec), len(pt))
        acc = sum(1 for a, b in zip(dec[:m], pt[:m]) if a == b) / m
        return bl, (gname, seed), acc

    return detection_floor(plant_names, plant, recover, label="seed")


# --- main --------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", type=int, default=44,
                    help="runes per segment to score (matches other attacks)")
    ap.add_argument("--beam", type=int, default=300)
    ap.add_argument("--max-skip", type=int, default=2)
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--selftest", action="store_true",
                    help="run the Dukotah reproduction only, then exit")
    args = ap.parse_args()

    model = get_model(args.order)

    if args.selftest:
        ok = reproduce_dukotah(model, args.head, args.beam, args.max_skip)
        raise SystemExit(0 if ok else 1)

    # reproduction gates the whole run: if the beam cannot recover a planted
    # hash-CTR key-skip seed, any negative below is meaningless.
    if not reproduce_dukotah(model, args.head, args.beam, args.max_skip):
        print("reproduction FAILED — not trusting the real run.")
        return

    segs = parse("data/liber_primus.md")
    unsolved = [s for s in segs if not s.solved and len(s.indices) >= 50]
    seeds = seed_space()
    print(f"generators: {', '.join(GENERATORS)}")
    print(f"seed space: {len(seeds)} thematic passphrases "
          f"(x {len(GENERATORS)} generators x 2 signs)\n")

    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(5)
    rnd = model.score_sequence([rng.randint(N) for _ in range(400)])
    print(f"refs: English trigram {eng:.2f}, random {rnd:.2f}\n")

    floor, cov, unc, _ = calibrate_floor(model, args.head, args.beam,
                                         args.max_skip, seeds)

    # matched chance ceiling: the same brute on random ciphertext, one draw per
    # real run (per-segment runs + the global run).
    # extra=0: the ciphertext the ceiling scores must be exactly `head` runes,
    # like the real segments. brute() generates its own keystream internally
    # (need = m*(max_skip+1)+16), so the drawn null needs no keystream padding.
    n_trials = len(unsolved) + 1
    ceil = matched_ceiling(
        lambda ct: brute(ct, GENERATORS, seeds, model, args.beam,
                         args.max_skip)[0],
        args.head, trials=n_trials, seed=700)
    print(f"=== CHANCE CEILING ({n_trials} trials matched to the real runs): "
          f"{ceil:.2f} ===\n")

    # GLOBAL: one seed for the whole concatenated unsolved stream
    glob = [i for s in unsolved for i in s.indices][:args.head]
    gbl, ggen, gseed, gsign, gdec = brute(glob, GENERATORS, seeds, model,
                                          args.beam, args.max_skip)
    print("=== REAL: global keystream (one seed, whole stream) ===")
    print(f"  best {ggen} seed '{gseed}' {'c-k' if gsign<0 else 'c+k'} "
          f"score {gbl:.2f}")
    print(f"    {g.indices_to_latin(gdec)[:100]}\n")

    print("=== REAL: per-segment keystream (each page its own seed) ===")
    overall = gbl
    for s in unsolved:
        bl, gn, sd, sg, dec = brute(s.indices[:args.head], GENERATORS, seeds,
                                    model, args.beam, args.max_skip)
        overall = max(overall, bl)
        print(f"  {s.section[:30]:30s} {gn:13s} '{str(sd)[:16]:16s}' "
              f"{'c-k' if sg<0 else 'c+k'} {bl:.2f}")

    print()
    print(verdict(overall, floor, ceil, n_covered=len(cov),
                  n_total=len(cov) + len(unc), label="seeds"))


if __name__ == "__main__":
    main()
