"""News collectors. Each returns NewsItems; a failing source is logged and skipped, never fatal."""
import html
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

from .http import get_bytes, get_json
from .models import NewsItem

log = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")
ATOM = "{http://www.w3.org/2005/Atom}"


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def to_ist(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)          # RSS: 'Sat, 26 Sep 2026 14:21:07 +0530'
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))   # Atom: ISO 8601
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    return dt.astimezone(IST)


def parse_feed(raw: bytes) -> list[dict]:
    """RSS 2.0 or Atom -> [{title, url, published, summary, outlet}]. Tolerates bad bytes."""
    text = raw.decode("utf-8", "replace").encode("utf-8", "replace")
    root = ET.fromstring(text)
    entries = []
    for item in root.iter("item"):
        source = item.find("source")
        entries.append({
            "title": strip_html(item.findtext("title", "")),
            "url": (item.findtext("link") or "").strip(),
            "published": item.findtext("pubDate", ""),
            "summary": strip_html(item.findtext("description", ""))[:600],
            "outlet": source.text.strip() if source is not None and source.text else "",
        })
    for entry in root.iter(f"{ATOM}entry"):
        link = entry.find(f"{ATOM}link")
        entries.append({
            "title": strip_html(entry.findtext(f"{ATOM}title", "")),
            "url": link.get("href", "") if link is not None else "",
            "published": entry.findtext(f"{ATOM}updated", "") or entry.findtext(f"{ATOM}published", ""),
            "summary": strip_html(entry.findtext(f"{ATOM}content", ""))[:600],
            "outlet": "",
        })
    return entries


def _items(entries, source, outlet, since) -> list[NewsItem]:
    items = []
    for e in entries:
        published = to_ist(e["published"])
        if not e["title"] or published is None or published < since:
            continue
        title = e["title"]
        name = e["outlet"] or outlet
        if source == "google_news":   # Google appends " - Outlet" to every title
            title = re.sub(r"\s+-\s+[^-]+$", "", title)
        items.append(NewsItem(source=source, outlet=name, title=title, url=e["url"],
                              published=published.isoformat(), summary=e["summary"]))
    return items


def fetch_rss(feeds: dict, since: datetime) -> list[NewsItem]:
    items = []
    for outlet, url in feeds.items():
        try:
            items += _items(parse_feed(get_bytes(url)), "rss", outlet, since)
        except Exception as exc:
            log.warning("RSS %s failed: %s", outlet, exc)
    return items


def fetch_google_news(queries: dict, since: datetime) -> list[NewsItem]:
    items = []
    for label, query in queries.items():
        url = f"https://news.google.com/rss/search?q={quote_plus(query + ' when:2d')}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            items += _items(parse_feed(get_bytes(url)), "google_news", label, since)
        except Exception as exc:
            log.warning("Google News '%s' failed: %s", label, exc)
    return items


def fetch_reddit(subreddits: list[str], since: datetime) -> list[NewsItem]:
    items = []
    for sub in subreddits:
        try:
            raw = get_bytes(f"https://www.reddit.com/r/{sub}/new/.rss?limit=50", retries=3)
            items += _items(parse_feed(raw), "reddit", f"r/{sub}", since)
        except Exception as exc:   # Reddit rate-limits aggressively; the run carries on without it
            log.warning("Reddit r/%s failed: %s", sub, exc)
    return items


def fetch_nse(skip_categories: list[str], since: datetime, now: datetime) -> list[NewsItem]:
    skip = {c.lower() for c in skip_categories}
    url = ("https://www.nseindia.com/api/corporate-announcements?index=equities"
           f"&from_date={since:%d-%m-%Y}&to_date={now:%d-%m-%Y}")
    try:
        rows = get_json(url, headers={"Referer": "https://www.nseindia.com/companies-listing/corporate-filings-announcements"})
    except Exception as exc:
        log.warning("NSE announcements failed: %s", exc)
        return []
    items = []
    for r in rows:
        category = (r.get("desc") or "").strip()
        if category.lower() in skip:
            continue
        try:
            published = datetime.strptime(r["an_dt"], "%d-%b-%Y %H:%M:%S").replace(tzinfo=IST)
        except (KeyError, ValueError):
            continue
        if published < since:
            continue
        items.append(NewsItem(
            source="nse", outlet="NSE filing", category=category,
            title=f"{r.get('sm_name', r.get('symbol', ''))}: {category}",
            url=r.get("attchmntFile") or "", published=published.isoformat(),
            summary=strip_html(r.get("attchmntText") or "")[:600],
            symbols=[r["symbol"]] if r.get("symbol") else [],
        ))
    return items


def collect(config: dict, now: datetime) -> list[NewsItem]:
    since = now - timedelta(hours=config["news_window_hours"])
    items = (fetch_nse(config["nse_skip_categories"], since, now)
             + fetch_rss(config["rss_feeds"], since)
             + fetch_google_news(config["google_news_queries"], since)
             + fetch_reddit(config["subreddits"], since))
    unique = {}
    for item in items:   # the same story often appears in several feeds; keep the first
        key = re.sub(r"[^a-z0-9]", "", item.title.lower())[:80]
        unique.setdefault(key, item)
    return list(unique.values())
