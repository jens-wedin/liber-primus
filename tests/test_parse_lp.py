"""Parsing invariants — the segment split and the canonical unsolved count."""
import paths
from parse_lp import parse

SEGS = parse(paths.data("liber_primus.md"))


def test_unsolved_stream_is_12947_runes_over_13_segments():
    un = [s for s in SEGS if not s.solved and len(s.indices) >= 50]
    assert len(un) == 13
    assert sum(len(s.indices) for s in un) == 12947


def test_words_partition_each_segment_exactly():
    for s in SEGS:
        assert sum(len(w) for w in s.words) == len(s.indices)


def test_some_pages_are_solved():
    assert any(s.solved for s in SEGS)
