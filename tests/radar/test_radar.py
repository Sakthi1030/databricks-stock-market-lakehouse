"""Unit tests for the radar pipeline's pure logic (no network)."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from radar import scoring
from radar.classify import classify_with_keywords
from radar.models import Candidate, NewsItem
from radar.outcomes import grade
from radar.prices import reach_rate, session_fraction
from radar.sources import parse_feed, to_ist
from radar.universe import Universe, normalize

IST = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 9, 25, 14, 0, tzinfo=IST)
UNIVERSE = Universe([
    {"symbol": "TATAMOTORS", "name": "Tata Motors Limited"},
    {"symbol": "RAILTEL", "name": "RailTel Corporation of India Limited"},
    {"symbol": "M&M", "name": "Mahindra & Mahindra Limited"},
])
CFG = {"target_pct": 1.0, "min_price": 10, "min_traded_value_cr": 1.0, "max_day_change_pct": 6.0,
       "top_n": 2, "min_news_score": 20, "source_weights": {"nse": 1.0, "rss": 0.8, "reddit": 0.5},
       "weights": {"news": 0.45, "reach": 0.25, "momentum": 0.15, "volume": 0.15}}


def news(sentiment=0.8, impact=3, hours_ago=1, source="nse", outlet="NSE filing", symbols=("TATAMOTORS",)):
    return NewsItem(source=source, outlet=outlet, title=f"t{hours_ago}{outlet}", url="",
                    published=(NOW - timedelta(hours=hours_ago)).isoformat(),
                    symbols=list(symbols), sentiment=sentiment, impact=impact, catalyst="order_win")


def test_normalize_and_resolve():
    assert normalize("Mahindra & Mahindra Limited") == "mahindra and mahindra"
    assert UNIVERSE.resolve("TATAMOTORS.NS") == "TATAMOTORS"
    assert UNIVERSE.resolve("", "Tata Motors Ltd.") == "TATAMOTORS"
    assert UNIVERSE.resolve("WRONG", "RailTel Corporation of India") == "RAILTEL"
    assert UNIVERSE.resolve("", "Unknown Co") is None


def test_parse_rss_and_atom():
    rss = b"""<rss><channel><item><title>A &amp; B</title><link>http://x</link>
      <pubDate>Fri, 25 Sep 2026 10:00:00 +0530</pubDate><description>&lt;p&gt;hi&lt;/p&gt;</description>
      <source url="u">Mint</source></item></channel></rss>"""
    atom = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Post</title>
      <link href="http://r"/><updated>2026-09-25T04:30:00+00:00</updated></entry></feed>"""
    (a,) = parse_feed(rss)
    assert (a["title"], a["summary"], a["outlet"]) == ("A & B", "hi", "Mint")
    (b,) = parse_feed(atom)
    assert b["url"] == "http://r"
    assert to_ist(b["published"]).hour == 10   # 04:30 UTC = 10:00 IST


def test_news_score_rewards_fresh_strong_positive_news():
    fresh = scoring.news_raw([news(hours_ago=1)], CFG["source_weights"], NOW)
    stale = scoring.news_raw([news(hours_ago=24)], CFG["source_weights"], NOW)
    weak = scoring.news_raw([news(impact=1)], CFG["source_weights"], NOW)
    bad = scoring.news_raw([news(sentiment=-0.8)], CFG["source_weights"], NOW)
    assert fresh > weak > 0 and fresh > stale * 3 and bad < 0
    assert 0 < scoring.news_score(fresh) <= 100 and scoring.news_score(bad) == 0


def test_breadth_bonus_for_several_outlets():
    one = scoring.news_raw([news(outlet="A"), news(outlet="A")], CFG["source_weights"], NOW)
    two = scoring.news_raw([news(outlet="A"), news(outlet="B")], CFG["source_weights"], NOW)
    assert two > one


def test_momentum_prefers_modest_rise():
    m = lambda x: scoring.momentum_score(x, 6.0)
    assert m(-3) == 0 and m(0) == 40 and m(2) == 100
    assert m(1) > m(0) > m(-1) and m(5) < m(2) and m(6) == 40


def test_volume_score():
    assert scoring.volume_score(0.5) == 0 and scoring.volume_score(4) == 100
    assert 30 < scoring.volume_score(1) < 35


def test_candidates_guards_and_ranking():
    items = [news(symbols=["TATAMOTORS"]), news(symbols=["RAILTEL"]), news(sentiment=-0.9, symbols=["M&M"])]
    cands = scoring.build_candidates(items, UNIVERSE.names, CFG, NOW)
    assert {c.symbol for c in cands} == {"TATAMOTORS", "RAILTEL"}   # negative news is not a candidate
    base = {"price": 100, "prev_close": 99, "day_change_pct": 1.0, "volume_ratio": 2.0,
            "avg_traded_value_cr": 50, "reach_rate": 0.6}
    tata, rail = sorted(cands, key=lambda c: c.symbol)[::-1]
    scoring.apply_prices(tata, base, CFG)
    scoring.apply_prices(rail, {**base, "day_change_pct": 8.0}, CFG)
    assert tata.target_price == 101.0 and tata.skip_reason == ""
    assert rail.skip_reason.startswith("already up")
    for c in cands:
        scoring.score(c, CFG)
    ranked = scoring.rank(cands, CFG)
    assert ranked[0].symbol == "TATAMOTORS" and ranked[0].is_pick and not ranked[1].is_pick


def test_illiquid_and_penny_guards():
    c = Candidate("X", "X")
    scoring.apply_prices(c, {"price": 50, "prev_close": 50, "day_change_pct": 0, "volume_ratio": 1,
                             "avg_traded_value_cr": 0.3, "reach_rate": 0.5}, CFG)
    assert c.skip_reason.startswith("illiquid")
    scoring.apply_prices(c, {"price": 5, "prev_close": 5, "day_change_pct": 0, "volume_ratio": 1,
                             "avg_traded_value_cr": 9, "reach_rate": 0.5}, CFG)
    assert c.skip_reason.startswith("price below")


def test_reach_rate_and_grade():
    bars = [{"close": 100, "high": 100}] * 10 + [{"close": 100, "high": 101.5}] * 15
    assert round(reach_rate(bars, 1.0), 3) == round(15 / 24, 3)
    assert reach_rate(bars[:10], 1.0) is None
    hit = grade(100, {"date": "2026-09-26", "open": 99, "high": 101.2, "close": 100.5}, 1.0)
    miss = grade(100, {"date": "2026-09-26", "open": 99, "high": 100.8, "close": 99}, 1.0)
    assert hit["hit"] and not miss["hit"] and hit["max_gain_pct"] == 1.2


def test_session_fraction():
    assert session_fraction(NOW.replace(hour=9, minute=0)) == 0.1
    assert session_fraction(NOW.replace(hour=14, minute=0)) == 0.76
    assert session_fraction(NOW.replace(hour=16, minute=0)) == 1.0


def test_keyword_fallback():
    items = [NewsItem("rss", "ET", "Tata Motors bags Rs 500 crore order from defence ministry", "u", NOW.isoformat()),
             NewsItem("rss", "ET", "Tata Motors shares plunge after probe", "u2", NOW.isoformat()),
             NewsItem("reddit", "r/ISB", "Tata Motors wins huge contract, to the moon", "u3", NOW.isoformat())]
    classify_with_keywords(items, UNIVERSE)
    good, bad, hype = items
    assert good.symbols == ["TATAMOTORS"] and good.catalyst == "order_win" and good.sentiment > 0
    assert bad.sentiment < 0
    assert hype.catalyst == "buzz" and hype.impact <= 1
