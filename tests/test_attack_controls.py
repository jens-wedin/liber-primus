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
