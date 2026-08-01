"""Databricks SQL Warehouse connection — the same warehouse Power BI connects to.

A new connection per request is deliberate, not an oversight: this is a small personal
project with light traffic, so the simplicity of "connect, query, close" outweighs the
cost of connection pooling. The real cost worth knowing about is the warehouse itself —
Databricks SQL Warehouses auto-stop after inactivity, so the first request after a while
can take 10-30s to wake it back up. Everything after that is fast.
"""
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

from databricks import sql
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@contextmanager
def get_connection():
    host = os.environ.get("DATABRICKS_HOST")
    http_path = os.environ.get("DATABRICKS_HTTP_PATH")
    token = os.environ.get("DATABRICKS_TOKEN")
    if not all([host, http_path, token]):
        raise EnvironmentError(
            "DATABRICKS_HOST, DATABRICKS_HTTP_PATH, and DATABRICKS_TOKEN must all be set in .env"
        )

    connection = sql.connect(server_hostname=host, http_path=http_path, access_token=token)
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
