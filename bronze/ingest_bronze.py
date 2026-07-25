"""Bronze layer entrypoint.

Reads the raw JSON produced by the Extract step for a given ingestion_date and appends it,
untouched apart from lineage columns, into the Bronze Delta tables. No cleaning, no dedup,
no dropped rows — that discipline is what makes Bronze a trustworthy audit trail.
"""
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import functions as F

from bronze.schemas import PROFILE_SCHEMA, QUOTE_SCHEMA
from etl.load.delta_io import read_json_raw, write_delta_append
from etl.load.spark_session import get_spark
from etl.utils.config_loader import load_config
from etl.utils.logger import get_logger

logger = get_logger(__name__)

ENTITIES = {
    "quotes": QUOTE_SCHEMA,
    "profiles": PROFILE_SCHEMA,
}


def add_lineage_columns(df, ingestion_date: str):
    return (
        df.withColumn("ingestion_date", F.lit(ingestion_date))
        .withColumn("bronze_load_timestamp", F.current_timestamp())
    )


def main(ingestion_date: str = None):
    config = load_config()
    project_root = Path(config["project_root"])
    ingestion_date = ingestion_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    partition_column = config["pipeline"]["partition_column"]

    spark = get_spark(project_root)
    logger.info("Bronze ingestion starting for ingestion_date=%s", ingestion_date)

    for entity, schema in ENTITIES.items():
        raw_dir = project_root / "data" / "raw" / entity / f"ingestion_date={ingestion_date}"
        if not raw_dir.exists():
            logger.warning("No raw data for %s on %s — run the Extract step first. Skipping.", entity, ingestion_date)
            continue

        df = read_json_raw(spark, raw_dir, schema)
        if df.rdd.isEmpty():
            logger.warning("Raw data directory for %s on %s was empty. Skipping.", entity, ingestion_date)
            continue

        df = add_lineage_columns(df, ingestion_date)

        # Local path for now; on Databricks this becomes config["delta"]["bronze_path"] + f"/{entity}" (DBFS).
        bronze_path = str(project_root / "data" / "bronze" / entity)
        write_delta_append(df, bronze_path, partition_column)

    spark.stop()
    logger.info("Bronze ingestion complete for ingestion_date=%s", ingestion_date)


if __name__ == "__main__":
    main()
