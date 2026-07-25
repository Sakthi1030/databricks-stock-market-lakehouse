import time
from datetime import datetime, timezone

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from etl.utils.exceptions import (
    FinnhubAuthError,
    FinnhubError,
    FinnhubRateLimitError,
    FinnhubRequestError,
    FinnhubServerError,
    FinnhubTransientError,
)
from etl.utils.logger import get_logger

logger = get_logger(__name__)


class FinnhubClient:
    """Resilient REST client for the Finnhub API: auth, structured errors, retry-with-backoff."""

    def __init__(self, api_key: str, base_url: str, endpoints: dict,
                 timeout_seconds: int = 10, max_retries: int = 3, retry_backoff_seconds: int = 2):
        if not api_key:
            raise FinnhubAuthError("No API key provided to FinnhubClient.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.endpoints = endpoints
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff_seconds
        self.session = requests.Session()

    def _get(self, path: str, params: dict) -> dict:
        @retry(
            reraise=True,
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=self.retry_backoff, min=1, max=30),
            retry=retry_if_exception_type(
                (FinnhubTransientError, requests.exceptions.ConnectionError, requests.exceptions.Timeout)
            ),
        )
        def _do_request():
            url = f"{self.base_url}{path}"
            request_params = {**params, "token": self.api_key}
            logger.info("Requesting %s params=%s", path, params)

            try:
                response = self.session.get(url, params=request_params, timeout=self.timeout)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
                logger.warning("Network error calling %s: %s — will retry", path, exc)
                raise

            if response.status_code in (401, 403):
                logger.error("Auth failed calling %s: HTTP %s", path, response.status_code)
                raise FinnhubAuthError(f"Finnhub rejected the API key (HTTP {response.status_code}). Check .env.")

            if response.status_code == 429:
                logger.warning("Rate limited calling %s (HTTP 429) — will retry with backoff", path)
                raise FinnhubRateLimitError("Finnhub rate limit exceeded (HTTP 429).")

            if 500 <= response.status_code < 600:
                logger.warning("Server error calling %s (HTTP %s) — will retry", path, response.status_code)
                raise FinnhubServerError(f"Finnhub server error (HTTP {response.status_code}).")

            if response.status_code != 200:
                logger.error("Request to %s failed: HTTP %s — %s", path, response.status_code, response.text[:300])
                raise FinnhubRequestError(f"HTTP {response.status_code} calling {path}: {response.text[:300]}")

            return response.json()

        return _do_request()

    def get_quote(self, symbol: str) -> dict:
        data = self._get(self.endpoints["quote"], {"symbol": symbol})
        data["symbol"] = symbol
        return data

    def get_profile(self, symbol: str) -> dict:
        data = self._get(self.endpoints["profile"], {"symbol": symbol})
        data["symbol"] = symbol
        return data

    def fetch_all(self, tickers: list, calls_per_minute_limit: int = 55) -> dict:
        """Fetch quote + profile for every ticker, self-throttled under the free-tier rate limit.

        Note: Finnhub's historical `/stock/candle` endpoint is paid-plan-only (HTTP 403 on the
        free tier), so there is no bulk historical backfill here. Instead, daily quote snapshots
        (each with that day's open/high/low/close) accumulate into our own historical time series
        over time in Bronze/Silver — the incremental-loading pattern, not a one-time backfill.
        """
        results = {"quotes": [], "profiles": []}
        call_count = 0
        window_start = time.monotonic()

        for symbol in tickers:
            for fetch_fn, bucket in (
                (lambda s=symbol: self.get_quote(s), "quotes"),
                (lambda s=symbol: self.get_profile(s), "profiles"),
            ):
                if call_count >= calls_per_minute_limit:
                    elapsed = time.monotonic() - window_start
                    sleep_for = max(0.0, 60 - elapsed)
                    if sleep_for > 0:
                        logger.info("Approaching rate limit — sleeping %.1fs", sleep_for)
                        time.sleep(sleep_for)
                    call_count = 0
                    window_start = time.monotonic()

                try:
                    record = fetch_fn()
                    record["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()
                    results[bucket].append(record)
                except FinnhubAuthError:
                    logger.error("Aborting fetch_all: API key invalid.")
                    raise
                except FinnhubError as exc:
                    logger.error("Skipping %s for %s after retries exhausted: %s", bucket, symbol, exc)
                finally:
                    call_count += 1

        return results
