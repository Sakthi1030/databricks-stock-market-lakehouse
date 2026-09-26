"""Hot path and fallback: the raw zone on the repo's `data` branch, cached briefly in memory.

`today` always comes from here (fresh the moment the 2 PM run commits). The analytics below
mirror the Gold marts (lakehouse/gold.py) so the site still works while the warehouse sleeps.
"""
import json
import time
from collections import defaultdict

import requests

RAW = "https://raw.githubusercontent.com/Sakthi1030/databricks-stock-market-lakehouse/data"
TTL_SECONDS = 120
_cache: dict[str, tuple[float, object]] = {}

SCORE_BANDS = [(0, 35, "<35"), (35, 45, "35-45"), (45, 55, "45-55"), (55, 65, "55-65"), (65, 101, "65+")]


def _get(path: str):
    hit = _cache.get(path)
    if hit and time.time() - hit[0] < TTL_SECONDS:
        return hit[1]
    resp = requests.get(f"{RAW}/{path}", timeout=20)
    if resp.status_code == 404:
        value = {} if path.endswith(".json") else []
    else:
        resp.raise_for_status()
        value = (resp.json() if path.endswith(".json")
                 else [json.loads(line) for line in resp.text.splitlines() if line.strip()])
    _cache[path] = (time.time(), value)
    return value


def latest() -> dict:
    return _get("latest.json")


def candidates() -> list[dict]:
    return _get("candidates.jsonl")


def outcomes() -> list[dict]:
    return _get("outcomes.jsonl")


def news() -> list[dict]:
    return _get("news.jsonl")


def _band(score: float | None) -> str | None:
    return next((label for lo, hi, label in SCORE_BANDS if score is not None and lo <= score < hi), None)


def pick_performance() -> list[dict]:
    graded = {(o["date"], o["symbol"]): o for o in outcomes()}
    rows = []
    for c in candidates():
        o = graded.get((c["date"], c["symbol"]), {})
        rows.append({
            "trade_date": c["date"], "symbol": c["symbol"], "name": c["name"], "rank": c.get("rank"),
            "is_pick": bool(c.get("is_pick")), "score": c.get("score"), "score_band": _band(c.get("score")),
            "skip_reason": c.get("skip_reason", ""), "catalysts": c.get("catalysts", []),
            "headline": c.get("headline", ""), "price": c.get("price"), "target_price": c.get("target_price"),
            "day_change_pct": c.get("day_change_pct"), "reach_rate": c.get("reach_rate"),
            "graded": "hit" in o, "hit": o.get("hit"), "next_trade_date": o.get("next_date"),
            "next_high": o.get("next_high"), "max_gain_pct": o.get("max_gain_pct"),
            "close_return_pct": o.get("close_return_pct"),
        })
    return rows


def _rate(rows: list[dict]) -> dict:
    n = len(rows)
    hits = sum(1 for r in rows if r["hit"])
    avg = lambda k: round(sum(r[k] or 0 for r in rows) / n, 2) if n else None
    return {"trades": n, "hits": hits, "hit_rate": round(100 * hits / n, 1) if n else None,
            "avg_max_gain_pct": avg("max_gain_pct"), "avg_close_return_pct": avg("close_return_pct")}


def track_record_daily(perf: list[dict]) -> list[dict]:
    by_day = defaultdict(list)
    for r in perf:
        if r["graded"]:
            by_day[r["trade_date"]].append(r)
    out, window = [], []
    for day in sorted(by_day):
        picks = [r for r in by_day[day] if r["is_pick"]]
        others = [r for r in by_day[day] if not r["is_pick"]]
        window = (window + [(len(picks), sum(r["hit"] for r in picks))])[-20:]
        total = sum(p for p, _ in window)
        out.append({
            "trade_date": day, "picks": len(picks), "pick_hits": sum(r["hit"] for r in picks),
            "others": len(others), "other_hits": sum(r["hit"] for r in others),
            "pick_hit_rate": _rate(picks)["hit_rate"], "other_hit_rate": _rate(others)["hit_rate"],
            "pick_avg_max_gain_pct": _rate(picks)["avg_max_gain_pct"],
            "rolling_20d_pick_hit_rate": round(100 * sum(h for _, h in window) / total, 1) if total else None,
        })
    return out


def analytics(perf: list[dict], news_rows: list[dict]) -> dict:
    graded = [r for r in perf if r["graded"]]
    by_catalyst = defaultdict(list)
    for r in graded:
        for cat in r["catalysts"] or ["none"]:
            by_catalyst[(cat, r["is_pick"])].append(r)
    by_band = defaultdict(list)
    for r in graded:
        by_band[r["score_band"]].append(r)
    sources = defaultdict(set)
    for n in news_rows:
        for sym in n.get("symbols") or []:
            sources[(n["date"], sym)].add(n["source"])
    by_source = defaultdict(list)
    for r in graded:
        for src in sources.get((r["trade_date"], r["symbol"]), ()):
            by_source[src].append(r)
    return {
        "by_catalyst": sorted(({"catalyst": c, "is_pick": p, **_rate(rs)} for (c, p), rs in by_catalyst.items()),
                              key=lambda x: -x["trades"]),
        "by_score_band": [{"score_band": b, **_rate(by_band[b])} for _, _, b in SCORE_BANDS if by_band.get(b)],
        "by_source": sorted(({"source": s, **_rate(rs)} for s, rs in by_source.items()), key=lambda x: -x["trades"]),
    }
