"""Bronze: copy the raw zone (the repo's `data` branch) into a landing folder, then load it as-is.

The raw files hold the full, de-duplicated history, so every load is a full refresh: re-running
is idempotent and a bad day can be fixed at the source and simply re-ingested.
"""
import json
from pathlib import Path

import requests
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from . import schemas

REPO = "Sakthi1030/databricks-stock-market-lakehouse"
RAW = f"https://raw.githubusercontent.com/{REPO}/data"
JSONL = {"candidates": schemas.CANDIDATES, "news": schemas.NEWS, "outcomes": schemas.OUTCOMES}


def download_raw(landing: Path) -> None:
    """Fetch the JSONL history files plus one runs/<date>.json per trading day."""
    landing.mkdir(parents=True, exist_ok=True)
    for name in JSONL:
        resp = requests.get(f"{RAW}/{name}.jsonl", timeout=60)
        (landing / f"{name}.jsonl").write_text(resp.text if resp.ok else "", encoding="utf-8")
    listing = requests.get(f"https://api.github.com/repos/{REPO}/contents/runs?ref=data", timeout=60)
    runs = []
    for entry in listing.json() if listing.ok else []:
        run = requests.get(entry["download_url"], timeout=60).json()
        runs.append({"market_date": run["market_date"], "run_at": run["run_at"],
                     "target_pct": run.get("target_pct"), "brief": run.get("brief", ""),
                     "indices_json": json.dumps(run.get("indices", {})),
                     "stats_json": json.dumps(run.get("stats", {}))})
    (landing / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in runs), encoding="utf-8")


def load_bronze(spark: SparkSession, landing: Path) -> dict[str, DataFrame]:
    tables = {**JSONL, "runs": schemas.RUNS}
    out = {}
    for name, schema in tables.items():
        path = landing / f"{name}.jsonl"
        if path.exists() and path.stat().st_size:
            df = spark.read.schema(schema).json(str(path))
        else:
            df = spark.createDataFrame([], schema)
        out[name] = (df.withColumn("_ingested_at", F.current_timestamp())
                       .withColumn("_source_file", F.lit(f"{name}.jsonl")))
    return out
