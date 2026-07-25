"""Environment-aware path resolution.

The same pipeline code runs unmodified locally and inside Databricks. Every Databricks
cluster automatically sets DATABRICKS_RUNTIME_VERSION, so we detect that and switch from a
local ./data folder to DBFS paths from config.yaml — no separate "Databricks version" of
the scripts to maintain.

Two variants matter because Databricks exposes DBFS two different ways:
  - spark_path(): the dbfs:/... URI, for Spark/Delta I/O (spark.read, DeltaTable.forPath)
  - fs_path():    the /dbfs/... FUSE-mounted path, for plain Python file I/O (open(), mkdir) —
                   only the raw JSON layer (Extract step) needs this; Bronze/Silver/Gold are
                   pure Spark/Delta I/O and only ever need spark_path().
"""
import os
from pathlib import Path


def is_databricks() -> bool:
    return "DATABRICKS_RUNTIME_VERSION" in os.environ


def spark_path(config: dict, layer: str, entity: str = None) -> str:
    if is_databricks():
        base = config["delta"][f"{layer}_path"]
    else:
        base = str(Path(config["project_root"]) / "data" / layer)
    return f"{base}/{entity}" if entity else base


def fs_path(config: dict, layer: str, entity: str = None) -> Path:
    if is_databricks():
        base = Path("/dbfs") / config["delta"][f"{layer}_path"].replace("dbfs:/", "")
    else:
        base = Path(config["project_root"]) / "data" / layer
    return (base / entity) if entity else base
