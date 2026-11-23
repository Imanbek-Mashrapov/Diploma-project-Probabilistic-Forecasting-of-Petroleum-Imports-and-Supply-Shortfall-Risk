"""Fetch missing abstracts one DOI at a time from the Semantic Scholar Graph API with slow pacing
(the unauthenticated pool returns HTTP 429 most of the time). Writes metadata/raw/s2_abstracts.json incrementally."""
import json
import time
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[1] / "metadata" / "raw"
UA = {"User-Agent": "academic-literature-review-script"}


def main():
    v = json.load(open(RAW / "verified.json", encoding="utf-8"))
    out_path = RAW / "s2_abstracts.json"
    got = json.load(open(out_path, encoding="utf-8")) if out_path.exists() else {}
    todo = [i["doi"] for i in v if i["doi"] and len(i["abstract"]) < 100
            and len(i["verification"].get("crossref_abstract", "")) < 100 and i["doi"] not in got]
    todo.sort(key=lambda d: 0 if any(i["doi"] == d and i["tier"] == "core" for i in v) else 1)
    deadline = time.time() + 3 * 3600
    while todo and time.time() < deadline:
        d = todo[0]
        pid = f"ARXIV:{d.split('arxiv.')[1]}" if d.startswith("10.48550/arxiv.") else f"DOI:{d}"
        try:
            r = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/{pid}",
                             params={"fields": "title,abstract,tldr,openAccessPdf"}, headers=UA, timeout=40)
        except requests.RequestException:
            time.sleep(30); continue
        if r.status_code == 200:
            p = r.json()
            got[d] = {"title": p.get("title"), "abstract": p.get("abstract") or "", "tldr": (p.get("tldr") or {}).get("text", ""),
                      "oa_pdf": (p.get("openAccessPdf") or {}).get("url", "")}
            todo.pop(0)
            json.dump(got, open(out_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
            print("ok", d, bool(got[d]["abstract"]), flush=True)
            time.sleep(4)
        elif r.status_code == 404:
            got[d] = {"title": None, "abstract": "", "tldr": "", "oa_pdf": "", "status": "not_found"}
            todo.pop(0)
            print("404", d, flush=True)
        else:
            time.sleep(30)
    json.dump(got, open(out_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
