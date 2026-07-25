from pathlib import Path

from pyspark.sql import SparkSession

from etl.utils.paths import is_databricks


def get_spark(project_root: Path, app_name: str = "lakehouse-pipeline") -> SparkSession:
    """Return the right Spark session for wherever this code is running.

    On Databricks, a Spark session already exists on the cluster — building a second one
    would be wrong, so we just reuse it via getOrCreate(). Locally, no such session exists,
    so we build one configured for Delta Lake against a local warehouse directory.
    """
    if is_databricks():
        return SparkSession.builder.getOrCreate()

    from delta import configure_spark_with_delta_pip

    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.warehouse.dir", str(project_root / "data" / "spark-warehouse"))
        .config("spark.ui.showConsoleProgress", "false")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()
