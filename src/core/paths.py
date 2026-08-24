"""Resolve repo files relative to the repo ROOT, not the current directory.

The scripts read `data/...` and write `results/...` with cwd-relative paths, so
they only work when run from the repo root. `paths.data(name)` and
`paths.results(name)` resolve against the root regardless of cwd, so a script can
be run from anywhere. The root is found by walking up from this file until a
directory that has both `src/` and `data/`.
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))


def root():
    """Absolute path to the repo root."""
    d = _HERE
    while True:
        if os.path.isdir(os.path.join(d, "src")) and \
           os.path.isdir(os.path.join(d, "data")):
            return d
        parent = os.path.dirname(d)
        if parent == d:                       # reached the filesystem root
            raise RuntimeError("repo root not found above %s" % _HERE)
        d = parent


def _under(sub, parts):
    return os.path.join(root(), sub, *parts)


def data(*parts):
    return _under("data", parts)


def results(*parts):
    return _under("results", parts)


def download(*parts):
    return _under("download", parts)
