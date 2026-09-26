"""Turn classified news + price features into one 0-100 score per stock, and pick the top few."""
import math
from collections import defaultdict
from datetime import datetime

from .models import Candidate, NewsItem

HALF_LIFE_HOURS = 12   # a headline's weight halves every 12 hours


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def news_raw(items: list[NewsItem], source_weights: dict, now: datetime) -> float:
    """Signed news strength: sentiment x impact x source trust x recency, plus a small breadth bonus."""
    total = 0.0
    for it in items:
        age_h = max(0.0, (now - datetime.fromisoformat(it.published)).total_seconds() / 3600)
        decay = 0.5 ** (age_h / HALF_LIFE_HOURS)
        total += it.sentiment * (it.impact / 3) * source_weights.get(it.source, 0.5) * decay
    outlets = {it.outlet for it in items if it.sentiment > 0}
    return total * (1 + 0.15 * max(0, len(outlets) - 1))   # confirmed by several outlets


def news_score(raw: float) -> float:
    return round(100 * (1 - math.exp(-max(raw, 0) / 0.6)), 1)


def reach_score(rate: float | None) -> float:
    return 50.0 if rate is None else round(100 * clamp((rate - 0.2) / 0.6), 1)


def momentum_score(change: float | None, max_change: float) -> float:
    """Best when the stock is already moving up modestly (+0.5..3%); weak if falling or stretched."""
    if change is None:
        return 50.0
    if change < -2:
        return 0.0
    if change < 0:
        return round(40 + 20 * change / 2, 1)            # -2%..0 -> 20..40
    if change <= 2:
        return round(40 + 30 * change, 1)                # 0..2% -> 40..100
    return round(100 - 60 * clamp((change - 2) / max(max_change - 2, 0.1)), 1)   # fades to 40


def volume_score(ratio: float | None) -> float:
    if not ratio:
        return 40.0
    return round(100 * clamp((math.log2(ratio) + 1) / 3), 1)   # 0.5x -> 0, 1x -> 33, 4x -> 100


def build_candidates(items: list[NewsItem], names: dict, cfg: dict, now: datetime) -> list[Candidate]:
    by_symbol = defaultdict(list)
    for it in items:
        for sym in it.symbols:
            by_symbol[sym].append(it)
    candidates = []
    for sym, news in by_symbol.items():
        raw = news_raw(news, cfg["source_weights"], now)
        if raw <= 0:
            continue   # only stocks whose news is net positive
        best = max(news, key=lambda it: it.sentiment * it.impact)
        candidates.append(Candidate(
            symbol=sym, name=names.get(sym, sym), news_ids=[it.id for it in news],
            news_score=news_score(raw), headline=best.title,
            catalysts=sorted({it.catalyst for it in news if it.sentiment > 0 and it.catalyst}),
        ))
    return sorted(candidates, key=lambda c: c.news_score, reverse=True)


def apply_prices(c: Candidate, f: dict | None, cfg: dict) -> None:
    if f is None:
        c.skip_reason = "no price data"
        return
    for key in ("price", "prev_close", "day_change_pct", "volume_ratio", "avg_traded_value_cr", "reach_rate"):
        setattr(c, key, f[key])
    c.target_price = round(c.price * (1 + cfg["target_pct"] / 100), 2)
    if c.price < cfg["min_price"]:
        c.skip_reason = f"price below Rs {cfg['min_price']:.0f}"
    elif c.avg_traded_value_cr < cfg["min_traded_value_cr"]:
        c.skip_reason = f"illiquid (Rs {c.avg_traded_value_cr} cr/day)"
    elif c.day_change_pct > cfg["max_day_change_pct"]:
        c.skip_reason = f"already up {c.day_change_pct}% today"


def score(c: Candidate, cfg: dict) -> None:
    w = cfg["weights"]
    c.scores = {
        "news": c.news_score,
        "reach": reach_score(c.reach_rate),
        "momentum": momentum_score(c.day_change_pct, cfg["max_day_change_pct"]),
        "volume": volume_score(c.volume_ratio),
    }
    c.score = round(sum(c.scores[k] * w[k] for k in w), 1)


def rank(candidates: list[Candidate], cfg: dict) -> list[Candidate]:
    ordered = sorted(candidates, key=lambda c: (c.skip_reason == "", c.score), reverse=True)
    picks = 0
    for i, c in enumerate(ordered, 1):
        c.rank = i
        if not c.skip_reason and picks < cfg["top_n"] and c.news_score >= cfg.get("min_news_score", 20):
            c.is_pick, picks = True, picks + 1
    return ordered
