"""Tests for Silver transformations — the actual cleaning/dedup/derived-column logic that
Bronze deliberately skips. Each test targets one specific rule rather than asserting on a
whole realistic-looking row, so a failure points straight at which rule broke.
"""
from datetime import datetime

from silver.transform import clean_profiles, clean_quotes

QUOTE_COLUMNS = [
    "symbol", "c", "d", "dp", "h", "l", "o", "pc", "t",
    "ingestion_date", "bronze_load_timestamp",
]

PROFILE_COLUMNS = [
    "symbol", "ticker", "name", "exchange", "country", "currency", "finnhubIndustry",
    "marketCapitalization", "shareOutstanding", "ipo", "weburl",
    "ingestion_date", "bronze_load_timestamp",
]


def _quote_row(symbol="AAPL", c=150.0, ts=None, **overrides):
    row = {
        "symbol": symbol, "c": c, "d": 1.5, "dp": 1.01, "h": 152.0, "l": 148.0, "o": 149.0,
        "pc": 148.5, "t": 1735689600,
        "ingestion_date": "2026-01-01", "bronze_load_timestamp": ts or datetime(2026, 1, 1, 12, 0, 0),
    }
    row.update(overrides)
    return tuple(row[c] for c in QUOTE_COLUMNS)


def _profile_row(symbol="AAPL", ts=None, **overrides):
    row = {
        "symbol": symbol, "ticker": symbol, "name": "Apple Inc", "exchange": "NASDAQ",
        "country": "US", "currency": "USD", "finnhubIndustry": "Technology",
        "marketCapitalization": 4500000.0, "shareOutstanding": 14000.0, "ipo": "1980-12-12",
        "weburl": "https://www.apple.com/",
        "ingestion_date": "2026-01-01", "bronze_load_timestamp": ts or datetime(2026, 1, 1, 12, 0, 0),
    }
    row.update(overrides)
    return tuple(row[c] for c in PROFILE_COLUMNS)


class TestCleanQuotes:
    def test_drops_row_with_null_symbol(self, spark):
        df = spark.createDataFrame([_quote_row(symbol=None), _quote_row(symbol="MSFT")], QUOTE_COLUMNS)
        result = clean_quotes(df)
        assert result.count() == 1
        assert result.first()["symbol"] == "MSFT"

    def test_drops_row_with_zero_or_negative_price(self, spark):
        df = spark.createDataFrame(
            [_quote_row(symbol="AAPL", c=0.0), _quote_row(symbol="MSFT", c=-5.0), _quote_row(symbol="GOOGL", c=100.0)],
            QUOTE_COLUMNS,
        )
        result = clean_quotes(df)
        assert result.count() == 1
        assert result.first()["symbol"] == "GOOGL"

    def test_dedup_keeps_most_recently_loaded_row_per_symbol_and_date(self, spark):
        older = _quote_row(symbol="AAPL", c=100.0, ts=datetime(2026, 1, 1, 9, 0, 0))
        newer = _quote_row(symbol="AAPL", c=105.0, ts=datetime(2026, 1, 1, 15, 0, 0))
        df = spark.createDataFrame([older, newer], QUOTE_COLUMNS)

        result = clean_quotes(df)

        assert result.count() == 1
        assert result.first()["current_price"] == 105.0

    def test_derived_columns_computed_correctly(self, spark):
        df = spark.createDataFrame([_quote_row(h=152.0, l=148.0, dp=1.014159)], QUOTE_COLUMNS)
        row = clean_quotes(df).first()

        assert row["daily_range"] == 4.0
        assert row["pct_change"] == 1.0142  # rounded to 4 decimal places

    def test_columns_renamed_from_finnhub_field_codes(self, spark):
        df = spark.createDataFrame([_quote_row(c=150.0, d=1.5, h=152.0, l=148.0, o=149.0, pc=148.5)], QUOTE_COLUMNS)
        row = clean_quotes(df).first()

        assert row["current_price"] == 150.0
        assert row["price_change"] == 1.5
        assert row["day_high"] == 152.0
        assert row["day_low"] == 148.0
        assert row["day_open"] == 149.0
        assert row["previous_close"] == 148.5


class TestCleanProfiles:
    def test_drops_row_with_null_name(self, spark):
        df = spark.createDataFrame(
            [_profile_row(symbol="AAPL", name=None), _profile_row(symbol="MSFT")], PROFILE_COLUMNS
        )
        result = clean_profiles(df)
        assert result.count() == 1
        assert result.first()["symbol"] == "MSFT"

    def test_dedup_keeps_most_recently_loaded_row(self, spark):
        older = _profile_row(symbol="AAPL", ts=datetime(2026, 1, 1, 9, 0, 0), marketCapitalization=1000.0)
        newer = _profile_row(symbol="AAPL", ts=datetime(2026, 1, 1, 15, 0, 0), marketCapitalization=2000.0)
        df = spark.createDataFrame([older, newer], PROFILE_COLUMNS)

        result = clean_profiles(df)

        assert result.count() == 1
        assert result.first()["market_cap_musd"] == 2000.0

    def test_attr_hash_identical_for_unchanged_attributes(self, spark):
        row_a = _profile_row(symbol="AAPL", ts=datetime(2026, 1, 1))
        row_b = _profile_row(symbol="AAPL", ts=datetime(2026, 1, 2))  # same attrs, different day
        df = spark.createDataFrame([row_a, row_b], PROFILE_COLUMNS)

        hashes = {r["attr_hash"] for r in clean_profiles(df).collect()}

        assert len(hashes) == 1  # same underlying attributes -> same hash, regardless of date

    def test_attr_hash_differs_when_market_cap_changes(self, spark):
        row_a = _profile_row(symbol="AAPL", marketCapitalization=1000.0)
        row_b = _profile_row(symbol="MSFT", marketCapitalization=2000.0)
        df = spark.createDataFrame([row_a, row_b], PROFILE_COLUMNS)

        hashes = [r["attr_hash"] for r in clean_profiles(df).collect()]

        assert hashes[0] != hashes[1]
