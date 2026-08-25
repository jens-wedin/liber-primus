"""Reading-order diagnostic must resolve the direction a no-repeat rule ran in (N23).

Characterises the power the §62 negative rests on: given a stream whose doublets
are suppressed along COLUMNS, the diagnostic must pick column-major as the
lowest-doublet-rate reading order (and row-major must read as ~random). If this
regressed, the real-data negative (row-major is lowest ⇒ no geometric transpose)
would be unfounded.
"""
import analyze_readorder as A


def _col_suppressed_grid(R=30, C=20):
    # deterministic LCG, doublets suppressed down each column
    from doublet_sim import LCG
    from gematria import N
    rng = LCG(7)
    cols = []
    for _ in range(C):
        col = []
        for _ in range(R):
            v = rng.randint(N)
            while col and v == col[-1]:
                v = rng.randint(N)
            col.append(v)
        cols.append(col)
    return [[cols[j][i] for j in range(C)] for i in range(R)]


def test_diagnostic_detects_column_reading_order():
    rows = _col_suppressed_grid()
    t = A.transforms(rows)
    rates = {name: A.rate_ioc([flat])[2] for name, flat in t.items()}
    best = min(rates, key=rates.get)
    assert best.startswith("column-major"), f"expected column-major lowest, got {best}"
    assert rates["column-major(transpose)"] < 0.5          # ~0% (suppressed)
    assert rates["row-major(=transcription)"] > 2.0        # ~random 3.45%
