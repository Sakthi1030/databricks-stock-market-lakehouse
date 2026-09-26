"""Records that flow through a run and land, as JSON, in the lakehouse's raw zone."""
from dataclasses import asdict, dataclass, field
from hashlib import sha1


@dataclass
class NewsItem:
    source: str            # nse | rss | google_news | reddit
    outlet: str            # e.g. "Economic Times", "r/IndianStreetBets", "NSE filing"
    title: str
    url: str
    published: str         # ISO 8601, IST
    summary: str = ""
    symbols: list[str] = field(default_factory=list)   # NSE symbols the item is about
    category: str = ""     # NSE filing category, when known
    # Filled by classification (Gemini, or the keyword fallback):
    sentiment: float = 0.0  # -1 bearish .. +1 bullish
    impact: int = 0         # 0 none .. 3 likely to move the price next day
    catalyst: str = ""      # order_win, results, upgrade, acquisition, ...
    reason: str = ""
    classified_by: str = ""

    @property
    def id(self) -> str:
        return sha1(f"{self.source}|{self.url or self.title}".encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {"id": self.id, **asdict(self)}


@dataclass
class Candidate:
    symbol: str
    name: str
    news_ids: list[str] = field(default_factory=list)
    news_score: float = 0.0      # 0-100
    reach_rate: float | None = None      # share of days whose next-day high was >= +target
    day_change_pct: float | None = None
    volume_ratio: float | None = None
    avg_traded_value_cr: float | None = None
    price: float | None = None           # at the 2 PM snapshot
    prev_close: float | None = None
    target_price: float | None = None
    scores: dict = field(default_factory=dict)   # component scores, 0-100
    score: float = 0.0
    rank: int | None = None
    is_pick: bool = False
    skip_reason: str = ""
    catalysts: list[str] = field(default_factory=list)
    headline: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
