"""The no-repeat mechanism: key-skip removes doublets; the soft rule fits ~0.19."""
import paths
import no_repeat_model as M
from parse_lp import parse
from doublet_sim import english_plaintext, LCG

SEGS = parse(paths.data("liber_primus.md"))
PT = english_plaintext(SEGS)[:600]
_RNG = LCG(11)
K = [_RNG.randint(29) for _ in range(2000)]   # one generator -> a VARYING key


def _doublets(seq):
    return sum(1 for i in range(1, len(seq)) if seq[i] == seq[i - 1])


def test_key_skip_emits_no_doublets():
    assert _doublets(M.enc_key_skip(PT, K)) == 0


def test_soft_rule_with_zero_keep_emits_no_doublets():
    assert _doublets(M.enc_soft(PT, K, 0.0, LCG(3))) == 0


def test_fitted_p_keep_matches_the_reported_0_19():
    un = [s for s in SEGS if not s.solved and len(s.indices) >= 50]
    p_keep, obs, pairs = M.fit_p_keep(un)
    assert obs == 86                     # the 86 residual doublets
    assert 0.18 <= p_keep <= 0.20


def test_key_skip_raises_on_a_constant_key_instead_of_hanging():
    import pytest
    const_key = [7] * 50            # a doublet can never be dodged
    with pytest.raises(ValueError):
        M.enc_key_skip([3, 4, 4, 4], const_key)
