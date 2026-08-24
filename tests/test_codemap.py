"""N14 regression: the code pages reproduce rtkd's String 4 byte-for-byte."""
import attack_codemap as CM
import analyze_codepage as A


def test_codes_reproduce_string4_256_of_256():
    pages = A.load_pages()
    codes = [c for p in CM.PAGE_ORDER for c in pages[p]]
    s4 = CM.load_target()
    assert len(codes) == len(s4) == 256
    hits = sum(1 for c, b in zip(codes, s4) if CM.code_value(c) == b)
    assert hits == 256
