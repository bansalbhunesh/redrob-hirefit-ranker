"""Study Phi-2 -- REAL retrieval of two additional ToS-clean strata:
 (1) Workplace Stack Exchange (CC-BY-SA, official API): structured HR/workplace-POLICY
     reasoning -- the recruiter/process perspective HN lacks. Each voted ANSWER = one
     opinion unit (the actual advice); question = scenario context; thread_id = question id.
 (2) more Hacker News anachronism-targeted queries to deliberately expand that cell.

ToS/content: SE content is CC-BY-SA (attribution via stored URL); store short excerpts only,
hash authors, no model training. Recruiter-Reddit and India-Reddit strata are NOT bulk-
retrieved (Reddit ToS) -> they remain frozen protocol awaiting appropriate access.
"""
import gzip
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("docs/human_opinion")
RAW2 = OUT / "raw_phi2_corpus.jsonl"

SE_QUERIES = {
    "recruiter_policy": ["resume inconsistency hiring decision", "exaggerated years of experience candidate"],
    "background_check": ["employment dates discrepancy background check", "employment verification mismatch offer"],
    "overlap_india": ["overlapping employment dual employment", "experience letter discrepancy India"],
    "tech_anachronism": ["candidate claims more experience than technology exists", "inflated years technology resume"],
}
HN_ANACHRONISM = ["claims years kubernetes experience", "rag llm experience resume inflated",
                  "cloud experience predates launch", "framework experience longer than exists"]


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "phi-research/1.0", "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return json.loads(raw)


def strip_html(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    for a, b in [("&#39;", "'"), ("&quot;", '"'), ("&gt;", ">"), ("&lt;", "<"), ("&amp;", "&")]:
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def fetch_se(query, fam, rows, seen):
    base = "https://api.stackexchange.com/2.3"
    url = (f"{base}/search/advanced?order=desc&sort=relevance&q={urllib.parse.quote(query)}"
           f"&site=workplace&pagesize=5&filter=withbody")
    d = _get(url)
    qids = [it["question_id"] for it in d.get("items", []) if it.get("answer_count", 0) > 0][:5]
    qmeta = {it["question_id"]: it for it in d.get("items", [])}
    if not qids:
        return
    ids = ";".join(str(q) for q in qids)
    au = (f"{base}/questions/{ids}/answers?order=desc&sort=votes&site=workplace"
          f"&pagesize=20&filter=withbody")
    ans = _get(au)
    per_q = {}
    for a in ans.get("items", []):
        per_q.setdefault(a["question_id"], []).append(a)
    for qid in qids:
        for a in (per_q.get(qid, [])[:2]):  # top-2 voted answers per question
            oid = f"SE_{a['answer_id']}"
            if oid in seen:
                continue
            seen.add(oid)
            body = strip_html(a.get("body"))
            if len(body) < 150:
                continue
            rows.append({
                "item_id": oid, "platform": "workplace.stackexchange", "thread_id": f"SEQ_{qid}",
                "query_family": fam, "query": query,
                "author_hash": hashlib.md5(("se:" + str(a.get("owner", {}).get("display_name"))).encode()).hexdigest()[:10],
                "source_date": datetime.fromtimestamp(a.get("creation_date", 0), timezone.utc).date().isoformat(),
                "collection_date": datetime.now(timezone.utc).date().isoformat(),
                "story_title": strip_html(qmeta.get(qid, {}).get("title", ""))[:160],
                "answer_score": a.get("score"), "is_accepted": a.get("is_accepted"),
                "source_url": f"https://workplace.stackexchange.com/a/{a['answer_id']}",
                "text": body[:1400],
            })


def fetch_hn(query, rows, seen):
    url = ("https://hn.algolia.com/api/v1/search?" +
           urllib.parse.urlencode({"query": query, "tags": "comment", "hitsPerPage": 12}))
    d = _get(url)
    for h in d.get("hits", []):
        oid = f"HN_{h.get('objectID')}"
        txt = strip_html(h.get("comment_text"))
        if oid in seen or len(txt) < 120:
            continue
        seen.add(oid)
        rows.append({
            "item_id": oid, "platform": "hackernews", "thread_id": str(h.get("story_id")),
            "query_family": "tech_anachronism", "query": query,
            "author_hash": hashlib.md5(("hn:" + str(h.get("author"))).encode()).hexdigest()[:10],
            "source_date": datetime.fromtimestamp(h.get("created_at_i", 0), timezone.utc).date().isoformat(),
            "collection_date": datetime.now(timezone.utc).date().isoformat(),
            "story_title": h.get("story_title") or "", "answer_score": h.get("points"),
            "is_accepted": None, "source_url": f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "text": txt[:1400]})


def main():
    rows, seen = [], set()
    for fam, qs in SE_QUERIES.items():
        for q in qs:
            try:
                fetch_se(q, fam, rows, seen)
            except Exception as e:
                print("SE err", q, str(e)[:60])
            time.sleep(0.5)
    for q in HN_ANACHRONISM:
        try:
            fetch_hn(q, rows, seen)
        except Exception as e:
            print("HN err", q, str(e)[:60])
        time.sleep(0.4)
    with open(RAW2, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    from collections import Counter
    print(f"retrieved {len(rows)} new units")
    print("by platform:", dict(Counter(r["platform"] for r in rows)))
    print("by family:", dict(Counter(r["query_family"] for r in rows)))
    print(f"raw -> {RAW2}")


if __name__ == "__main__":
    main()
