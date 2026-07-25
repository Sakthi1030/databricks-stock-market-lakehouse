# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Silver
# MAGIC Cleans, validates (data quality gate), and merges into Silver: Type 1 upsert for
# MAGIC quotes, SCD Type 2 for company profiles. Depends on `02_bronze`.

# COMMAND ----------

%pip install tenacity python-dotenv PyYAML requests

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

from silver.ingest_silver import main as run_silver

run_silver()
