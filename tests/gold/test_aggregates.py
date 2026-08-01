from gold.aggregates import build_daily_market_summary, build_sector_summary, build_top_movers

FACT_COLUMNS = ["sk_company", "sk_date", "symbol", "ingestion_date", "pct_change", "daily_range", "current_price"]
DIM_COMPANY_COLUMNS = ["sk_company", "name", "industry", "market_cap_musd"]


def _fact_row(sk_company, symbol, pct_change, daily_range=5.0, current_price=100.0, ingestion_date="2026-01-01"):
    return (sk_company, 20260101, symbol, ingestion_date, pct_change, daily_range, current_price)


class TestBuildDailyMarketSummary:
    def test_gainers_and_losers_counted_correctly(self, spark):
        df = spark.createDataFrame(
            [
                _fact_row(1, "AAPL", 3.5),
                _fact_row(2, "MSFT", -1.2),
                _fact_row(3, "GOOGL", 2.0),
                _fact_row(4, "TSLA", 0.0),  # exactly zero counts as neither gainer nor loser
            ],
            FACT_COLUMNS,
        )
        row = build_daily_market_summary(df).first()

        assert row["num_companies"] == 4
        assert row["num_gainers"] == 2
        assert row["num_losers"] == 1

    def test_best_and_worst_pct_change(self, spark):
        df = spark.createDataFrame(
            [_fact_row(1, "AAPL", 5.0), _fact_row(2, "MSFT", -3.0), _fact_row(3, "GOOGL", 1.0)], FACT_COLUMNS
        )
        row = build_daily_market_summary(df).first()

        assert row["best_pct_change"] == 5.0
        assert row["worst_pct_change"] == -3.0


class TestBuildTopMovers:
    def test_ranks_gainers_descending_and_losers_ascending(self, spark):
        fact = spark.createDataFrame(
            [
                _fact_row(1, "AAPL", 5.0),
                _fact_row(2, "MSFT", 3.0),
                _fact_row(3, "GOOGL", -1.0),
                _fact_row(4, "TSLA", -4.0),
            ],
            FACT_COLUMNS,
        )
        dim_company = spark.createDataFrame(
            [(1, "Apple", "Tech", 100.0), (2, "Microsoft", "Tech", 100.0), (3, "Alphabet", "Media", 100.0), (4, "Tesla", "Auto", 100.0)],
            DIM_COMPANY_COLUMNS,
        )

        result = build_top_movers(fact, dim_company, top_n=5)
        gainers = {r["symbol"]: r["rank"] for r in result.collect() if r["mover_type"] == "gainer"}
        losers = {r["symbol"]: r["rank"] for r in result.collect() if r["mover_type"] == "loser"}

        assert gainers["AAPL"] == 1  # highest pct_change ranks first among gainers
        assert gainers["MSFT"] == 2
        assert losers["TSLA"] == 1  # most negative pct_change ranks first among losers
        assert losers["GOOGL"] == 2

    def test_top_n_limits_result_count(self, spark):
        fact = spark.createDataFrame(
            [_fact_row(i, f"SYM{i}", float(i)) for i in range(1, 8)], FACT_COLUMNS
        )
        dim_company = spark.createDataFrame(
            [(i, f"Company{i}", "Tech", 100.0) for i in range(1, 8)], DIM_COMPANY_COLUMNS
        )

        result = build_top_movers(fact, dim_company, top_n=3)

        assert result.filter("mover_type = 'gainer'").count() == 3
        assert result.filter("mover_type = 'loser'").count() == 3


class TestBuildSectorSummary:
    def test_rolls_up_by_industry(self, spark):
        fact = spark.createDataFrame(
            [_fact_row(1, "AAPL", 4.0), _fact_row(2, "MSFT", 2.0), _fact_row(3, "TSLA", -6.0)], FACT_COLUMNS
        )
        dim_company = spark.createDataFrame(
            [(1, "Apple", "Technology", 1000.0), (2, "Microsoft", "Technology", 2000.0), (3, "Tesla", "Automobiles", 500.0)],
            DIM_COMPANY_COLUMNS,
        )

        result = {r["industry"]: r for r in build_sector_summary(fact, dim_company).collect()}

        assert result["Technology"]["num_companies"] == 2
        assert result["Technology"]["avg_pct_change"] == 3.0  # (4.0 + 2.0) / 2
        assert result["Technology"]["total_market_cap_musd"] == 3000.0
        assert result["Automobiles"]["num_companies"] == 1
