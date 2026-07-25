from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType

# Matches the raw /quote response from Finnhub, field-for-field.
QUOTE_SCHEMA = StructType([
    StructField("symbol", StringType(), False),
    StructField("c", DoubleType(), True),    # current price
    StructField("d", DoubleType(), True),    # change
    StructField("dp", DoubleType(), True),   # percent change
    StructField("h", DoubleType(), True),    # day high
    StructField("l", DoubleType(), True),    # day low
    StructField("o", DoubleType(), True),    # day open
    StructField("pc", DoubleType(), True),   # previous close
    StructField("t", LongType(), True),      # quote unix timestamp
    StructField("ingestion_timestamp", StringType(), True),
])

# Matches the raw /stock/profile2 response from Finnhub, field-for-field.
PROFILE_SCHEMA = StructType([
    StructField("symbol", StringType(), False),
    StructField("ticker", StringType(), True),
    StructField("name", StringType(), True),
    StructField("country", StringType(), True),
    StructField("currency", StringType(), True),
    StructField("estimateCurrency", StringType(), True),
    StructField("exchange", StringType(), True),
    StructField("ipo", StringType(), True),
    StructField("marketCapitalization", DoubleType(), True),
    StructField("shareOutstanding", DoubleType(), True),
    StructField("floatingShare", DoubleType(), True),
    StructField("finnhubIndustry", StringType(), True),
    StructField("phone", StringType(), True),
    StructField("weburl", StringType(), True),
    StructField("logo", StringType(), True),
    StructField("ingestion_timestamp", StringType(), True),
])
