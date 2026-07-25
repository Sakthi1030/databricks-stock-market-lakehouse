"""Silver layer transformations: cleaning, typing, dedup, and derived columns.

Bronze is raw and can contain duplicate appends (e.g. Extract rerunning the same day) or
missing fields. Silver enforces the contract: one clean row per key, correct types, and
business-meaningful derived columns.
"""
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def _dedupe_latest(df: DataFrame, key_columns: list) -> DataFrame:
    """Keep only the most-recently-loaded Bronze row per key (handles Extract reruns)."""
    window = Window.partitionBy(*key_columns).orderBy(F.col("bronze_load_timestamp").desc())
    return (
        df.withColumn("_row_rank", F.row_number().over(window))
        .filter(F.col("_row_rank") == 1)
        .drop("_row_rank")
    )


def clean_quotes(bronze_df: DataFrame) -> DataFrame:
    df = bronze_df.filter(F.col("symbol").isNotNull() & F.col("c").isNotNull() & (F.col("c") > 0))
    df = _dedupe_latest(df, ["symbol", "ingestion_date"])

    return (
        df.withColumn("quote_timestamp", F.to_timestamp(F.from_unixtime(F.col("t"))))
        .withColumn("daily_range", F.round(F.col("h") - F.col("l"), 4))
        .withColumn("pct_change", F.round(F.col("dp"), 4))
        .withColumnRenamed("c", "current_price")
        .withColumnRenamed("d", "price_change")
        .withColumnRenamed("h", "day_high")
        .withColumnRenamed("l", "day_low")
        .withColumnRenamed("o", "day_open")
        .withColumnRenamed("pc", "previous_close")
        .withColumn("silver_load_timestamp", F.current_timestamp())
        .select(
            "symbol", "ingestion_date", "quote_timestamp", "current_price", "price_change",
            "pct_change", "day_high", "day_low", "day_open", "previous_close", "daily_range",
            "bronze_load_timestamp", "silver_load_timestamp",
        )
    )


def clean_profiles(bronze_df: DataFrame) -> DataFrame:
    df = bronze_df.filter(F.col("symbol").isNotNull() & F.col("name").isNotNull())
    df = _dedupe_latest(df, ["symbol", "ingestion_date"])

    return (
        df.withColumn("market_cap_musd", F.round(F.col("marketCapitalization"), 2))
        .withColumn(
            # Hash of the attributes we care about changing — lets the SCD2 merge detect
            # "did anything meaningful change" with one column comparison instead of N.
            "attr_hash",
            F.sha2(
                F.concat_ws(
                    "||",
                    F.coalesce(F.col("name"), F.lit("")),
                    F.coalesce(F.col("exchange"), F.lit("")),
                    F.coalesce(F.col("finnhubIndustry"), F.lit("")),
                    F.coalesce(F.round(F.col("marketCapitalization"), 2).cast("string"), F.lit("")),
                ),
                256,
            ),
        )
        .withColumn("silver_load_timestamp", F.current_timestamp())
        .select(
            "symbol", "ticker", "name", "exchange", "country", "currency", "finnhubIndustry",
            "market_cap_musd", "shareOutstanding", "ipo", "weburl", "ingestion_date",
            "attr_hash", "bronze_load_timestamp", "silver_load_timestamp",
        )
    )
