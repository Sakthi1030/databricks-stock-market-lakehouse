"""Gold: the marts the website reads. Every question here is "does the signal actually work?"."""
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

SCORE_BANDS = [(0, 35, "<35"), (35, 45, "35-45"), (45, 55, "45-55"), (55, 65, "55-65"), (65, 101, "65+")]


def pick_performance(candidates: DataFrame, outcomes: DataFrame) -> DataFrame:
    """Every scored stock with what happened next; `graded` is false until the next session closes."""
    band = F.lit(None).cast("string")
    for lo, hi, label in reversed(SCORE_BANDS):
        band = F.when((F.col("score") >= lo) & (F.col("score") < hi), label).otherwise(band)
    return (candidates.join(outcomes, ["trade_date", "symbol"], "left")
            .withColumn("graded", F.col("hit").isNotNull())
            .withColumn("score_band", band))


def _rates(df: DataFrame, *keys: str) -> DataFrame:
    return (df.filter("graded").groupBy(*keys).agg(
        F.count("*").alias("trades"),
        F.sum(F.col("hit").cast("int")).alias("hits"),
        F.round(100 * F.avg(F.col("hit").cast("double")), 1).alias("hit_rate"),
        F.round(F.avg("max_gain_pct"), 2).alias("avg_max_gain_pct"),
        F.round(F.avg("close_return_pct"), 2).alias("avg_close_return_pct"),
    ))


def track_record_daily(perf: DataFrame) -> DataFrame:
    """Per trading day: picks vs the other candidates, plus a rolling 20-day pick hit rate."""
    graded = perf.filter("graded")
    daily = graded.groupBy("trade_date").agg(
        F.sum(F.col("is_pick").cast("int")).alias("picks"),
        F.sum((F.col("is_pick") & F.col("hit")).cast("int")).alias("pick_hits"),
        F.sum((~F.col("is_pick")).cast("int")).alias("others"),
        F.sum((~F.col("is_pick") & F.col("hit")).cast("int")).alias("other_hits"),
        F.round(F.avg(F.when(F.col("is_pick"), F.col("max_gain_pct"))), 2).alias("pick_avg_max_gain_pct"),
    )
    w = Window.orderBy("trade_date").rowsBetween(-19, 0)
    rate = lambda hits, n: F.when(n > 0, F.round(100 * hits / n, 1))   # null when there were none
    return (daily
            .withColumn("pick_hit_rate", rate(F.col("pick_hits"), F.col("picks")))
            .withColumn("other_hit_rate", rate(F.col("other_hits"), F.col("others")))
            .withColumn("rolling_20d_pick_hit_rate", rate(F.sum("pick_hits").over(w), F.sum("picks").over(w)))
            .orderBy("trade_date"))


def hit_rate_by_catalyst(perf: DataFrame) -> DataFrame:
    exploded = perf.withColumn("catalyst", F.explode_outer("catalysts")).fillna({"catalyst": "none"})
    return _rates(exploded, "catalyst", "is_pick").orderBy(F.desc("trades"))


def hit_rate_by_score_band(perf: DataFrame) -> DataFrame:
    return _rates(perf, "score_band").orderBy("score_band")


def hit_rate_by_source(perf: DataFrame, news_symbols: DataFrame) -> DataFrame:
    """Credit each graded stock to every news source that mentioned it that day."""
    sources = news_symbols.select("trade_date", "symbol", "source").distinct()
    return _rates(perf.join(sources, ["trade_date", "symbol"]), "source").orderBy(F.desc("trades"))


def market_days(runs: DataFrame, perf: DataFrame) -> DataFrame:
    day = perf.groupBy("trade_date").agg(
        F.sum(F.col("is_pick").cast("int")).alias("picks"),
        F.sum((F.col("is_pick") & F.coalesce(F.col("hit"), F.lit(False))).cast("int")).alias("pick_hits"),
        F.max(F.when(F.col("is_pick") & (F.col("rank") == 1), F.col("symbol"))).alias("top_pick"),
    )
    return runs.join(day, "trade_date", "left").orderBy(F.desc("trade_date"))


def symbol_history(perf: DataFrame) -> DataFrame:
    """Per stock: how often it showed up, was picked, and hit."""
    return perf.groupBy("symbol", "name").agg(
        F.count("*").alias("appearances"),
        F.sum(F.col("is_pick").cast("int")).alias("times_picked"),
        F.sum(F.col("hit").cast("int")).alias("hits"),
        F.round(100 * F.avg(F.col("hit").cast("double")), 1).alias("hit_rate"),
        F.max("trade_date").alias("last_seen"),
    ).orderBy(F.desc("appearances"))
