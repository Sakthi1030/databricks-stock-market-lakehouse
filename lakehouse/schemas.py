"""Explicit Bronze schemas: the raw files are JSON Lines, and an empty file (e.g. no outcomes yet
on day one) must still produce a typed, empty table instead of failing schema inference."""
from pyspark.sql.types import (ArrayType, BooleanType, DoubleType, IntegerType, MapType, StringType,
                               StructField, StructType)

S, D, I, B = StringType(), DoubleType(), IntegerType(), BooleanType()


def _fields(*spec):
    return StructType([StructField(name, dtype, True) for name, dtype in spec])


CANDIDATES = _fields(
    ("date", S), ("symbol", S), ("name", S), ("news_ids", ArrayType(S)), ("news_score", D),
    ("reach_rate", D), ("day_change_pct", D), ("volume_ratio", D), ("avg_traded_value_cr", D),
    ("price", D), ("prev_close", D), ("target_price", D), ("scores", MapType(S, D)), ("score", D),
    ("rank", I), ("is_pick", B), ("skip_reason", S), ("catalysts", ArrayType(S)), ("headline", S),
    ("sparkline", ArrayType(D)),
)

NEWS = _fields(
    ("date", S), ("id", S), ("source", S), ("outlet", S), ("title", S), ("url", S), ("published", S),
    ("summary", S), ("symbols", ArrayType(S)), ("category", S), ("sentiment", D), ("impact", I),
    ("catalyst", S), ("reason", S), ("classified_by", S),
)

OUTCOMES = _fields(
    ("date", S), ("symbol", S), ("entry", D), ("is_pick", B), ("score", D), ("catalysts", ArrayType(S)),
    ("next_date", S), ("next_open", D), ("next_high", D), ("next_close", D), ("hit", B),
    ("max_gain_pct", D), ("close_return_pct", D), ("open_gap_pct", D), ("graded_at", S),
)

RUNS = _fields(
    ("market_date", S), ("run_at", S), ("target_pct", D), ("brief", S),
    ("indices_json", S), ("stats_json", S),
)
