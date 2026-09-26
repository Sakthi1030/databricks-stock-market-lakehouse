"""CLI: `python -m radar run` (the 2 PM job) and `python -m radar outcomes` (after the close)."""
import argparse
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from . import classify, outcomes, prices, report, scoring, sources, store
from .universe import load_universe

log = logging.getLogger("radar")
IST = ZoneInfo("Asia/Kolkata")
ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path = ROOT / "config" / "radar.yaml") -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def wait_until(hhmm: str) -> None:
    """Hold until the snapshot time so prices reflect 2 PM (GitHub cron often starts a bit early or late)."""
    h, m = map(int, hhmm.split(":"))
    now = datetime.now(IST)
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if now < target:
        log.info("Waiting %.0fs until %s IST for the price snapshot", (target - now).total_seconds(), hhmm)
        time.sleep((target - now).total_seconds())


def run(cfg: dict, data_dir: Path, force: bool, wait: bool, send: bool, test_email: bool) -> dict | None:
    now = datetime.now(IST)
    today = now.date()
    if not force and not prices.market_open_today(today):
        log.info("NSE is closed today (%s); nothing to do", today)
        return None

    universe = load_universe(cfg["series"])
    log.info("Universe: %d NSE stocks", len(universe))
    news = sources.collect(cfg, now)
    log.info("Collected %d unique headlines: %s", len(news),
             {s: sum(n.source == s for n in news) for s in ("nse", "rss", "google_news", "reddit")})
    classify.classify(news, universe, cfg["gemini"])

    if wait:
        wait_until(cfg["snapshot_time"])
    now = datetime.now(IST)
    candidates = scoring.build_candidates(news, universe.names, cfg, now)
    shortlist = candidates[: cfg["watchlist_n"] * 3]   # price the strongest news only
    with ThreadPoolExecutor(max_workers=8) as pool:
        feats = list(pool.map(lambda c: prices.features(c.symbol, today, now, cfg["target_pct"]), shortlist))
    sparklines = {}
    for c, f in zip(shortlist, feats):
        scoring.apply_prices(c, f, cfg)
        scoring.score(c, cfg)
        if f:
            sparklines[c.symbol] = f["sparkline"]
    ranked = scoring.rank(shortlist, cfg)[: cfg["watchlist_n"]]

    kept = {i for c in ranked for i in c.news_ids}
    run_record = {
        "market_date": today.isoformat(),
        "run_at": now.isoformat(),
        "target_pct": cfg["target_pct"],
        "indices": prices.index_snapshot(today),
        "stats": {"headlines": len(news), "matched_stocks": len(candidates),
                  "by_source": {s: sum(n.source == s for n in news) for s in ("nse", "rss", "google_news", "reddit")},
                  "classified_by_gemini": sum(n.classified_by == "gemini" for n in news)},
        "candidates": [{**c.to_dict(), "sparkline": sparklines.get(c.symbol, [])} for c in ranked],
        # All company-specific or high-impact headlines, for the site's news feed.
        "news": [n.to_dict() for n in news if n.id in kept or n.symbols or n.impact >= 2],
    }
    run_record["brief"] = report.market_brief(run_record, cfg["gemini"])
    record = outcomes.track_record(data_dir)
    run_record["track_record"] = record
    store.save_run(data_dir, run_record)
    picks = [c.symbol for c in ranked if c.is_pick]
    log.info("Picks: %s", ", ".join(picks) or "none")
    if send or test_email:
        report.send_email(run_record, record, test=test_email)
    return run_record


def main() -> None:
    parser = argparse.ArgumentParser(prog="radar")
    parser.add_argument("mode", choices=["run", "outcomes"])
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--force", action="store_true", help="run even if NSE is closed today")
    parser.add_argument("--no-wait", action="store_true", help="don't wait for the snapshot time")
    parser.add_argument("--send", action="store_true", help="email the picks")
    parser.add_argument("--test-email", action="store_true", help="send, marked [TEST]")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_config()
    if args.mode == "run":
        run(cfg, args.data_dir, args.force, not args.no_wait, args.send, args.test_email)
    else:
        outcomes.update_outcomes(args.data_dir, datetime.now(IST), cfg["target_pct"])
