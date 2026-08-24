"""solved_text.full_plaintext must return the verified solved plaintext."""
import paths
import solved_text
from parse_lp import parse


def test_full_plaintext_is_nonempty_rune_indices():
    pt = solved_text.full_plaintext(parse(paths.data("liber_primus.md")))
    assert len(pt) > 500
    assert all(0 <= x < 29 for x in pt)
