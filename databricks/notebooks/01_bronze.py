# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Bronze
# MAGIC Copies the raw zone (the repo's `data` branch, written by the 2 PM GitHub Action) into a Unity Catalog Volume and loads it into `bronze_*` Delta tables. Full refresh, so re-runs are idempotent.

# COMMAND ----------

# Jobs don't always put the repo root on sys.path: find the folder that holds `lakehouse/`.
import os
import sys

root = os.getcwd()
while not os.path.isdir(os.path.join(root, "lakehouse")) and os.path.dirname(root) != root:
    root = os.path.dirname(root)
sys.path.insert(0, root)

from lakehouse.pipeline import get_spark, run_bronze

run_bronze(get_spark())
