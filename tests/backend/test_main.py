"""API tests. The raw zone and Databricks are always mocked: these test routing, the Gold-or-raw
fallback and the raw analytics maths, not whether GitHub or the warehouse is reachable."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend import raw
from backend.main import app

client = TestClient(app)

CANDIDATES = [
    {"date": "2026-09-28", "symbol": "AAA", "name": "Aaa", "rank": 1, "is_pick": True, "score": 70,
     "catalysts": ["order_win"], "price": 100, "news_ids": ["n1"]},
    {"date": "2026-09-28", "symbol": "BBB", "name": "Bbb", "rank": 2, "is_pick": True, "score": 50,
     "catalysts": ["results"], "price": 100, "news_ids": ["n2"]},
    {"date": "2026-09-28", "symbol": "CCC", "name": "Ccc", "rank": 3, "is_pick": False, "score": 30,
     "catalysts": [], "price": 100, "news_ids": []},
    {"date": "2026-09-29", "symbol": "AAA", "name": "Aaa", "rank": 1, "is_pick": True, "score": 66,
     "catalysts": ["order_win"], "price": 101, "news_ids": []},
]
OUTCOMES = [
    {"date": "2026-09-28", "symbol": "AAA", "hit": True, "max_gain_pct": 1.8, "close_return_pct": 0.5, "next_date": "2026-09-29"},
    {"date": "2026-09-28", "symbol": "BBB", "hit": False, "max_gain_pct": 0.4, "close_return_pct": -1.0, "next_date": "2026-09-29"},
    {"date": "2026-09-28", "symbol": "CCC", "hit": True, "max_gain_pct": 1.1, "close_return_pct": 0.2, "next_date": "2026-09-29"},
]
NEWS = [
    {"date": "2026-09-28", "id": "n1", "source": "nse", "symbols": ["AAA"], "published": "2026-09-28T10:00:00+05:30"},
    {"date": "2026-09-28", "id": "n2", "source": "reddit", "symbols": ["BBB"], "published": "2026-09-28T11:00:00+05:30"},
    {"date": "2026-09-29", "id": "n3", "source": "rss", "symbols": ["AAA"], "published": "2026-09-29T09:00:00+05:30"},
]
LATEST = {"market_date": "2026-09-29", "brief": "b", "candidates": CANDIDATES[3:], "news": NEWS[2:]}
FILES = {"latest.json": LATEST, "candidates.jsonl": CANDIDATES, "outcomes.jsonl": OUTCOMES, "news.jsonl": NEWS}


@pytest.fixture(autouse=True)
def raw_zone():
    with patch.object(raw, "_get", side_effect=FILES.__getitem__), \
         patch("backend.db.gold", return_value=None):   # warehouse asleep unless a test says otherwise
        yield


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_today_comes_from_raw_without_news():
    body = client.get("/api/today").json()
    assert body["source"] == "raw" and body["data"]["market_date"] == "2026-09-29"
    assert "news" not in body["data"]


def test_news_filters():
    assert [n["id"] for n in client.get("/api/news", params={"days": 5}).json()["data"]] == ["n3", "n2", "n1"]
    assert [n["id"] for n in client.get("/api/news", params={"days": 5, "symbol": "aaa"}).json()["data"]] == ["n3", "n1"]
    assert [n["id"] for n in client.get("/api/news").json()["data"]] == ["n3", "n2", "n1"]
    assert client.get("/api/news", params={"days": 1}).json()["data"][0]["id"] == "n3"


def test_track_record_falls_back_to_raw():
    body = client.get("/api/track-record").json()
    assert body["source"] == "raw"
    (day,) = body["data"]   # 2026-09-29 is not graded yet
    assert (day["picks"], day["pick_hits"], day["pick_hit_rate"], day["other_hit_rate"]) == (2, 1, 50.0, 100.0)


def test_track_record_prefers_gold():
    with patch("backend.db.gold", return_value=[{"trade_date": "2026-09-28", "picks": 9}]):
        body = client.get("/api/track-record").json()
    assert body == {"source": "databricks", "data": [{"trade_date": "2026-09-28", "picks": 9}]}


def test_analytics_raw_maths():
    data = client.get("/api/analytics").json()["data"]
    by_source = {r["source"]: r for r in data["by_source"]}
    assert by_source["nse"]["hit_rate"] == 100.0 and by_source["reddit"]["hit_rate"] == 0.0
    bands = {r["score_band"]: r["trades"] for r in data["by_score_band"]}
    assert bands == {"<35": 1, "45-55": 1, "65+": 1}
    cats = {(r["catalyst"], r["is_pick"]): r["hits"] for r in data["by_catalyst"]}
    assert cats[("order_win", True)] == 1 and cats[("none", False)] == 1


def test_history_marks_ungraded():
    rows = client.get("/api/history").json()["data"]
    assert rows[0]["trade_date"] == "2026-09-29" and rows[0]["graded"] is False
    assert {r["symbol"] for r in rows if r["graded"]} == {"AAA", "BBB", "CCC"}


def test_stock_validates_symbol():
    assert client.get("/api/stock/bad$ymbol").status_code == 400


def test_stock_combines_chart_and_radar_history():
    chart = {"meta": {"regularMarketPrice": 102.5}, "bars": [{"date": "2026-09-29", "close": 102.5}]}
    with patch("backend.main.fetch_chart", return_value=chart):
        data = client.get("/api/stock/AAA").json()["data"]
    assert data["price"] == 102.5 and data["name"] == "Aaa"
    assert [a["trade_date"] for a in data["appearances"]] == ["2026-09-29", "2026-09-28"]
    assert [n["id"] for n in data["news"]] == ["n3", "n1"]
