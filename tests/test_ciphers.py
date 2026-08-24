"""Cipher-op invariants in rune-index space mod 29."""
import ciphers as c
import gematria as g


def test_atbash_is_an_involution():
    ix = list(range(g.N))
    assert c.atbash(c.atbash(ix)) == ix


def test_atbash_reflects_the_ring():
    assert c.atbash([0, 1, 28]) == [28, 27, 0]


def test_shift_then_unshift_is_identity():
    ix = [5, 0, 28, 13, 1]
    assert c.shift(c.shift(ix, 7), g.N - 7) == ix


def test_prime_stream_starts_with_the_primes():
    it = c.prime_stream()
    assert [next(it) for _ in range(5)] == [2, 3, 5, 7, 11]


def test_totient_stream_is_prime_minus_one():
    it = c.totient_stream()
    assert [next(it) for _ in range(5)] == [1, 2, 4, 6, 10]
