from datetime import datetime

from gold.facts import build_fact_daily_quotes

QUOTE_COLUMNS = [
    "symbol", "ingestion_date", "quote_timestamp", "current_price", "price_change",
    "pct_change", "day_high", "day_low", "day_open", "previous_close", "daily_range",
]

DIM_COMPANY_COLUMNS = ["sk_company", "symbol"]

# quote_timestamp is passed through unused by build_fact_daily_quotes, but Spark's schema
# inference can't determine a type for a column that's None in every sample row — a real
# value (rather than None) sidesteps that entirely.
_TS = datetime(2026, 1, 1, 12, 0, 0)


def test_inner_join_keeps_only_symbols_present_in_dim_company(spark):
    quotes = spark.createDataFrame(
        [
            ("AAPL", "2026-01-01", _TS, 150.0, 1.0, 0.5, 152.0, 148.0, 149.0, 149.5, 4.0),
            ("DELISTED", "2026-01-01", _TS, 10.0, 0.0, 0.0, 10.0, 10.0, 10.0, 10.0, 0.0),
        ],
        QUOTE_COLUMNS,
    )
    dim_company = spark.createDataFrame([(1, "AAPL")], DIM_COMPANY_COLUMNS)

    result = build_fact_daily_quotes(quotes, dim_company)

    # "DELISTED" has no dim_company row and must be dropped, not kept with a null FK —
    # this is the exact behavior ingest_gold.py relies on to detect and log dropped rows.
    assert result.count() == 1
    assert result.first()["symbol"] == "AAPL"


def test_sk_date_derived_from_ingestion_date_string(spark):
    quotes = spark.createDataFrame(
        [("AAPL", "2026-03-05", _TS, 150.0, 1.0, 0.5, 152.0, 148.0, 149.0, 149.5, 4.0)], QUOTE_COLUMNS
    )
    dim_company = spark.createDataFrame([(1, "AAPL")], DIM_COMPANY_COLUMNS)

    result = build_fact_daily_quotes(quotes, dim_company)

    assert result.first()["sk_date"] == 20260305


def test_sk_company_carried_through_from_dim_company(spark):
    quotes = spark.createDataFrame(
        [("AAPL", "2026-01-01", _TS, 150.0, 1.0, 0.5, 152.0, 148.0, 149.0, 149.5, 4.0)], QUOTE_COLUMNS
    )
    dim_company = spark.createDataFrame([(42, "AAPL")], DIM_COMPANY_COLUMNS)

    result = build_fact_daily_quotes(quotes, dim_company)

    assert result.first()["sk_company"] == 42
