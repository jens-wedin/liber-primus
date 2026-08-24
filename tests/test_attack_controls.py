"""The positive controls that back the project's power claims must PASS.

Each attack proves it can recover a PLANTED hypothesis through its own pipeline
(the 'every claim is control-validated' ground rule). These tests pin that: if a
change silently breaks the beam or the model, the control stops recovering and
the test goes red — so a negative result can never quietly become meaningless.

They call the control functions directly (one plant-and-recover each, not the
full sweep) and run from the repo root, since the controls read data/.
"""
import numpy as np
import pytest

from language_model import get_model


@pytest.fixture(scope="module")
def model():
    return get_model(3)


@pytest.fixture(autouse=True)
def _at_repo_root(monkeypatch):
    import paths
    monkeypatch.chdir(paths.root())


@pytest.mark.slow
def test_keyskip_control_recovers_a_planted_prime_key_skip(model):
    import attack_keyskip
    assert attack_keyskip.selftest(model) is True


@pytest.mark.slow
def test_derived_seed_control_reproduces_the_hash_ctr_recovery(model):
    import attack_derived_seed
    # beam recovers a planted hash-CTR key-skip seed where a rigid decode cannot
    assert attack_derived_seed.reproduce_dukotah(model, 44, 300, 2) is True


@pytest.mark.slow
def test_running_text_control_recovers_a_planted_book_key(model):
    import attack_running_text as art
    import keytexts
    Karr = np.array(keytexts.get("runepoem_oe"), dtype=np.int16)
    T = art.trigram_table(model)
    assert art.positive_control(Karr, model, T,
                                scan_head=28, step=24, conf_len=44,
                                top=200, beam=200, max_skip=2) is True


@pytest.mark.slow
def test_vigenere_skip_control_recovers_a_planted_word_key(model):
    import attack_vigenere_skip as vs
    keys = vs.load_key_words(400, 4, 16)
    assert vs.positive_control(keys, model, head=30, beam=100, max_skip=2) is True


@pytest.mark.slow
def test_shortbrute_floor_recovers_planted_short_keys(model):
    import attack_shortbrute as sb
    floor, covered, uncovered, rows = sb.short_key_floor(
        2, 2, model, head=30, beam=100, max_skip=2, samples=5)
    assert floor is not None            # at least one planted L=2 key self-recovers
    assert len(covered) >= 1


@pytest.mark.slow
def test_prng_control_recovers_a_planted_reroll_seed(model):
    import attack_prng
    from doublet_sim import english_plaintext
    from parse_lp import parse
    segs = parse("data/liber_primus.md")
    pt = english_plaintext(segs)
    eng = model.score_sequence(pt[:400])
    assert attack_prng.positive_control(model, pt[:120], eng, set(range(50))) is True


@pytest.mark.slow
def test_autokey_control_recovers_a_planted_autokey(model):
    import attack_autokey
    from parse_lp import parse
    dist = attack_autokey.english_rune_distribution(parse("data/liber_primus.md"))
    assert attack_autokey.positive_control(dist) is True


@pytest.mark.slow
def test_difference_space_controls_recover_cumulative_ciphers(model):
    import difference_space as ds
    from doublet_sim import english_plaintext
    from parse_lp import parse
    pt = english_plaintext(parse("data/liber_primus.md"))
    eng = model.score_sequence(pt[:400])
    assert ds.control_vigenere(model, pt[:1200], eng, 40) is True
    assert ds.control_prime(model, pt[:1200], eng) is True
