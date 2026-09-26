# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Gold
# MAGIC Builds the marts the website and Power BI read: pick performance, daily track record (picks vs other candidates), and hit rates by catalyst, score band and news source.

# COMMAND ----------

# Jobs don't always put the repo root on sys.path: find the folder that holds `lakehouse/`.
import os
import sys

root = os.getcwd()
while not os.path.isdir(os.path.join(root, "lakehouse")) and os.path.dirname(root) != root:
    root = os.path.dirname(root)
sys.path.insert(0, root)

from lakehouse.pipeline import get_spark, run_gold

run_gold(get_spark())
