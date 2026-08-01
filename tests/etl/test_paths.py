"""Tests for etl.utils.paths — pure Python logic, no Spark session needed.

This module is the one thing standing between "works on my machine" and "works in
Databricks" for the whole pipeline (see the Bronze/Silver/Gold path-resolution bugs found
while actually deploying to Databricks) — worth pinning down with tests precisely because it
was the source of real, previously-shipped bugs.

Local-path expectations are built via pathlib.Path rather than hardcoded forward-slash
strings — Windows renders these with backslashes, so a hardcoded "/repo/data/gold" passes on
Linux CI but fails on a Windows dev machine, silently hiding the real cross-platform behavior.
"""
from pathlib import Path

import pytest

from etl.utils.paths import fs_path, gold_table_ref, is_databricks, spark_path

CONFIG = {
    "project_root": "/repo",
    "delta": {
        "raw_path": "/Volumes/workspace/default/lakehouse/raw",
        "bronze_path": "/Volumes/workspace/default/lakehouse/bronze",
        "silver_path": "/Volumes/workspace/default/lakehouse/silver",
        "gold_path": "/Volumes/workspace/default/lakehouse/gold",
    },
}


@pytest.fixture
def not_databricks(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)


@pytest.fixture
def on_databricks(monkeypatch):
    monkeypatch.setenv("DATABRICKS_RUNTIME_VERSION", "14.3")


def test_is_databricks_false_when_env_var_unset(not_databricks):
    assert is_databricks() is False


def test_is_databricks_true_when_env_var_set(on_databricks):
    assert is_databricks() is True


def test_spark_path_local_uses_project_root(not_databricks):
    expected = (Path("/repo") / "data" / "bronze" / "quotes").as_posix()
    assert spark_path(CONFIG, "bronze", "quotes") == expected


def test_spark_path_databricks_uses_volume_path(on_databricks):
    assert spark_path(CONFIG, "bronze", "quotes") == "/Volumes/workspace/default/lakehouse/bronze/quotes"


def test_spark_path_without_entity_returns_layer_root(not_databricks):
    expected = (Path("/repo") / "data" / "gold").as_posix()
    assert spark_path(CONFIG, "gold") == expected


def test_fs_path_returns_expected_path(not_databricks):
    result = fs_path(CONFIG, "raw", "quotes")
    assert result == Path("/repo") / "data" / "raw" / "quotes"


def test_gold_table_ref_local_is_a_path(not_databricks):
    expected = (Path("/repo") / "data" / "gold" / "dim_company").as_posix()
    assert gold_table_ref(CONFIG, "dim_company") == expected


def test_gold_table_ref_databricks_is_a_catalog_table_name(on_databricks):
    # This is the exact distinction that made Power BI able to see Gold as browsable tables
    # instead of opaque files in a Volume — worth a named regression test on its own.
    assert gold_table_ref(CONFIG, "dim_company") == "workspace.default.dim_company"
