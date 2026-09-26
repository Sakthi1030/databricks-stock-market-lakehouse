"""Silver: typed, de-duplicated, one row per business key."""
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def _latest(df: DataFrame, keys: list[str], order_col: str = "_ingested_at") -> DataFrame:
    w = Window.partitionBy(*keys).orderBy(F.col(order_col).desc())
    return df.withColumn("_rn", F.row_number().over(w)).filter("_rn = 1").drop("_rn")


def candidates(bronze: DataFrame) -> DataFrame:
    df = (bronze.filter(F.col("symbol").isNotNull() & F.col("date").isNotNull())
          .withColumn("trade_date", F.to_date("date"))
          .withColumn("news_count", F.size("news_ids"))
          .withColumn("news_component", F.col("scores")["news"])
          .withColumn("reach_component", F.col("scores")["reach"])
          .withColumn("momentum_component", F.col("scores")["momentum"])
          .withColumn("volume_component", F.col("scores")["volume"])
          .withColumn("is_pick", F.coalesce("is_pick", F.lit(False)))
          .withColumn("skipped", F.col("skip_reason") != ""))
    df = _latest(df, ["trade_date", "symbol"])
    return df.select("trade_date", "symbol", "name", "rank", "is_pick", "skipped", "skip_reason", "score",
                     "news_component", "reach_component", "momentum_component", "volume_component",
                     "news_score", "reach_rate", "day_change_pct", "volume_ratio", "avg_traded_value_cr",
                     "price", "prev_close", "target_price", "catalysts", "headline", "news_ids",
                     "news_count", "sparkline")


def news(bronze: DataFrame) -> DataFrame:
    df = (bronze.filter(F.col("id").isNotNull())
          .withColumn("published_at", F.to_timestamp("published"))
          .withColumn("trade_date", F.to_date("date"))
          .withColumn("sentiment_label", F.when(F.col("sentiment") >= 0.25, "bullish")
                      .when(F.col("sentiment") <= -0.25, "bearish").otherwise("neutral")))
    df = _latest(df, ["id"])
    return df.select("id", "trade_date", "published_at", "source", "outlet", "title", "url", "summary",
                     "symbols", "category", "sentiment", "sentiment_label", "impact", "catalyst", "reason",
                     "classified_by")


def news_symbols(silver_news: DataFrame) -> DataFrame:
    """One row per (headline, stock): the bridge between news and candidates."""
    return (silver_news.select("id", "trade_date", "published_at", "source", "outlet", "sentiment", "impact",
                               "catalyst", F.explode("symbols").alias("symbol")))


def outcomes(bronze: DataFrame) -> DataFrame:
    df = (bronze.filter(F.col("symbol").isNotNull())
          .withColumn("trade_date", F.to_date("date"))
          .withColumn("next_trade_date", F.to_date("next_date"))
          .withColumn("graded_at", F.to_timestamp("graded_at")))
    df = _latest(df, ["trade_date", "symbol"])
    return df.select("trade_date", "symbol", "entry", "next_trade_date", "next_open", "next_high",
                     "next_close", "hit", "max_gain_pct", "close_return_pct", "open_gap_pct", "graded_at")


def runs(bronze: DataFrame) -> DataFrame:
    idx = "map<string, struct<price: double, change_pct: double>>"
    df = (bronze.withColumn("trade_date", F.to_date("market_date"))
          .withColumn("run_at", F.to_timestamp("run_at"))
          .withColumn("indices", F.from_json("indices_json", idx))
          .withColumn("stats", F.from_json("stats_json", "map<string, string>")))
    df = _latest(df, ["trade_date"])
    return df.select("trade_date", "run_at", "target_pct", "brief",
                     F.col("indices")["NIFTY 50"]["change_pct"].alias("nifty_change_pct"),
                     F.col("stats")["headlines"].cast("int").alias("headlines"),
                     F.col("stats")["matched_stocks"].cast("int").alias("matched_stocks"))
