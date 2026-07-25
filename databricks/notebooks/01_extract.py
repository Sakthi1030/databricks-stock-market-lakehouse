# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Extract
# MAGIC Pulls quote + company profile data from Finnhub for every configured ticker and lands
# MAGIC it as raw JSON in a Unity Catalog Volume.
# MAGIC
# MAGIC **Before running:** enter your Finnhub API key into the `finnhub_api_key` widget box
# MAGIC that appears at the top of the notebook once the cell below runs. Databricks Free
# MAGIC Edition doesn't expose the Secrets API or cluster environment variables on this token
# MAGIC tier, so a widget is the practical way to keep the real key out of the git-tracked
# MAGIC notebook source. For the scheduled Job (Step 6c), this same widget becomes a Job
# MAGIC parameter set once in the workspace UI — still never committed to GitHub.

# COMMAND ----------

%pip install tenacity python-dotenv PyYAML requests

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("finnhub_api_key", "")

# COMMAND ----------

import os

os.environ["FINNHUB_API_KEY"] = dbutils.widgets.get("finnhub_api_key")

from etl.extract.run_extract import main as run_extract

run_extract()
