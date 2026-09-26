"""Runs one layer at a time (one Databricks job task each) and writes managed Delta tables."""
import os
from pathlib import Path

from pyspark.sql import SparkSession

from . import bronze, gold, silver

SCHEMA = "workspace.nse_radar"
LANDING = Path("/Volumes/workspace/nse_radar/raw/landing")


def on_databricks() -> bool:
    return "DATABRICKS_RUNTIME_VERSION" in os.environ


def get_spark(app_name: str = "nse-radar") -> SparkSession:
    if on_databricks():
        return SparkSession.builder.getOrCreate()
    from delta import configure_spark_with_delta_pip

    builder = (SparkSession.builder.appName(app_name).master("local[*]")
               .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
               .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
               .config("spark.sql.session.timeZone", "Asia/Kolkata")
               .config("spark.ui.showConsoleProgress", "false"))
    return configure_spark_with_delta_pip(builder).getOrCreate()


def _save(df, name: str, schema: str) -> None:
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{schema}.{name}")


def setup(spark: SparkSession, schema: str = SCHEMA) -> None:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    if on_databricks():
        spark.sql(f"CREATE VOLUME IF NOT EXISTS {schema}.raw")


def run_bronze(spark: SparkSession, schema: str = SCHEMA, landing: Path = LANDING, download: bool = True) -> None:
    setup(spark, schema)
    if download:
        bronze.download_raw(landing)
    for name, df in bronze.load_bronze(spark, landing).items():
        _save(df, f"bronze_{name}", schema)


def run_silver(spark: SparkSession, schema: str = SCHEMA) -> None:
    t = lambda n: spark.table(f"{schema}.bronze_{n}")
    news = silver.news(t("news"))
    _save(silver.candidates(t("candidates")), "silver_candidates", schema)
    _save(news, "silver_news", schema)
    _save(silver.news_symbols(news), "silver_news_symbols", schema)
    _save(silver.outcomes(t("outcomes")), "silver_outcomes", schema)
    _save(silver.runs(t("runs")), "silver_runs", schema)


def run_gold(spark: SparkSession, schema: str = SCHEMA) -> None:
    t = lambda n: spark.table(f"{schema}.silver_{n}")
    perf = gold.pick_performance(t("candidates"), t("outcomes"))
    _save(perf, "gold_pick_performance", schema)
    perf = spark.table(f"{schema}.gold_pick_performance")
    _save(gold.track_record_daily(perf), "gold_track_record_daily", schema)
    _save(gold.hit_rate_by_catalyst(perf), "gold_hit_rate_by_catalyst", schema)
    _save(gold.hit_rate_by_score_band(perf), "gold_hit_rate_by_score_band", schema)
    _save(gold.hit_rate_by_source(perf, t("news_symbols")), "gold_hit_rate_by_source", schema)
    _save(gold.market_days(t("runs"), perf), "gold_market_days", schema)
    _save(gold.symbol_history(perf), "gold_symbol_history", schema)
