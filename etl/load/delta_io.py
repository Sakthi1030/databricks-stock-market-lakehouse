from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType

from etl.utils.logger import get_logger

logger = get_logger(__name__)


def read_json_raw(spark: SparkSession, raw_dir: Path, schema: StructType) -> DataFrame:
    """Read the raw JSON-array files produced by the Extract step into a typed DataFrame.

    An explicit schema is passed in (rather than letting Spark infer it) so that a field
    Finnhub returns as null on one day and populated on another can't silently flip the
    inferred type and break the next day's append.
    """
    files = [str(p) for p in raw_dir.rglob("*.json")]
    if not files:
        logger.warning("No raw files found under %s", raw_dir)
        return spark.createDataFrame([], schema)
    return spark.read.schema(schema).option("multiline", "true").json(files)


def write_delta_append(df: DataFrame, table_path: str, partition_column: str) -> None:
    """Append-only Delta write with schema evolution allowed (mergeSchema).

    Bronze/Silver/Gold all use append-or-merge, never a blind overwrite — overwriting would
    destroy history that downstream consumers (or an audit) might need to replay.
    """
    row_count = df.count()
    (
        df.write.format("delta")
        .mode("append")
        .partitionBy(partition_column)
        .option("mergeSchema", "true")
        .save(table_path)
    )
    logger.info("Appended %d rows to Delta table at %s", row_count, table_path)
