"""Prices from Yahoo Finance's chart API (NSE symbols carry a .NS suffix)."""
import logging
from datetime import date, datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

from .http import get_json

log = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")
CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{}"


def yahoo_symbol(symbol: str) -> str:
    return symbol if symbol.startswith("^") else f"{symbol}.NS"


def fetch_chart(symbol: str, range_: str = "6mo", interval: str = "1d") -> dict:
    """{'meta': {...}, 'bars': [{'date', 'open', 'high', 'low', 'close', 'volume'}]} (IST dates)."""
    data = get_json(CHART.format(quote(yahoo_symbol(symbol))),
                    params={"range": range_, "interval": interval}, retries=2)
    result = data["chart"]["result"][0]
    quote_ = result["indicators"]["quote"][0]
    bars = []
    for i, ts in enumerate(result.get("timestamp") or []):
        o, h, l, c, v = (quote_[k][i] for k in ("open", "high", "low", "close", "volume"))
        if None in (o, h, l, c):
            continue
        when = datetime.fromtimestamp(ts, IST)
        bars.append({"date": when.date().isoformat(), "time": when.isoformat(),
                     "open": round(o, 2), "high": round(h, 2), "low": round(l, 2), "close": round(c, 2),
                     "volume": v or 0})
    return {"meta": result["meta"], "bars": bars}


def reach_rate(bars: list[dict], target_pct: float, lookback: int = 120) -> float | None:
    """Share of days on which the NEXT day's high reached close * (1 + target)."""
    bars = bars[-(lookback + 1):]
    if len(bars) < 21:
        return None
    hits = sum(1 for a, b in zip(bars, bars[1:]) if b["high"] >= a["close"] * (1 + target_pct / 100))
    return hits / (len(bars) - 1)


def session_fraction(now: datetime) -> float:
    """How much of the 09:15-15:30 session has elapsed (for comparing volume so far)."""
    minutes = (now.hour * 60 + now.minute) - (9 * 60 + 15)
    return max(0.1, min(1.0, minutes / 375))


def features(symbol: str, today: date, now: datetime, target_pct: float) -> dict | None:
    try:
        chart = fetch_chart(symbol)
    except Exception as exc:
        log.info("No price data for %s: %s", symbol, exc)
        return None
    bars, meta = chart["bars"], chart["meta"]
    if len(bars) < 22:
        return None
    done = [b for b in bars if b["date"] < today.isoformat()]   # completed sessions only
    live = bars[-1] if bars[-1]["date"] == today.isoformat() else None
    prev_close = done[-1]["close"]
    price = meta.get("regularMarketPrice") or (live or done[-1])["close"]
    today_volume = (live or {}).get("volume") or 0
    last20 = done[-20:]
    avg_volume = sum(b["volume"] for b in last20) / len(last20)
    expected_so_far = avg_volume * session_fraction(now)
    return {
        "price": round(price, 2),
        "prev_close": round(prev_close, 2),
        "day_change_pct": round((price / prev_close - 1) * 100, 2),
        "volume_ratio": round(today_volume / expected_so_far, 2) if live and expected_so_far else None,
        "avg_traded_value_cr": round(sum(b["close"] * b["volume"] for b in last20) / len(last20) / 1e7, 2),
        "reach_rate": reach_rate(done, target_pct),
        "sparkline": [round(b["close"], 2) for b in done[-30:]] + ([round(price, 2)] if live else []),
    }


def market_open_today(today: date) -> bool:
    """True if NIFTY 50 printed a bar today (False on weekends and NSE holidays)."""
    try:
        bars = fetch_chart("^NSEI", range_="5d")["bars"]
        return bool(bars) and bars[-1]["date"] == today.isoformat()
    except Exception as exc:
        log.warning("Could not check the market calendar: %s", exc)
        return True   # when in doubt, run


def index_snapshot(today: date) -> dict:
    out = {}
    for name, sym in {"NIFTY 50": "^NSEI", "NIFTY Bank": "^NSEBANK", "Sensex": "^BSESN"}.items():
        try:
            chart = fetch_chart(sym, range_="1mo")
            done = [b for b in chart["bars"] if b["date"] < today.isoformat()]
            price = chart["meta"].get("regularMarketPrice") or chart["bars"][-1]["close"]
            out[name] = {"price": round(price, 2),
                         "change_pct": round((price / done[-1]["close"] - 1) * 100, 2),
                         "sparkline": [round(b["close"], 2) for b in chart["bars"]]}
        except Exception as exc:
            log.warning("Index %s failed: %s", name, exc)
    return out
