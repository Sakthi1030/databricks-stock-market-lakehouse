# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Bronze
# MAGIC Copies the raw zone (the repo's `data` branch, written by the 2 PM GitHub Action) into a Unity Catalog Volume and loads it into `bronze_*` Delta tables. Full refresh, so re-runs are idempotent.

# COMMAND ----------

# Jobs don't put the Git folder's root on sys.path; the notebook runs from databricks/notebooks/.
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..", "..")))

from lakehouse.pipeline import get_spark, run_bronze

run_bronze(get_spark())
