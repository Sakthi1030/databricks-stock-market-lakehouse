"""Databricks SQL Warehouse access, with a time budget so a sleeping warehouse never blocks a page.

Free Edition serverless warehouses stop when idle and take ~35s to start. A query that misses
its budget keeps running in the background (waking the warehouse), the caller serves the raw
fallback now, and the next request, a few seconds later, gets Gold from cache or a warm warehouse.
"""
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

from databricks import sql
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
log = logging.getLogger(__name__)

SCHEMA = "workspace.nse_radar"
CACHE_SECONDS = 600          # Gold changes twice a day; ten minutes of staleness is fine
_pool = ThreadPoolExecutor(max_workers=4)
_cache: dict[str, tuple[float, list[dict]]] = {}
_inflight: dict[str, Any] = {}


def configured() -> bool:
    return all(os.environ.get(k) for k in ("DATABRICKS_HOST", "DATABRICKS_HTTP_PATH", "DATABRICKS_TOKEN"))


@contextmanager
def get_connection():
    # The connector's default retry policy keeps retrying for up to 15 minutes; cap it at two.
    connection = sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
        _retry_stop_after_attempts_count=4,
        _retry_stop_after_attempts_duration=120,
        _socket_timeout=60,
    )
    try:
        yield connection
    finally:
        connection.close()


def run_query(query: str, parameters: Optional[dict[str, Any]] = None) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, parameters)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


def gold(query: str, budget_seconds: float = 12) -> Optional[list[dict]]:
    """Cached Gold query result, or None if the warehouse can't answer within the budget."""
    if not configured():
        return None
    hit = _cache.get(query)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    future = _inflight.get(query)
    if future is None or future.done():
        future = _inflight[query] = _pool.submit(run_query, query)
    try:
        rows = future.result(timeout=budget_seconds)
    except FutureTimeout:
        log.info("Warehouse still waking; serving the raw fallback for now")
        return None
    except Exception as exc:
        log.warning("Gold query failed: %s", exc)
        return None
    _cache[query] = (time.time(), rows)
    return rows
