"""Helper for the full-text pass: print page-numbered snippets of a PDF around search terms.
Usage: python ftsearch.py <pdf> <max_chars_per_hit> <term1> [term2 ...]   (or --pages a-b to dump pages)"""
import re
import sys
import warnings

warnings.filterwarnings("ignore")
import fitz  # noqa: E402

pdf = sys.argv[1]
doc = fitz.open(pdf)
if sys.argv[2] == "--pages":
    a, b = map(int, sys.argv[3].split("-"))
    for p in range(a - 1, min(b, doc.page_count)):
        print(f"=== page {p + 1} ===")
        print(" ".join(doc[p].get_text().split())[: int(sys.argv[4]) if len(sys.argv) > 4 else 6000])
    sys.exit()
width = int(sys.argv[2])
print("pages:", doc.page_count)
for term in sys.argv[3:]:
    for p in range(doc.page_count):
        text = " ".join(doc[p].get_text().split())
        for m in list(re.finditer(term, text, re.I))[:2]:
            s = max(0, m.start() - width // 2)
            print(f"[p{p + 1}] '{term}': ...{text[s:s + width]}...")
