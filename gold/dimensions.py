"""Gold dimension builders.

dim_date is fully deterministic reference data — safe to overwrite every run, nothing to merge.
dim_company is a Type 1 (current-state) view over Silver's SCD2 profile history. Gold keeps
this simple for BI; if a report ever needs "what did we know about this company on date X",
that question is answered from Silver, not Gold — trading full history for query simplicity
is a deliberate design choice here, not an oversight.
"""
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def build_dim_date(spark: SparkSession, start_date: str = "2024-01-01", end_date: str = "2030-12-31") -> DataFrame:
    df = spark.sql(
        f"SELECT explode(sequence(to_date('{start_date}'), to_date('{end_date}'), interval 1 day)) AS full_date"
    )
    return (
        df.withColumn("sk_date", F.date_format("full_date", "yyyyMMdd").cast("int"))
        .withColumn("year", F.year("full_date"))
        .withColumn("quarter", F.quarter("full_date"))
        .withColumn("month", F.month("full_date"))
        .withColumn("month_name", F.date_format("full_date", "MMMM"))
        .withColumn("day_of_month", F.dayofmonth("full_date"))
        .withColumn("day_of_week", F.dayofweek("full_date"))
        .withColumn("day_name", F.date_format("full_date", "EEEE"))
        .withColumn("week_of_year", F.weekofyear("full_date"))
        .withColumn("is_weekend", F.dayofweek("full_date").isin(1, 7))
        .select(
            "sk_date", "full_date", "year", "quarter", "month", "month_name",
            "day_of_month", "day_of_week", "day_name", "week_of_year", "is_weekend",
        )
    )


def build_dim_company(silver_profiles_df: DataFrame) -> DataFrame:
    current = silver_profiles_df.filter(F.col("is_current"))
    return (
        current.withColumn("sk_company", F.xxhash64(F.col("symbol")))
        .select(
            "sk_company", "symbol", "ticker", "name", "exchange", "country", "currency",
            F.col("finnhubIndustry").alias("industry"),
            "market_cap_musd", "shareOutstanding", "ipo", "weburl",
            "effective_start_date",
        )
    )
