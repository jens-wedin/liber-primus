"""paths: resolve repo files relative to the repo root, not the cwd.

Post-restructure the scripts read 'data/...' relative to the current directory,
which breaks when run from anywhere but the repo root. `paths` fixes that.
"""
import os
import pytest


def test_root_is_the_repo_root():
    import paths
    root = paths.root()
    assert os.path.isabs(root)
    assert os.path.isdir(os.path.join(root, "src", "core"))
    assert os.path.isfile(os.path.join(root, "data", "liber_primus.md"))


def test_data_resolves_absolute_and_exists():
    import paths
    p = paths.data("liber_primus.md")
    assert os.path.isabs(p)
    assert os.path.isfile(p)


def test_data_is_cwd_independent(tmp_path, monkeypatch):
    import paths
    monkeypatch.chdir(tmp_path)          # run from somewhere that is NOT the root
    p = paths.data("liber_primus.md")
    assert os.path.isfile(p)             # still resolves
