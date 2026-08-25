"""Digraphic Hill cipher (2x2 over GF(29)) — round-trip and brute recovery (N22).

The Swedish paper proposes a 2x2 Hill cipher on rune pairs. These lock the two
invariants the attack rests on: encrypt/decrypt is an exact involution for any
invertible matrix, and the brute recovers a planted matrix through its own scorer.
"""
import pytest

import attack_hill as H
from language_model import get_model


def test_hill_roundtrip_is_exact():
    pt = [3, 18, 0, 24, 7, 11, 16, 2]          # even length
    M = (2, 1, 3, 5)                            # det = 2*5-1*3 = 7, invertible mod 29
    ct = H.hill_encrypt(pt, M)
    back = H.hill_decrypt(ct, M)
    assert back == pt
    assert ct != pt                            # it actually enciphers


def test_singular_matrix_rejected():
    assert not H.is_invertible((2, 4, 1, 2))   # det = 0
    assert H.is_invertible((2, 1, 3, 5))


@pytest.mark.slow
def test_brute_recovers_planted_matrix():
    model = get_model(3)
    from doublet_sim import english_plaintext
    from parse_lp import parse
    pt = english_plaintext(parse("data/liber_primus.md"))[:60]
    if len(pt) % 2:
        pt = pt[:-1]
    M = (5, 2, 3, 7)                            # det = 35-6 = 29 ≡ 0 -> pick another
    M = (5, 2, 4, 7)                            # det = 35-8 = 27, invertible
    ct = H.hill_encrypt(pt, M)
    best = H.brute_best(ct, model, head=len(ct), workers=1)
    assert best[1] == M, f"expected planted {M}, got {best[1]}"
