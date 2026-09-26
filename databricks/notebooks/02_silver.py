# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Silver
# MAGIC Types, de-duplicates and explodes the Bronze tables: one row per candidate per day, per headline, and per headline-stock pair.

# COMMAND ----------

# Jobs don't always put the repo root on sys.path: find the folder that holds `lakehouse/`.
import os
import sys

root = os.getcwd()
while not os.path.isdir(os.path.join(root, "lakehouse")) and os.path.dirname(root) != root:
    root = os.path.dirname(root)
sys.path.insert(0, root)

from lakehouse.pipeline import get_spark, run_silver

run_silver(get_spark())
