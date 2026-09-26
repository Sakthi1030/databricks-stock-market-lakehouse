# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Gold
# MAGIC Builds the marts the website and Power BI read: pick performance, daily track record (picks vs other candidates), and hit rates by catalyst, score band and news source.

# COMMAND ----------

from lakehouse.pipeline import get_spark, run_gold

run_gold(get_spark())
