class FinnhubError(Exception):
    """Base exception for all Finnhub API client errors."""


class FinnhubAuthError(FinnhubError):
    """API key missing, invalid, or rejected (HTTP 401/403). Never retried — a bad key won't fix itself."""


class FinnhubTransientError(FinnhubError):
    """Temporary failure a retry is likely to resolve (HTTP 429, HTTP 5xx, network hiccups)."""


class FinnhubRateLimitError(FinnhubTransientError):
    """HTTP 429 — rate limit exceeded."""


class FinnhubServerError(FinnhubTransientError):
    """HTTP 5xx — failure on Finnhub's side."""


class FinnhubRequestError(FinnhubError):
    """Any other non-2xx response (bad params, unknown symbol, etc). Not retried."""
