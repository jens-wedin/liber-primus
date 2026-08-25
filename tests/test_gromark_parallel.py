"""Parallelising the Gromark primer brute must not change its result.

The per-segment run (§42/N10-ext) brute-forces 24,360 L=3 primers per segment;
serial it is ~5 min/brute. Parallelising across cores is only safe if it returns
the IDENTICAL best (score, primer, sign, decode) — otherwise the checkpoint cache
(keyed only by ciphertext, not by worker count) would mix incompatible results.
This locks that invariant on a small injected primer list.
"""
import attack_gromark as G
from language_model import get_model


def test_brute_best_parallel_matches_serial():
    model = get_model(3)
    ct = [(i * 7 + 3) % 29 for i in range(24)]          # small deterministic ct
    primer_list = [(1, 2, 3), (5, 0, 7), (9, 27, 12), (2, 2, 5), (11, 4, 19)]
    head, beam, skip = 20, 12, 2

    ser = G.brute_best(ct, model, head, beam, skip,
                       primer_list=primer_list, workers=1)
    par = G.brute_best(ct, model, head, beam, skip,
                       primer_list=primer_list, workers=4)

    assert par[1] == ser[1], "parallel picked a different primer"
    assert par[2] == ser[2], "parallel picked a different sign"
    assert par[3] == ser[3], "parallel returned a different decode"
    assert abs(par[0] - ser[0]) < 1e-9, "parallel score differs"
