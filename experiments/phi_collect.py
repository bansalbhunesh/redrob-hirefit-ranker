"""Study Phi -- REAL corpus retrieval from the public Hacker News search API (Algolia).
ToS-clean public endpoint; we store only short excerpts + URLs, hash authors, and use the
text for qualitative analysis only (NOT model training). Writes a full query audit trail.

This collects ONLY the Hacker News stratum (founders / senior engineers / hiring managers).
The other strata in the frozen protocol (recruiter & engineering Reddit, Workplace
StackExchange, blogs, India-specific) require ToS-appropriate access and are left for the
full study; this is the protocol's prescribed pilot stratum.
"""
import csv
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("docs/human_opinion")
RAW = OUT / "raw_hn_corpus.jsonl"
SEARCHLOG = OUT / "search_log.csv"

QUERY_FAMILIES = {
    "integrity_focused": [
        "resume lied about years of experience", "fake employment history interview",
        "resume inconsistency rejection",
    ],
    "quality_first": [
        "great engineer bad resume", "projects matter more than resume",
        "hire candidate despite resume mistake",
    ],
    "verification_first": [
        "ask candidate explain resume discrepancy", "resume inconsistency typo or lie",
        "verify experience before rejecting",
    ],
    "technology_anachronism": [
        "years experience longer than technology existed", "claims ten years kubernetes",
        "inflated AI experience candidate",
    ],
}
PER_QUERY = 12


def fetch(query):
    url = ("https://hn.algolia.com/api/v1/search?" +
           urllib.parse.urlencode({"query": query, "tags": "comment", "hitsPerPage": PER_QUERY}))
    req = urllib.request.Request(url, headers={"User-Agent": "phi-research/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def strip_html(t):
    import re
    t = re.sub(r"<[^>]+>", " ", t or "")
    return re.sub(r"\s+", " ", t).replace("&#x27;", "'").replace("&quot;", '"').replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&").strip()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    seen = set()
    rows = []
    log = []
    for fam, queries in QUERY_FAMILIES.items():
        for q in queries:
            try:
                data = fetch(q)
            except Exception as e:
                log.append([fam, q, "ERROR", str(e)[:60], datetime.now(timezone.utc).date().isoformat()])
                continue
            hits = data.get("hits", [])
            kept = 0
            for h in hits:
                oid = h.get("objectID")
                txt = strip_html(h.get("comment_text"))
                if not oid or oid in seen or len(txt) < 120:
                    continue
                seen.add(oid)
                rows.append({
                    "item_id": f"HN_{oid}", "platform": "hackernews", "thread_id": str(h.get("story_id")),
                    "query_family": fam, "query": q,
                    "author_hash": hashlib.md5(("hn:" + str(h.get("author"))).encode()).hexdigest()[:10],
                    "source_date": datetime.fromtimestamp(h.get("created_at_i", 0), timezone.utc).date().isoformat(),
                    "collection_date": datetime.now(timezone.utc).date().isoformat(),
                    "story_title": h.get("story_title") or "",
                    "source_url": f"https://news.ycombinator.com/item?id={oid}",
                    "text": txt[:1200],
                })
                kept += 1
            log.append([fam, q, "OK", f"{len(hits)} hits / {kept} kept", datetime.now(timezone.utc).date().isoformat()])
            time.sleep(0.4)
    with open(RAW, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    with open(SEARCHLOG, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["query_family", "query", "status", "result", "search_date"])
        w.writerows(log)
    # time strata
    from collections import Counter
    strata = Counter()
    for r in rows:
        y = int(r["source_date"][:4])
        strata["pre-2023" if y < 2023 else ("2023-2024" if y < 2025 else "2025-2026")] += 1
    print(f"retrieved {len(rows)} unique HN comments across {len(seen)} ids")
    print("query families:", {fam: sum(1 for r in rows if r['query_family'] == fam) for fam in QUERY_FAMILIES})
    print("time strata:", dict(strata))
    print(f"raw -> {RAW}; search log -> {SEARCHLOG}")


if __name__ == "__main__":
    main()
