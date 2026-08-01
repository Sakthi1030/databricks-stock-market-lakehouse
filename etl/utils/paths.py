"""Environment-aware path resolution.

The same pipeline code runs unmodified locally and inside Databricks. Every Databricks
cluster automatically sets DATABRICKS_RUNTIME_VERSION, so we detect that and switch from a
local ./data folder to a Unity Catalog Volume path from config.yaml — no separate
"Databricks version" of the scripts to maintain.

Databricks Free Edition's serverless compute doesn't support the legacy /dbfs FUSE mount for
plain file I/O (raises OSError: Operation not supported), and Unity Catalog governance
expects storage access through Volumes rather than the raw DBFS root anyway. So on
Databricks, both Spark I/O (spark_path) and plain Python file I/O (fs_path) resolve to the
same Volume path — there's no dbfs:/ vs /dbfs/ split to maintain like there was pre-Unity
Catalog.
"""
import os
from pathlib import Path


def is_databricks() -> bool:
    return "DATABRICKS_RUNTIME_VERSION" in os.environ


def _base_path(config: dict, layer: str) -> str:
    if is_databricks():
        return config["delta"][f"{layer}_path"]
    # Spark/Hadoop paths are URI-style and always forward-slash, regardless of host OS —
    # .as_posix() keeps this consistent with the entity-appending below instead of mixing
    # Windows backslashes with a hardcoded "/" separator.
    return (Path(config["project_root"]) / "data" / layer).as_posix()


def spark_path(config: dict, layer: str, entity: str = None) -> str:
    base = _base_path(config, layer)
    return f"{base}/{entity}" if entity else base


def fs_path(config: dict, layer: str, entity: str = None) -> Path:
    base = Path(_base_path(config, layer))
    return (base / entity) if entity else base


def gold_table_ref(config: dict, entity: str) -> str:
    """Gold is the BI-serving layer, so on Databricks it's registered as a real Unity Catalog
    managed table (queryable from Power BI's Databricks connector, discoverable in Catalog
    Explorer) rather than a path-based Delta table in a Volume — Volumes are for files, not
    the tables a BI tool needs to browse. Locally there's no catalog, so it's just a path.
    """
    if is_databricks():
        return f"workspace.default.{entity}"
    return spark_path(config, "gold", entity)
