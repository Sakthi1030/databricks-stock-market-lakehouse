from datetime import date

from gold.dimensions import build_dim_company, build_dim_date

PROFILE_COLUMNS = [
    "sk_company", "symbol", "ticker", "name", "exchange", "country", "currency",
    "finnhubIndustry", "market_cap_musd", "shareOutstanding", "ipo", "weburl",
    "effective_start_date", "is_current",
]


class TestBuildDimDate:
    def test_row_count_matches_inclusive_date_range(self, spark):
        result = build_dim_date(spark, start_date="2026-01-01", end_date="2026-01-10")
        assert result.count() == 10  # Jan 1 through Jan 10 inclusive

    def test_sk_date_matches_yyyymmdd_format(self, spark):
        result = build_dim_date(spark, start_date="2026-03-05", end_date="2026-03-05")
        row = result.first()
        assert row["sk_date"] == 20260305

    def test_is_weekend_flags_saturday_and_sunday_correctly(self, spark):
        # 2026-01-03 is a Saturday, 2026-01-05 is a Monday
        result = build_dim_date(spark, start_date="2026-01-03", end_date="2026-01-05")
        by_date = {row["full_date"]: row["is_weekend"] for row in result.collect()}

        assert by_date[date(2026, 1, 3)] is True
        assert by_date[date(2026, 1, 4)] is True
        assert by_date[date(2026, 1, 5)] is False


class TestBuildDimCompany:
    def test_filters_to_current_records_only(self, spark):
        df = spark.createDataFrame(
            [
                (1, "AAPL", "AAPL", "Apple Inc", "NASDAQ", "US", "USD", "Technology", 4500000.0, 14000.0, "1980-12-12", "https://apple.com", "2026-01-01", False),
                (1, "AAPL", "AAPL", "Apple Inc", "NASDAQ", "US", "USD", "Technology", 4600000.0, 14000.0, "1980-12-12", "https://apple.com", "2026-01-02", True),
            ],
            PROFILE_COLUMNS,
        )
        result = build_dim_company(df)
        assert result.count() == 1
        assert result.first()["market_cap_musd"] == 4600000.0

    def test_surrogate_key_is_deterministic_for_same_symbol(self, spark):
        df = spark.createDataFrame(
            [(1, "AAPL", "AAPL", "Apple Inc", "NASDAQ", "US", "USD", "Technology", 4500000.0, 14000.0, "1980-12-12", "https://apple.com", "2026-01-01", True)],
            PROFILE_COLUMNS,
        )
        first_run = build_dim_company(df).first()["sk_company"]
        second_run = build_dim_company(df).first()["sk_company"]

        # Same symbol must always hash to the same surrogate key across separate rebuilds —
        # this is exactly the property that lets fact-table foreign keys survive a dim rebuild.
        assert first_run == second_run

    def test_industry_column_renamed_from_finnhub_field(self, spark):
        df = spark.createDataFrame(
            [(1, "AAPL", "AAPL", "Apple Inc", "NASDAQ", "US", "USD", "Technology", 4500000.0, 14000.0, "1980-12-12", "https://apple.com", "2026-01-01", True)],
            PROFILE_COLUMNS,
        )
        result = build_dim_company(df)
        assert "industry" in result.columns
        assert "finnhubIndustry" not in result.columns
        assert result.first()["industry"] == "Technology"
