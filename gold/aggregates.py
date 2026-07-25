"""Pre-aggregated Gold marts — built for BI dashboard performance, not ad-hoc querying.

Power BI and the React dashboard read these directly instead of aggregating the fact table
on every page load.
"""
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def build_daily_market_summary(fact_df: DataFrame) -> DataFrame:
    """One row per day: the Executive Summary / KPI-row numbers."""
    return fact_df.groupBy("ingestion_date").agg(
        F.count("*").alias("num_companies"),
        F.round(F.avg("pct_change"), 4).alias("avg_pct_change"),
        F.sum(F.when(F.col("pct_change") > 0, 1).otherwise(0)).alias("num_gainers"),
        F.sum(F.when(F.col("pct_change") < 0, 1).otherwise(0)).alias("num_losers"),
        F.round(F.avg("daily_range"), 4).alias("avg_daily_range"),
        F.round(F.max("pct_change"), 4).alias("best_pct_change"),
        F.round(F.min("pct_change"), 4).alias("worst_pct_change"),
    )


def build_top_movers(fact_df: DataFrame, dim_company_df: DataFrame, top_n: int = 5) -> DataFrame:
    """Top N gainers and losers per day — the Top Movers / Top Categories visual."""
    joined = fact_df.join(dim_company_df.select("sk_company", "name", "industry"), on="sk_company", how="left")

    gainers_window = Window.partitionBy("ingestion_date").orderBy(F.col("pct_change").desc())
    losers_window = Window.partitionBy("ingestion_date").orderBy(F.col("pct_change").asc())

    gainers = (
        joined.withColumn("rank", F.row_number().over(gainers_window))
        .filter(F.col("rank") <= top_n)
        .withColumn("mover_type", F.lit("gainer"))
    )
    losers = (
        joined.withColumn("rank", F.row_number().over(losers_window))
        .filter(F.col("rank") <= top_n)
        .withColumn("mover_type", F.lit("loser"))
    )

    return gainers.unionByName(losers).select(
        "ingestion_date", "mover_type", "rank", "symbol", "name", "industry", "pct_change", "current_price",
    )


def build_sector_summary(fact_df: DataFrame, dim_company_df: DataFrame) -> DataFrame:
    """Industry-level rollup per day — feeds a 'performance by sector' category chart."""
    joined = fact_df.join(dim_company_df.select("sk_company", "industry", "market_cap_musd"), on="sk_company", how="left")

    return joined.groupBy("ingestion_date", "industry").agg(
        F.count("*").alias("num_companies"),
        F.round(F.avg("pct_change"), 4).alias("avg_pct_change"),
        F.round(F.sum("market_cap_musd"), 2).alias("total_market_cap_musd"),
    )
