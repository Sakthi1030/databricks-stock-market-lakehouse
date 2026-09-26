"""Bronze -> Silver -> Gold on a local Spark + Delta session, from small raw files."""
import json

import pytest

pytest.importorskip("pyspark")
pytest.importorskip("delta")

from lakehouse import pipeline  # noqa: E402

SCHEMA = "radar_test"


def cand(date, symbol, score, is_pick, rank, catalysts=("order_win",)):
    return {"date": date, "symbol": symbol, "name": symbol.title(), "news_ids": [f"n-{date}-{symbol}"],
            "news_score": 60.0, "reach_rate": 0.6, "day_change_pct": 1.0, "volume_ratio": 2.0,
            "avg_traded_value_cr": 50.0, "price": 100.0, "prev_close": 99.0, "target_price": 101.0,
            "scores": {"news": 60.0, "reach": 67.0, "momentum": 70.0, "volume": 67.0}, "score": score,
            "rank": rank, "is_pick": is_pick, "skip_reason": "", "catalysts": list(catalysts),
            "headline": "h", "sparkline": [99.0, 100.0]}


def outcome(date, symbol, hit, gain):
    return {"date": date, "symbol": symbol, "entry": 100.0, "is_pick": None, "score": None, "catalysts": [],
            "next_date": "2026-09-30", "next_open": 100.0, "next_high": 100 + gain, "next_close": 100.0,
            "hit": hit, "max_gain_pct": gain, "close_return_pct": 0.0, "open_gap_pct": 0.0,
            "graded_at": "2026-09-30T15:45:00+05:30"}


def news(date, symbol, source):
    return {"date": date, "id": f"n-{date}-{symbol}", "source": source, "outlet": "x", "title": "t", "url": "u",
            "published": f"{date}T10:00:00+05:30", "summary": "", "symbols": [symbol], "category": "",
            "sentiment": 0.8, "impact": 3, "catalyst": "order_win", "reason": "", "classified_by": "gemini"}


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


@pytest.fixture(scope="module")
def spark():
    session = pipeline.get_spark("pytest")
    yield session
    session.sql(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
    session.stop()


@pytest.fixture(scope="module")
def built(spark, tmp_path_factory):
    landing = tmp_path_factory.mktemp("landing")
    d1, d2 = "2026-09-28", "2026-09-29"
    write_jsonl(landing / "candidates.jsonl", [
        cand(d1, "AAA", 70, True, 1), cand(d1, "BBB", 50, True, 2, ["results"]), cand(d1, "CCC", 30, False, 3),
        cand(d2, "AAA", 66, True, 1), cand(d2, "DDD", 40, False, 2),
        cand(d2, "DDD", 41, False, 2),   # duplicate key: Silver must keep one row
    ])
    write_jsonl(landing / "outcomes.jsonl", [
        outcome(d1, "AAA", True, 1.8), outcome(d1, "BBB", False, 0.4), outcome(d1, "CCC", True, 1.1),
    ])
    write_jsonl(landing / "news.jsonl", [news(d1, "AAA", "nse"), news(d1, "BBB", "reddit"), news(d1, "CCC", "nse")])
    write_jsonl(landing / "runs.jsonl", [{
        "market_date": d1, "run_at": f"{d1}T14:00:00+05:30", "target_pct": 1.0, "brief": "b",
        "indices_json": json.dumps({"NIFTY 50": {"price": 1.0, "change_pct": 0.5}}),
        "stats_json": json.dumps({"headlines": 300, "matched_stocks": 40})}])
    pipeline.run_bronze(spark, SCHEMA, landing, download=False)
    pipeline.run_silver(spark, SCHEMA)
    pipeline.run_gold(spark, SCHEMA)
    return spark


def rows(spark, table):
    return [r.asDict() for r in spark.table(f"{SCHEMA}.{table}").collect()]


def test_silver_dedupes_candidates(built):
    assert built.table(f"{SCHEMA}.silver_candidates").count() == 5


def test_pick_performance_marks_ungraded(built):
    perf = {(str(r["trade_date"]), r["symbol"]): r for r in rows(built, "gold_pick_performance")}
    assert perf[("2026-09-28", "AAA")]["graded"] and perf[("2026-09-28", "AAA")]["score_band"] == "65+"
    assert not perf[("2026-09-29", "AAA")]["graded"]


def test_track_record_compares_picks_with_others(built):
    (day,) = rows(built, "gold_track_record_daily")
    assert (day["picks"], day["pick_hits"], day["pick_hit_rate"]) == (2, 1, 50.0)
    assert (day["others"], day["other_hit_rate"]) == (1, 100.0)
    assert day["rolling_20d_pick_hit_rate"] == 50.0


def test_hit_rate_by_source_and_catalyst(built):
    by_source = {r["source"]: r for r in rows(built, "gold_hit_rate_by_source")}
    assert by_source["nse"]["trades"] == 2 and by_source["nse"]["hit_rate"] == 100.0
    assert by_source["reddit"]["hit_rate"] == 0.0
    by_cat = {(r["catalyst"], r["is_pick"]): r for r in rows(built, "gold_hit_rate_by_catalyst")}
    assert by_cat[("order_win", True)]["hits"] == 1 and by_cat[("results", True)]["hits"] == 0


def test_market_days(built):
    days = {str(r["trade_date"]): r for r in rows(built, "gold_market_days")}
    assert days["2026-09-28"]["nifty_change_pct"] == 0.5 and days["2026-09-28"]["top_pick"] == "AAA"
