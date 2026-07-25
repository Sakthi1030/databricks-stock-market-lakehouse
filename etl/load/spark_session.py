from pathlib import Path

from pyspark.sql import SparkSession


def get_spark(project_root: Path, app_name: str = "lakehouse-pipeline") -> SparkSession:
    """Build a local Spark session configured for Delta Lake.

    Locally this runs against the filesystem under data/spark-warehouse. In Databricks,
    a Spark session already exists on the cluster (the global `spark` variable) — this
    function is only needed for local/standalone execution, not inside a Databricks notebook.
    """
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
