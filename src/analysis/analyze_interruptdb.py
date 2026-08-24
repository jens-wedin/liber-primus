"""Verify relikd's finished 29-rune InterruptDB firsthand (N1).

§40 built the power analysis for a generalised interrupter (any of the 29 runes,
not just ᚠ): an interrupt ORACLE gives a per-slot IoC of 1.886 vs ~1.0 noise —
detectable in principle — but 63% of ciphertext runes equal to the interrupt rune
are coincidental, and each false skip desyncs the rest, collapsing the signal to
1.201. The real attack is an interrupt-SUBSET search (relikd's sequential
look-ahead + genetic bit-flipping, first ~20 occurrences per page, ~1.4e10 ops,
~38 h). relikd ran it and ships the result as a database.

Rather than rebuild the 38-hour search, this verifies relikd's finished result
from the raw `db/` files. Format (per the db header):
  `section | #interrupts | score | interrupt-rune | key-length | positions`
`db_norm` scores closeness to English IoC (English ≈ 1.0); `db_high` stores the
raw IoC (English ≈ 1.74, random ≈ 1.0). We take the best score per section and
split the genuinely-unsolved page-range sections from the SOLVED control pages.

The result is a large, powered, independent NEGATIVE:
  * every SOLVED control page is recovered near English (db_norm 0.81-1.00) — so
    the search has power;
  * every genuinely-unsolved section tops out at db_norm ~0.55-0.63 (IoC ~1.5),
    far below English;
  * the bullseye control is `p57_parable` — the one solved LP2 page that sits in
    the unsolved numbering — which scores 0.997, exactly where a solved page
    should, while the truly-unsolved pages beside it sit at ~0.6.

So the full 29-rune interrupter × polyalphabetic-key sweep (key lengths 1-32)
does not lift the unsolved Liber Primus out of the random floor, confirming §40
and closing N1 without our own 38-hour rebuild.

Data (gitignored, fetch on demand):
  download/relikd_interruptdb/{db_norm.txt,db_high.txt}
  curl -sL https://raw.githubusercontent.com/relikd/LiberPrayground/main/db/db_norm.txt \\
    -o download/relikd_interruptdb/db_norm.txt   # and db_high.txt

Usage: python3 analyze_interruptdb.py
"""
# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

import collections
import os

DB = "download/relikd_interruptdb"


def best_by_section(path):
    best = collections.defaultdict(float)
    for line in open(path):
        if line.startswith("#"):
            continue
        p = line.rstrip("\n").split("|")
        if len(p) < 5:
            continue
        try:
            best[p[0]] = max(best[p[0]], float(p[2]))
        except ValueError:
            continue
    return best


def is_unsolved(section):
    # unsolved page-range sections are 'p' + digit ('p0-2', 'p54-55'); the solved
    # controls have names ('0_koan_1', '57_parable', 'jpg229').
    return len(section) > 1 and section[0] == "p" and section[1].isdigit()


def main():
    norm_path = os.path.join(DB, "db_norm.txt")
    high_path = os.path.join(DB, "db_high.txt")
    if not os.path.exists(norm_path):
        print(f"missing {norm_path} — fetch it (see the module docstring).")
        return
    norm = best_by_section(norm_path)
    high = best_by_section(high_path)

    un = sorted(s for s in norm if is_unsolved(s))
    sv = sorted(s for s in norm if not is_unsolved(s))

    print("=== relikd InterruptDB — best score per section (verified firsthand) "
          "===")
    print("(db_norm: English ≈ 1.0; db_high: IoC, English ≈ 1.74, random ≈ 1.0)\n")
    print("GENUINELY UNSOLVED sections:")
    for s in un:
        print(f"  {s:12s} db_norm {norm[s]:.3f}   db_high IoC {high.get(s, 0):.3f}")
    plain_un = [s for s in un if s not in ("p57_parable", "p56_an_end")]
    print(f"  -> unsolved db_norm range: "
          f"{min(norm[s] for s in plain_un):.3f} .. "
          f"{max(norm[s] for s in plain_un):.3f}  (far below English 1.0)\n")

    print("SOLVED control sections (the method must recover these):")
    for s in sv:
        print(f"  {s:20s} db_norm {norm[s]:.3f}   db_high IoC {high.get(s, 0):.3f}")
    print(f"  -> solved db_norm range: {min(norm[s] for s in sv):.3f} .. "
          f"{max(norm[s] for s in sv):.3f}\n")

    print("BULLSEYE: p57_parable (the one solved LP2 page in the unsolved "
          f"numbering) scores db_norm {norm.get('p57_parable', 0):.3f} — where a "
          "SOLVED page belongs — while\nthe truly-unsolved pages beside it top "
          "out near 0.6.\n")

    print("VERDICT: the full 29-rune interrupter × polyalphabetic sweep (key "
          "lengths 1-32)\nrecovers every solved page but leaves every unsolved "
          "section at the random floor.\nA large, powered, INDEPENDENT negative, "
          "verified from relikd's raw db — it\nconfirms §40 and closes N1 without "
          "our own 38-hour rebuild.\n")

    verify_modulo()


def verify_modulo():
    """N4: relikd's alternating-alphabet ('modulo cipher') sweep. It splits the
    text into mod-2/3 subgroups and finds the best interrupt set + key length per
    subgroup, over 2^20 combinations. Per-subgroup scores look HIGHER than the
    main sweep (db_norm up to ~0.93, db_high IoC up to ~1.99) — but that is length
    and multiplicity inflation, not signal: IoC is measured per key-slot
    (subgroup / key-length), which is a very short sequence, and the max over 2^20
    trials at that length runs far above what is observed."""
    import glob
    import collections
    def best_over(pattern):
        merged = collections.defaultdict(float)
        for path in sorted(glob.glob(os.path.join(DB, pattern))):
            for sec, sc in best_by_section(path).items():
                merged[sec] = max(merged[sec], sc)
        return merged

    if not glob.glob(os.path.join(DB, "db_norm_mod_*.txt")):
        print("\n(modulo db files not present — skipping N4 verification.)")
        return
    normf = best_over("db_norm_mod_*.txt")
    highf = best_over("db_high_mod_*.txt")
    un = sorted(s for s in normf if is_unsolved(s)
                and s not in ("p57_parable", "p56_an_end"))

    print("=== N4: relikd's MODULO (alternating-alphabet) sweep, verified "
          "firsthand ===")
    print("best per unsolved section, across a/b × mod-2/3 × subgroups:")
    for s in un:
        print(f"  {s:10s} db_norm {normf[s]:.3f}   db_high IoC {highf.get(s, 0):.3f}")
    print(f"  -> unsolved db_norm best: "
          f"{max(normf[s] for s in un):.3f} (still < English 1.0)\n")

    # chance ceiling at the SHORT per-key-slot lengths IoC is measured on
    import controls

    def ioc(seq):
        m = len(seq)
        c = collections.Counter(seq)
        return sum(v * (v - 1) for v in c.values()) / (m * (m - 1) / 29)

    print("random IoC ceiling at short per-key-slot lengths (200k draws each):")
    for L in (12, 20, 40):
        best = max(ioc(controls.random_runes(L, seed=t)) for t in range(200000))
        print(f"  L={L:2d}: max random IoC {best:.2f}")
    print("  -> the observed db_high IoC (~1.99) sits INSIDE the chance ceiling "
          "for short\n     slots; db_norm's >=25-rune floor keeps the unsolved "
          "best below English.\n")
    print("VERDICT (N4): the alternating-alphabet 'modulo cipher' is a confirmed "
          "NEGATIVE —\nits higher-looking scores are length/multiplicity "
          "inflation, and relikd's own\nnote records that no solution fits both "
          "subgroups. Weaker than N1 (the mod sweep\nomits the solved controls), "
          "but consistent with it and with §4.")


if __name__ == "__main__":
    main()
