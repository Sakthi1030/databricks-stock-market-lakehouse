# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Silver
# MAGIC Types, de-duplicates and explodes the Bronze tables: one row per candidate per day, per headline, and per headline-stock pair.

# COMMAND ----------

from lakehouse.pipeline import get_spark, run_silver

run_silver(get_spark())
