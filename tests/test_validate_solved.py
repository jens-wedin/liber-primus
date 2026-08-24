"""The canonical regression: every solved page still reproduces (9/9).

This is the project's ground-truth check — run as a subprocess exactly as a
human would, so a break in any core cipher path is caught here.
"""
import subprocess
import sys
import paths


def test_all_solved_pages_reproduce():
    out = subprocess.run(
        [sys.executable, "validate_solved.py"],
        cwd=paths.root(), capture_output=True, text=True, timeout=300,
    )
    assert "9/9 checks passed" in out.stdout, out.stdout + out.stderr
    assert out.returncode == 0
