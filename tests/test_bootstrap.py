"""Every src module's path bootstrap must be LIVE (at module level), not stranded
inside the docstring — the bug where the inserter matched a docstring line
starting with 'from '/'import '. A dead bootstrap makes the module fail to import
when run directly from its own folder.
"""
import ast
import glob


def test_all_path_bootstraps_are_live():
    dead = []
    for path in glob.glob("src/**/*.py", recursive=True):
        src = open(path).read()
        if "path bootstrap" not in src:
            continue
        tree = ast.parse(src)
        live = any(isinstance(n, ast.Assign)
                   and any(getattr(t, "id", None) == "_SRC" for t in n.targets)
                   for n in tree.body)
        if not live:
            dead.append(path)
    assert not dead, f"bootstrap stranded inside docstring: {dead}"
