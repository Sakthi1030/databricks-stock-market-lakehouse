"""Shared pytest fixtures.

A single session-scoped SparkSession is reused across every test that needs one — creating a
new one per test would make the suite painfully slow (each SparkSession spin-up takes a
couple of seconds even locally).
"""
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def spark():
    from etl.load.spark_session import get_spark

    session = get_spark(PROJECT_ROOT, app_name="pytest")
    yield session
    session.stop()
