# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Bronze
# MAGIC Appends today's raw JSON into the Bronze Delta tables, untouched apart from lineage
# MAGIC columns. Depends on `01_extract` having run first for the same day.

# COMMAND ----------

%pip install tenacity python-dotenv PyYAML requests

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

from bronze.ingest_bronze import main as run_bronze

run_bronze()
