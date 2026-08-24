"""Test bootstrap: put the src/ subfolders on sys.path so tests import the
project's flat modules (import gematria, from controls import ...) exactly as the
scripts do."""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = os.path.join(_ROOT, "src", _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)
