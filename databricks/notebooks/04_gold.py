# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Gold
# MAGIC Refreshes dimensions, builds the day's fact rows, and refreshes the pre-aggregated
# MAGIC marts (daily_market_summary, top_movers, sector_summary) that Power BI and React
# MAGIC read directly. Depends on `03_silver`.

# COMMAND ----------

%pip install tenacity python-dotenv PyYAML requests

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

from gold.ingest_gold import main as run_gold

run_gold()
