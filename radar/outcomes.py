"""Grade past candidates: did the next trading day's high reach the +target from the 2 PM price?"""
import logging
from datetime import datetime
from pathlib import Path

from .prices import fetch_chart
from .store import read_jsonl, upsert_jsonl

log = logging.getLogger(__name__)
SESSION_CLOSE = (15, 35)


def grade(entry: float, bar: dict, target_pct: float) -> dict:
    return {
        "next_date": bar["date"],
        "next_open": round(bar["open"], 2),
        "next_high": round(bar["high"], 2),
        "next_close": round(bar["close"], 2),
        "hit": bar["high"] >= entry * (1 + target_pct / 100),
        "max_gain_pct": round((bar["high"] / entry - 1) * 100, 2),
        "close_return_pct": round((bar["close"] / entry - 1) * 100, 2),
        "open_gap_pct": round((bar["open"] / entry - 1) * 100, 2),
    }


def update_outcomes(data_dir: Path, now: datetime, target_pct: float) -> int:
    graded = {f"{o['date']}|{o['symbol']}" for o in read_jsonl(data_dir / "outcomes.jsonl")}
    pending = [c for c in read_jsonl(data_dir / "candidates.jsonl")
               if c.get("price") and f"{c['date']}|{c['symbol']}" not in graded]
    today = now.date().isoformat()
    closed = (now.hour, now.minute) >= SESSION_CLOSE
    charts, rows = {}, []
    for c in pending:
        if c["symbol"] not in charts:
            try:
                charts[c["symbol"]] = fetch_chart(c["symbol"], range_="3mo")["bars"]
            except Exception as exc:
                log.info("Outcome price fetch failed for %s: %s", c["symbol"], exc)
                charts[c["symbol"]] = []
        nxt = next((b for b in charts[c["symbol"]] if b["date"] > c["date"]), None)
        if nxt is None or (nxt["date"] == today and not closed):
            continue   # next session not finished yet
        rows.append({"date": c["date"], "symbol": c["symbol"], "entry": c["price"],
                     "is_pick": c.get("is_pick", False), "score": c.get("score"),
                     "catalysts": c.get("catalysts", []), **grade(c["price"], nxt, target_pct),
                     "graded_at": now.isoformat()})
    if rows:
        upsert_jsonl(data_dir / "outcomes.jsonl", rows, key=lambda r: f"{r['date']}|{r['symbol']}")
    log.info("Graded %d candidates (%d still waiting)", len(rows), len(pending) - len(rows))
    return len(rows)


def track_record(data_dir: Path, days: int = 30) -> dict:
    """Hit rate of the picks (and of the other candidates, for contrast) over recent trading days."""
    outcomes = read_jsonl(data_dir / "outcomes.jsonl")
    dates = sorted({o["date"] for o in outcomes})[-days:]
    recent = [o for o in outcomes if o["date"] in dates]
    picks = [o for o in recent if o["is_pick"]]
    others = [o for o in recent if not o["is_pick"]]
    rate = lambda rows: round(100 * sum(o["hit"] for o in rows) / len(rows), 1) if rows else None
    return {"days": len(dates), "picks": len(picks), "pick_hits": sum(o["hit"] for o in picks),
            "pick_hit_rate": rate(picks), "other_hit_rate": rate(others)}
