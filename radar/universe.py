"""The NSE equity list: every listed symbol and company name, used to validate matches."""
import csv
import io
import re

from .http import get_bytes

EQUITY_LIST = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

_SUFFIXES = re.compile(r"\b(limited|ltd|pvt|private|corporation|corp|company|co|inc|the)\b\.?")


def normalize(name: str) -> str:
    """'Tata Motors Limited' -> 'tata motors'; used to map a company name to its symbol."""
    name = name.lower().replace("&", " and ")
    name = _SUFFIXES.sub(" ", name)
    name = re.sub(r"[^a-z0-9 ]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()


class Universe:
    def __init__(self, rows: list[dict]):
        self.names = {r["symbol"]: r["name"] for r in rows}
        self._by_name = {normalize(r["name"]): r["symbol"] for r in rows}

    def __contains__(self, symbol: str) -> bool:
        return symbol in self.names

    def __len__(self) -> int:
        return len(self.names)

    def resolve(self, symbol: str = "", name: str = "") -> str | None:
        """Best NSE symbol for an LLM-proposed symbol and/or company name, or None."""
        symbol = (symbol or "").upper().removesuffix(".NS").strip()
        if symbol in self.names:
            return symbol
        key = normalize(name or "")
        if not key:
            return None
        if key in self._by_name:
            return self._by_name[key]
        # 'Tata Motors' should find 'Tata Motors Passenger Vehicles' only if it is the sole match.
        hits = [s for n, s in self._by_name.items() if n.startswith(key + " ")]
        return hits[0] if len(hits) == 1 else None


def load_universe(series: list[str]) -> Universe:
    text = get_bytes(EQUITY_LIST).decode("utf-8", "replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        row = {k.strip(): (v or "").strip() for k, v in row.items()}
        if row.get("SERIES") in series:
            rows.append({"symbol": row["SYMBOL"], "name": row["NAME OF COMPANY"]})
    return Universe(rows)
