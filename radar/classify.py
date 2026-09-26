"""Tag each headline with NSE symbols, sentiment, likely next-day impact and catalyst type.

Gemini (free tier) does the reading; a keyword fallback keeps the run useful when the API is
down or over quota, so the 2 PM alert never depends on it.
"""
import json
import logging
import os
import re
import time

from .http import get_json, post_json
from .models import NewsItem
from .universe import Universe, normalize

log = logging.getLogger(__name__)
API = "https://generativelanguage.googleapis.com/v1beta"

CATALYSTS = ["order_win", "results", "upgrade", "downgrade", "acquisition", "fund_raise",
             "buyback_dividend", "approval", "expansion", "partnership", "management",
             "legal_regulatory", "block_deal", "buzz", "macro", "other"]

PROMPT = """You are an Indian equity news analyst. For each numbered item below, say which
NSE-listed companies it is specifically about, and how it is likely to move each one's share
price on the NEXT trading day.

Rules:
- companies: only companies the item is specifically about; [] for market-wide or macro news.
  Give the NSE symbol if you know it, and always the company name.
- sentiment: -1.0 (clearly bearish) to 1.0 (clearly bullish) for those companies.
- impact: 0 = routine, no price effect; 1 = minor; 2 = clear company-specific news;
  3 = large relative to the company's size (big order vs revenue, strong results beat,
  major approval or acquisition).
- catalyst: one of {catalysts}.
- reason: at most 12 words.
- Reddit posts are opinions: treat hype without facts as catalyst "buzz", impact at most 1.

Reply with a JSON array only, one object per item:
[{{"i": 0, "companies": [{{"symbol": "TATAMOTORS", "name": "Tata Motors"}}], "sentiment": 0.6,
  "impact": 2, "catalyst": "order_win", "reason": "..."}}]

Items:
{items}"""


def resolve_model(preferred: str, key: str) -> str | None:
    """Use the configured model if available, else the newest stable Flash(-Lite) model."""
    try:
        models = get_json(f"{API}/models", params={"key": key, "pageSize": 200}).get("models", [])
    except Exception as exc:
        log.warning("Could not list Gemini models: %s", exc)
        return preferred
    usable = [m["name"].removeprefix("models/") for m in models
              if "generateContent" in m.get("supportedGenerationMethods", [])]
    if preferred in usable:
        return preferred
    stable = [n for n in usable if "flash" in n and not any(
        t in n for t in ("preview", "exp", "image", "tts", "audio", "live"))]
    lite = sorted((n for n in stable if "lite" in n), reverse=True)
    return (lite or sorted(stable, reverse=True) or [None])[0]


def gemini_json(prompt: str, model: str, key: str, retries: int = 4):
    data = post_json(f"{API}/models/{model}:generateContent?key={key}", {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
    }, retries=retries, timeout=90)
    return json.loads(data["candidates"][0]["content"]["parts"][0]["text"])


def _describe(i: int, item: NewsItem) -> str:
    known = f" [company: {item.symbols[0]}]" if item.symbols else ""
    summary = f" | {item.summary[:280]}" if item.summary and item.summary != item.title else ""
    return f"{i}. ({item.outlet}){known} {item.title}{summary}"


def classify_with_gemini(items: list[NewsItem], universe: Universe, cfg: dict) -> bool:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        log.info("GEMINI_API_KEY not set; using keyword classification")
        return False
    model = resolve_model(cfg["model"], key)
    if not model:
        return False
    log.info("Classifying %d items with %s", len(items), model)
    batch_size, done = cfg["batch_size"], 0
    for start in range(0, min(len(items), cfg["max_items"]), batch_size):
        batch = items[start:start + batch_size]
        prompt = PROMPT.format(catalysts=", ".join(CATALYSTS),
                               items="\n".join(_describe(i, it) for i, it in enumerate(batch)))
        try:
            results = gemini_json(prompt, model, key)
        except Exception as exc:
            log.warning("Gemini batch %d failed: %s", start // batch_size, exc)
            continue
        for r in results if isinstance(results, list) else []:
            try:
                item = batch[int(r["i"])]
            except (KeyError, ValueError, IndexError, TypeError):
                continue
            symbols = [s for c in r.get("companies") or []
                       if (s := universe.resolve(c.get("symbol", ""), c.get("name", "")))]
            item.symbols = list(dict.fromkeys(item.symbols + symbols))
            item.sentiment = max(-1.0, min(1.0, float(r.get("sentiment") or 0)))
            item.impact = max(0, min(3, int(r.get("impact") or 0)))
            item.catalyst = r.get("catalyst") if r.get("catalyst") in CATALYSTS else "other"
            item.reason = str(r.get("reason") or "")[:160]
            item.classified_by = "gemini"
            done += 1
        time.sleep(cfg["delay_seconds"])
    return done > 0


# --- keyword fallback -------------------------------------------------------------------

BULLISH = {
    "order_win": r"\b(bags?|wins?|won|secures?|receives?|bagged|awarded)\b.*\b(order|contract|project|deal)s?\b|\border (win|inflow)",
    "results": r"\b(profit|net income|revenue|ebitda)\b.*\b(jumps?|surges?|rises?|soars?|up|doubles?|beats?)\b|\brecord (profit|revenue)",
    "upgrade": r"\bupgrades?\b|\braises? target\b|\bbuy rating\b|\btarget price\b.*\bupside\b",
    "acquisition": r"\b(acquires?|acquisition|to buy stake|merger)\b",
    "buyback_dividend": r"\b(buyback|bonus issue|special dividend|stock split)\b",
    "approval": r"\b(approval|approves?|clearance|usfda nod|gets nod)\b",
    "expansion": r"\b(expansion|new plant|capacity|launch(es)?)\b",
    "partnership": r"\b(partnership|ties up|tie-up|mou|joint venture|collaborat)",
}
BEARISH = r"\b(falls?|slumps?|plunges?|crash|downgrades?|loss widens|penalty|raid|fraud|resigns?|default|probe|ban)\b"


def match_names(text: str, universe: Universe) -> list[str]:
    """Company names (two words or more) mentioned in the text -> symbols."""
    norm = f" {normalize(text)} "
    return [sym for name, sym in universe._by_name.items()
            if " " in name and len(name) > 8 and f" {name} " in norm][:3]


def classify_with_keywords(items: list[NewsItem], universe: Universe) -> None:
    for item in items:
        if item.classified_by:
            continue
        text = f"{item.title} {item.summary}".lower()
        if not item.symbols:
            item.symbols = match_names(f"{item.title} {item.summary}", universe)
        catalyst = next((c for c, p in BULLISH.items() if re.search(p, text)), "")
        bearish = re.search(BEARISH, text)
        item.catalyst = catalyst or ("other" if not bearish else "downgrade")
        item.sentiment = -0.5 if bearish and not catalyst else (0.5 if catalyst else 0.0)
        item.impact = 1 if catalyst or bearish else 0
        if item.source == "reddit":
            item.catalyst, item.impact = "buzz", min(item.impact, 1)
        item.classified_by = "keywords"


def classify(items: list[NewsItem], universe: Universe, cfg: dict) -> None:
    # Company-specific sources first so the Gemini cap never drops NSE filings.
    order = {"nse": 0, "rss": 1, "google_news": 2, "reddit": 3}
    items.sort(key=lambda it: order.get(it.source, 9))
    classify_with_gemini(items, universe, cfg)
    classify_with_keywords(items, universe)   # anything Gemini skipped or failed on
