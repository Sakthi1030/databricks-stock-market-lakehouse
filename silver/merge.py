"""Silver merge strategies: Type 1 upsert for facts, Type 2 versioning for dimensions."""
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from delta.tables import DeltaTable

from etl.utils.logger import get_logger

logger = get_logger(__name__)


def upsert_quotes_type1(spark: SparkSession, new_df: DataFrame, silver_path: str) -> None:
    """SCD Type 1: one row per (symbol, ingestion_date). A same-day rerun overwrites, not duplicates."""
    key_columns = ["symbol", "ingestion_date"]

    if not DeltaTable.isDeltaTable(spark, silver_path):
        new_df.write.format("delta").mode("overwrite").partitionBy("ingestion_date").save(silver_path)
        logger.info("Initialized Silver quotes table at %s with %d rows", silver_path, new_df.count())
        return

    target = DeltaTable.forPath(spark, silver_path)
    merge_condition = " AND ".join(f"target.{k} = source.{k}" for k in key_columns)
    (
        target.alias("target")
        .merge(new_df.alias("source"), merge_condition)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    logger.info("Type 1 upsert: merged %d quote rows into %s", new_df.count(), silver_path)


def upsert_profiles_scd2(spark: SparkSession, new_df: DataFrame, silver_path: str) -> None:
    """SCD Type 2: full change history for company profiles via effective_start/end_date + is_current.

    Classic two-step Delta merge pattern:
      1. Expire the current row for any symbol whose tracked attributes changed (attr_hash differs).
      2. Insert a fresh "current" row for every changed or brand-new symbol.
    Unchanged symbols are left untouched — no new version is written for them.
    """
    new_df = (
        new_df.withColumn("effective_start_date", F.col("ingestion_date"))
        .withColumn("effective_end_date", F.lit(None).cast("string"))
        .withColumn("is_current", F.lit(True))
    )

    if not DeltaTable.isDeltaTable(spark, silver_path):
        new_df.write.format("delta").mode("overwrite").save(silver_path)
        logger.info("Initialized Silver profiles (SCD2) table at %s with %d rows", silver_path, new_df.count())
        return

    target = DeltaTable.forPath(spark, silver_path)
    current = target.toDF().filter(F.col("is_current"))

    changed_or_new = (
        new_df.alias("n")
        .join(current.alias("c"), on="symbol", how="left")
        .where(F.col("c.symbol").isNull() | (F.col("n.attr_hash") != F.col("c.attr_hash")))
        .select("n.*")
    )
    changed_count = changed_or_new.count()

    if changed_count == 0:
        logger.info("SCD2: no profile attribute changes detected for %s — nothing to version.", silver_path)
        return

    # Step 1: expire old current rows for symbols that changed.
    (
        target.alias("target")
        .merge(changed_or_new.alias("source"), "target.symbol = source.symbol AND target.is_current = true")
        .whenMatchedUpdate(set={
            "is_current": "false",
            "effective_end_date": "source.ingestion_date",
        })
        .execute()
    )

    # Step 2: insert the new current version for each changed/new symbol.
    changed_or_new.write.format("delta").mode("append").save(silver_path)
    logger.info("SCD2: versioned %d changed/new profile rows into %s", changed_count, silver_path)
