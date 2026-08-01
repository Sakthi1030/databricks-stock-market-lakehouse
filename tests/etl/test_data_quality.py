from etl.utils.data_quality import (
    check_no_duplicates,
    check_no_nulls,
    check_positive,
    check_row_count_min,
)


def test_check_no_nulls_passes_when_column_fully_populated(spark):
    df = spark.createDataFrame([("AAPL", 1.0), ("MSFT", 2.0)], ["symbol", "price"])
    assert check_no_nulls(["symbol", "price"])(df) is True


def test_check_no_nulls_fails_when_any_row_has_null(spark):
    df = spark.createDataFrame([("AAPL", 1.0), (None, 2.0)], ["symbol", "price"])
    assert check_no_nulls(["symbol", "price"])(df) is False


def test_check_positive_fails_on_zero_or_negative(spark):
    df = spark.createDataFrame([(1.0,), (0.0,), (-5.0,)], ["price"])
    assert check_positive("price")(df) is False


def test_check_positive_passes_when_all_strictly_positive(spark):
    df = spark.createDataFrame([(1.0,), (0.01,), (500.0,)], ["price"])
    assert check_positive("price")(df) is True


def test_check_no_duplicates_detects_repeated_key(spark):
    df = spark.createDataFrame(
        [("AAPL", "2026-01-01"), ("AAPL", "2026-01-01"), ("MSFT", "2026-01-01")],
        ["symbol", "ingestion_date"],
    )
    assert check_no_duplicates(["symbol", "ingestion_date"])(df) is False


def test_check_no_duplicates_passes_on_unique_keys(spark):
    df = spark.createDataFrame(
        [("AAPL", "2026-01-01"), ("MSFT", "2026-01-01")], ["symbol", "ingestion_date"]
    )
    assert check_no_duplicates(["symbol", "ingestion_date"])(df) is True


def test_check_row_count_min(spark):
    df = spark.createDataFrame([(1,), (2,), (3,)], ["x"])
    assert check_row_count_min(3)(df) is True
    assert check_row_count_min(4)(df) is False
