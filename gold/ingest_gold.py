"""Gold layer entrypoint.

Builds/refreshes dimensions, builds the day's fact rows, and refreshes the pre-aggregated
marts that Power BI and the React dashboard query directly — nothing downstream ever reads
Silver directly.
"""
from datetime import datetime, timezone
from pathlib import Path

from delta.tables import DeltaTable

from etl.load.spark_session import get_spark
from etl.utils.config_loader import load_config
from etl.utils.logger import get_logger
from etl.utils.paths import spark_path
from gold.aggregates import build_daily_market_summary, build_sector_summary, build_top_movers
from gold.dimensions import build_dim_company, build_dim_date
from gold.facts import build_fact_daily_quotes

logger = get_logger(__name__)


def _upsert(spark, df, path, key_columns, partition_column=None):
    if not DeltaTable.isDeltaTable(spark, path):
        writer = df.write.format("delta").mode("overwrite")
        if partition_column:
            writer = writer.partitionBy(partition_column)
        writer.save(path)
        logger.info("Initialized Gold table at %s with %d rows", path, df.count())
        return

    target = DeltaTable.forPath(spark, path)
    condition = " AND ".join(f"target.{k} = source.{k}" for k in key_columns)
    (
        target.alias("target")
        .merge(df.alias("source"), condition)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    logger.info("Upserted %d rows into Gold table at %s", df.count(), path)


def main(ingestion_date: str = None):
    config = load_config()
    project_root = Path(config["project_root"])
    ingestion_date = ingestion_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    spark = get_spark(project_root)
    logger.info("Gold ingestion starting for ingestion_date=%s", ingestion_date)

    try:
        # --- dim_date: deterministic reference data, safe to overwrite every run ---
        dim_date_path = spark_path(config, "gold", "dim_date")
        dim_date_df = build_dim_date(spark)
        dim_date_df.write.format("delta").mode("overwrite").save(dim_date_path)
        logger.info("Refreshed dim_date at %s (%d rows)", dim_date_path, dim_date_df.count())

        # --- dim_company: Type 1 upsert keyed on the deterministic surrogate key ---
        silver_profiles = spark.read.format("delta").load(spark_path(config, "silver", "profiles"))
        dim_company_df = build_dim_company(silver_profiles)
        dim_company_path = spark_path(config, "gold", "dim_company")
        _upsert(spark, dim_company_df, dim_company_path, key_columns=["sk_company"])

        # Re-read post-merge so downstream joins see the full current dimension, not just today's upserted rows.
        dim_company_current = spark.read.format("delta").load(dim_company_path)

        # --- fact_daily_quotes ---
        silver_quotes = (
            spark.read.format("delta").load(spark_path(config, "silver", "quotes"))
            .filter(f"ingestion_date = '{ingestion_date}'")
        )
        pre_join_count = silver_quotes.count()
        fact_df = build_fact_daily_quotes(silver_quotes, dim_company_current)
        post_join_count = fact_df.count()
        if post_join_count < pre_join_count:
            logger.warning(
                "%d quote rows had no matching dim_company entry and were dropped from the fact table",
                pre_join_count - post_join_count,
            )

        fact_path = spark_path(config, "gold", "fact_daily_quotes")
        _upsert(spark, fact_df, fact_path, key_columns=["sk_company", "sk_date"], partition_column="ingestion_date")

        fact_today = spark.read.format("delta").load(fact_path).filter(f"ingestion_date = '{ingestion_date}'")

        # --- Pre-aggregated marts ---
        summary_df = build_daily_market_summary(fact_today)
        _upsert(spark, summary_df, spark_path(config, "gold", "daily_market_summary"), key_columns=["ingestion_date"])

        movers_df = build_top_movers(fact_today, dim_company_current, top_n=5)
        _upsert(
            spark, movers_df, spark_path(config, "gold", "top_movers"),
            key_columns=["ingestion_date", "mover_type", "rank"],
        )

        sector_df = build_sector_summary(fact_today, dim_company_current)
        _upsert(
            spark, sector_df, spark_path(config, "gold", "sector_summary"),
            key_columns=["ingestion_date", "industry"],
        )

    finally:
        spark.stop()

    logger.info("Gold ingestion complete for ingestion_date=%s", ingestion_date)


if __name__ == "__main__":
    main()
