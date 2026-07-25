"""Gold fact table: one row per (company, date), enriched with dimension surrogate keys."""
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_fact_daily_quotes(silver_quotes_df: DataFrame, dim_company_df: DataFrame) -> DataFrame:
    """Inner-joins quotes to dim_company — a quote for a symbol with no dimension match is
    dropped rather than kept with a null foreign key. The caller is expected to compare row
    counts before/after and log any drop; silently losing rows is a real production hazard.
    """
    return (
        silver_quotes_df.alias("q")
        .join(dim_company_df.select("sk_company", "symbol").alias("c"), on="symbol", how="inner")
        .withColumn("sk_date", F.date_format(F.col("ingestion_date"), "yyyyMMdd").cast("int"))
        .select(
            "sk_company", "sk_date", "symbol", "ingestion_date", "quote_timestamp",
            "current_price", "price_change", "pct_change", "day_high", "day_low",
            "day_open", "previous_close", "daily_range",
        )
    )
