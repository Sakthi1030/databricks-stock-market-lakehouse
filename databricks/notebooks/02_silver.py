# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Silver
# MAGIC Types, de-duplicates and explodes the Bronze tables: one row per candidate per day, per headline, and per headline-stock pair.

# COMMAND ----------

# Jobs don't put the Git folder's root on sys.path; the notebook runs from databricks/notebooks/.
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..", "..")))

from lakehouse.pipeline import get_spark, run_silver

run_silver(get_spark())
