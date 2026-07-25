"""Gold layer entrypoint.

Builds/refreshes dimensions, builds the day's fact rows, and refreshes the pre-aggregated
marts that Power BI and the React dashboard query directly — nothing downstream ever reads
Silver directly.

On Databricks, Gold tables are registered as real Unity Catalog managed tables (via
gold_table_ref) rather than path-based Delta in a Volume — Gold is the BI-serving layer, and
Power BI's Databricks connector browses catalog tables, not raw volume files. Locally there's
no catalog, so everything falls back to the same path-based Delta tables used in Bronze/Silver.
"""
from datetime import datetime, timezone
from pathlib import Path

from delta.tables import DeltaTable

from etl.load.spark_session import get_spark
from etl.utils.config_loader import load_config
from etl.utils.logger import get_logger
from etl.utils.paths import gold_table_ref, is_databricks, spark_path
from gold.aggregates import build_daily_market_summary, build_sector_summary, build_top_movers
from gold.dimensions import build_dim_company, build_dim_date
from gold.facts import build_fact_daily_quotes

logger = get_logger(__name__)


def _exists(spark, ref: str) -> bool:
    if is_databricks():
        return spark.catalog.tableExists(ref)
    return DeltaTable.isDeltaTable(spark, ref)


def _read(spark, ref: str):
    if is_databricks():
        return spark.table(ref)
    return spark.read.format("delta").load(ref)


def _delta_table(spark, ref: str) -> DeltaTable:
    if is_databricks():
        return DeltaTable.forName(spark, ref)
    return DeltaTable.forPath(spark, ref)


def _write_new(df, ref: str, partition_column: str = None) -> None:
    writer = df.write.format("delta").mode("overwrite")
    if partition_column:
        writer = writer.partitionBy(partition_column)
    if is_databricks():
        writer.saveAsTable(ref)
    else:
        writer.save(ref)


def _upsert(spark, df, ref: str, key_columns: list, partition_column: str = None) -> None:
    if not _exists(spark, ref):
        _write_new(df, ref, partition_column)
        logger.info("Initialized Gold table %s with %d rows", ref, df.count())
        return

    target = _delta_table(spark, ref)
    condition = " AND ".join(f"target.{k} = source.{k}" for k in key_columns)
    (
        target.alias("target")
        .merge(df.alias("source"), condition)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    logger.info("Upserted %d rows into Gold table %s", df.count(), ref)


def main(ingestion_date: str = None):
    config = load_config()
    project_root = Path(config["project_root"])
    ingestion_date = ingestion_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    spark = get_spark(project_root)
    logger.info("Gold ingestion starting for ingestion_date=%s", ingestion_date)

    try:
        # --- dim_date: deterministic reference data, safe to overwrite every run ---
        dim_date_ref = gold_table_ref(config, "dim_date")
        dim_date_df = build_dim_date(spark)
        _write_new(dim_date_df, dim_date_ref)
        logger.info("Refreshed dim_date at %s (%d rows)", dim_date_ref, dim_date_df.count())

        # --- dim_company: Type 1 upsert keyed on the deterministic surrogate key ---
        silver_profiles = spark.read.format("delta").load(spark_path(config, "silver", "profiles"))
        dim_company_df = build_dim_company(silver_profiles)
        dim_company_ref = gold_table_ref(config, "dim_company")
        _upsert(spark, dim_company_df, dim_company_ref, key_columns=["sk_company"])

        # Re-read post-merge so downstream joins see the full current dimension, not just today's upserted rows.
        dim_company_current = _read(spark, dim_company_ref)

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

        fact_ref = gold_table_ref(config, "fact_daily_quotes")
        _upsert(spark, fact_df, fact_ref, key_columns=["sk_company", "sk_date"], partition_column="ingestion_date")

        fact_today = _read(spark, fact_ref).filter(f"ingestion_date = '{ingestion_date}'")

        # --- Pre-aggregated marts ---
        summary_df = build_daily_market_summary(fact_today)
        _upsert(spark, summary_df, gold_table_ref(config, "daily_market_summary"), key_columns=["ingestion_date"])

        movers_df = build_top_movers(fact_today, dim_company_current, top_n=5)
        _upsert(
            spark, movers_df, gold_table_ref(config, "top_movers"),
            key_columns=["ingestion_date", "mover_type", "rank"],
        )

        sector_df = build_sector_summary(fact_today, dim_company_current)
        _upsert(
            spark, sector_df, gold_table_ref(config, "sector_summary"),
            key_columns=["ingestion_date", "industry"],
        )

    finally:
        spark.stop()

    logger.info("Gold ingestion complete for ingestion_date=%s", ingestion_date)


if __name__ == "__main__":
    main()
