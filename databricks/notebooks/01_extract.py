# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Extract
# MAGIC Pulls quote + company profile data from Finnhub for every configured ticker and lands
# MAGIC it as raw JSON. Requires `FINNHUB_API_KEY` to be set as a cluster environment variable
# MAGIC (Compute → your cluster → Edit → Advanced Options → Spark → Environment Variables).

# COMMAND ----------

%pip install tenacity python-dotenv PyYAML requests

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

from etl.extract.run_extract import main as run_extract

run_extract()
