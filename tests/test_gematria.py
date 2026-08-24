"""Gematria Primus table invariants — 29 runes, bijections, round-trips."""
import gematria as g


def test_there_are_29_runes():
    assert g.N == 29
    assert len(g.RUNES) == 29


def test_primes_are_the_first_29_ascending():
    assert g.IDX_TO_PRIME[0] == 2
    assert g.IDX_TO_PRIME[:5] == [2, 3, 5, 7, 11]
    assert g.IDX_TO_PRIME == sorted(g.IDX_TO_PRIME)
    assert len(set(g.IDX_TO_PRIME)) == 29          # all distinct


def test_rune_index_is_a_bijection():
    for i in range(g.N):
        assert g.RUNE_TO_IDX[g.IDX_TO_RUNE[i]] == i


def test_index_to_latin_round_trips_for_every_rune():
    for i in range(g.N):
        assert g.latin_to_indices(g.indices_to_latin([i])) == [i]
