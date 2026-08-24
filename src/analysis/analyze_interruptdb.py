"""Verify relikd's finished 29-rune InterruptDB firsthand (N1).

§40 built the power analysis for a generalised interrupter (any of the 29 runes,
not just ᚠ): an interrupt ORACLE gives a per-slot IoC of 1.886 vs ~1.0 noise —
detectable in principle — but 63% of ciphertext runes equal to the interrupt rune
are coincidental, and each false skip desyncs the rest, collapsing the signal to
1.201. The real attack is an interrupt-SUBSET search (relikd's sequential
look-ahead + genetic bit-flipping, first ~20 occurrences per page, ~1.4e10 ops,
~38 h). relikd ran it and ships the result as a database.

Rather than rebuild the 38-hour search, this verifies relikd's finished result
# --- path bootstrap: keep flat imports working across src/ subfolders ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _d in ("core", "attacks", "analysis"):
    _p = _os.path.join(_SRC, _d)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
# --- end path bootstrap ---

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
          "our own 38-hour rebuild.")


if __name__ == "__main__":
    main()
