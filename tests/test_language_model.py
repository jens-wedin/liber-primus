"""The n-gram model must score English above random — the discriminator every
beam attack relies on."""
import paths
from language_model import get_model
from parse_lp import parse
from doublet_sim import english_plaintext, LCG


def test_english_scores_above_random():
    model = get_model(3)
    segs = parse(paths.data("liber_primus.md"))
    eng = model.score_sequence(english_plaintext(segs)[:400])
    rng = LCG(5)
    rnd = model.score_sequence([rng.randint(29) for _ in range(400)])
    assert eng > rnd + 1.0
