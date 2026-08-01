"""Backend API tests.

The Databricks connection is always mocked here — these test our routing, validation, and
response-shaping logic, not whether Databricks itself is reachable. That's deliberate: tests
that depend on a live external warehouse are slow and flaky in CI, and the parts worth unit
testing (input validation, SQL parameterization, error handling) don't need real data anyway.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("backend.main.run_query")
def test_companies_returns_query_results(mock_run_query):
    mock_run_query.return_value = [
        {
            "sk_company": 123,
            "symbol": "AAPL",
            "ticker": "AAPL",
            "name": "Apple Inc",
            "exchange": "NASDAQ",
            "country": "US",
            "currency": "USD",
            "industry": "Technology",
            "market_cap_musd": 4500000.0,
            "shareOutstanding": 14000.0,
            "ipo": "1980-12-12",
            "weburl": "https://www.apple.com/",
        }
    ]

    response = client.get("/api/companies")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["symbol"] == "AAPL"
    mock_run_query.assert_called_once()


@patch("backend.main.run_query")
def test_quote_history_not_found_returns_404(mock_run_query):
    mock_run_query.return_value = []

    response = client.get("/api/quotes/history", params={"symbol": "FAKESYMBOL"})

    assert response.status_code == 404
    assert "FAKESYMBOL" in response.json()["detail"]


@patch("backend.main.run_query")
def test_quote_history_passes_symbol_as_parameter_not_string_interpolation(mock_run_query):
    """The whole point of parameterized queries: user input must travel as a bind parameter,
    never get concatenated into the SQL string itself. This is what actually prevents
    injection — asserting on it directly, not just checking the endpoint "works".
    """
    mock_run_query.return_value = [{"symbol": "AAPL", "ingestion_date": "2026-01-01"}]

    malicious_input = "AAPL'; DROP TABLE fact_daily_quotes; --"
    client.get("/api/quotes/history", params={"symbol": malicious_input})

    called_query, called_params = mock_run_query.call_args[0]
    assert malicious_input not in called_query
    assert called_params == {"symbol": malicious_input}


def test_movers_rejects_invalid_mover_type():
    # No DB mock needed — FastAPI's Query(pattern=...) validates before the handler ever runs.
    response = client.get("/api/movers", params={"mover_type": "hacker"})
    assert response.status_code == 422


@patch("backend.main.run_query")
def test_movers_accepts_valid_mover_type(mock_run_query):
    mock_run_query.return_value = []
    response = client.get("/api/movers", params={"mover_type": "gainer"})
    assert response.status_code == 200


@patch("backend.main.run_query")
def test_summary_not_found_returns_404(mock_run_query):
    mock_run_query.return_value = []
    response = client.get("/api/summary/latest")
    assert response.status_code == 404
