"""Silver layer entrypoint.

Reads only the newly-arrived Bronze partition (ingestion_date) — partition pruning means we
never rescan the full Bronze history on a daily run. Cleans, validates, and merges into
Silver: Type 1 upsert for quotes (idempotent per day), SCD Type 2 for profiles (full change
history preserved).
"""
from datetime import datetime, timezone
from pathlib import Path

from etl.load.spark_session import get_spark
from etl.utils.config_loader import load_config
from etl.utils.data_quality import (
    DQCheck,
    check_no_duplicates,
    check_no_nulls,
    check_positive,
    check_row_count_min,
    run_checks,
)
from etl.utils.logger import get_logger
from etl.utils.paths import spark_path
from silver.merge import upsert_profiles_scd2, upsert_quotes_type1
from silver.transform import clean_profiles, clean_quotes

logger = get_logger(__name__)


def _run_quotes(spark, config: dict, ingestion_date: str) -> None:
    bronze_path = spark_path(config, "bronze", "quotes")
    bronze_df = spark.read.format("delta").load(bronze_path).filter(f"ingestion_date = '{ingestion_date}'")

    silver_df = clean_quotes(bronze_df)

    checks = [
        DQCheck("row_count_min", check_row_count_min(1)),
        DQCheck("no_nulls_symbol_price", check_no_nulls(["symbol", "current_price"])),
        DQCheck("price_positive", check_positive("current_price")),
        DQCheck("no_duplicate_symbol_per_day", check_no_duplicates(["symbol", "ingestion_date"])),
    ]
    report = run_checks(silver_df, checks, context="silver_quotes")
    if report.has_critical_failure:
        raise SystemExit(f"Critical DQ failures for silver_quotes: {report.failed}")

    silver_path = spark_path(config, "silver", "quotes")
    upsert_quotes_type1(spark, silver_df, silver_path)


def _run_profiles(spark, config: dict, ingestion_date: str) -> None:
    bronze_path = spark_path(config, "bronze", "profiles")
    bronze_df = spark.read.format("delta").load(bronze_path).filter(f"ingestion_date = '{ingestion_date}'")

    silver_df = clean_profiles(bronze_df)

    checks = [
        DQCheck("row_count_min", check_row_count_min(1)),
        DQCheck("no_nulls_symbol_name", check_no_nulls(["symbol", "name"])),
    ]
    report = run_checks(silver_df, checks, context="silver_profiles")
    if report.has_critical_failure:
        raise SystemExit(f"Critical DQ failures for silver_profiles: {report.failed}")

    silver_path = spark_path(config, "silver", "profiles")
    upsert_profiles_scd2(spark, silver_df, silver_path)


def main(ingestion_date: str = None):
    config = load_config()
    project_root = Path(config["project_root"])
    ingestion_date = ingestion_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    spark = get_spark(project_root)
    logger.info("Silver ingestion starting for ingestion_date=%s", ingestion_date)

    try:
        _run_quotes(spark, config, ingestion_date)
        _run_profiles(spark, config, ingestion_date)
    finally:
        spark.stop()

    logger.info("Silver ingestion complete for ingestion_date=%s", ingestion_date)


if __name__ == "__main__":
    main()
