"""Lightweight, dependency-free data quality checks.

Not a full framework — just enough structure to fail fast on corrupt data before it reaches
Silver, with a clear pass/fail report instead of a pipeline that silently writes garbage.
"""
from dataclasses import dataclass, field
from typing import Callable, List

from pyspark.sql import DataFrame

from etl.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DQCheck:
    name: str
    check_fn: Callable[[DataFrame], bool]
    critical: bool = True  # critical failure aborts the pipeline; non-critical only warns


@dataclass
class DQReport:
    passed: List[str] = field(default_factory=list)
    failed: List[dict] = field(default_factory=list)

    @property
    def has_critical_failure(self) -> bool:
        return any(f["critical"] for f in self.failed)


def run_checks(df: DataFrame, checks: List[DQCheck], context: str) -> DQReport:
    report = DQReport()
    for check in checks:
        try:
            ok = check.check_fn(df)
        except Exception as exc:
            ok = False
            logger.error("[%s] DQ check '%s' raised an exception: %s", context, check.name, exc)

        if ok:
            report.passed.append(check.name)
            logger.info("[%s] DQ check passed: %s", context, check.name)
        else:
            report.failed.append({"name": check.name, "critical": check.critical})
            log_fn = logger.error if check.critical else logger.warning
            log_fn("[%s] DQ check FAILED (%s): %s", context, "critical" if check.critical else "non-critical", check.name)

    return report


def check_no_nulls(columns: List[str]) -> Callable[[DataFrame], bool]:
    def _check(df: DataFrame) -> bool:
        for c in columns:
            if df.filter(df[c].isNull()).limit(1).count() > 0:
                return False
        return True
    return _check


def check_positive(column: str) -> Callable[[DataFrame], bool]:
    def _check(df: DataFrame) -> bool:
        return df.filter(df[column] <= 0).limit(1).count() == 0
    return _check


def check_no_duplicates(key_columns: List[str]) -> Callable[[DataFrame], bool]:
    def _check(df: DataFrame) -> bool:
        return df.count() == df.dropDuplicates(key_columns).count()
    return _check


def check_row_count_min(min_rows: int) -> Callable[[DataFrame], bool]:
    def _check(df: DataFrame) -> bool:
        return df.count() >= min_rows
    return _check
