"""controls: the null must be uniform, reproducible, and NOT producible by the
project's own LCG (the audit invariant that inflated a ceiling once)."""
import controls
from doublet_sim import LCG


def test_random_runes_is_reproducible_and_in_range():
    a = controls.random_runes(50, seed=1)
    b = controls.random_runes(50, seed=1)
    assert a == b and len(a) == 50
    assert all(0 <= x < 29 for x in a)


def test_null_is_not_reproduced_by_the_project_lcg():
    null = controls.random_runes(8, seed=700)
    for sd in range(0, 5000):
        r = LCG(sd)
        if [r.randint(29) for _ in range(8)] == null:
            raise AssertionError(f"LCG seed {sd} reproduces the null")


def test_shuffled_is_a_permutation():
    seq = list(range(40))
    s = controls.shuffled(seq, seed=5)
    assert sorted(s) == seq and s != seq
