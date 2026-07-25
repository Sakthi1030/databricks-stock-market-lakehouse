import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from etl.extract.finnhub_client import FinnhubClient
from etl.utils.config_loader import load_config
from etl.utils.exceptions import FinnhubAuthError
from etl.utils.logger import get_logger

logger = get_logger(__name__)


def save_raw(records: list, entity: str, project_root: Path, ingestion_date: str) -> Path:
    out_dir = project_root / "data" / "raw" / entity / f"ingestion_date={ingestion_date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{entity}_{datetime.now(timezone.utc).strftime('%H%M%S')}.json"
    with open(out_path, "w") as f:
        json.dump(records, f, indent=2)
    logger.info("Wrote %d %s records to %s", len(records), entity, out_path)
    return out_path


def main():
    config = load_config()
    finnhub_cfg = config["api"]["finnhub"]

    client = FinnhubClient(
        api_key=finnhub_cfg["api_key"],
        base_url=finnhub_cfg["base_url"],
        endpoints=finnhub_cfg["endpoints"],
        timeout_seconds=finnhub_cfg["timeout_seconds"],
        max_retries=finnhub_cfg["max_retries"],
        retry_backoff_seconds=finnhub_cfg["retry_backoff_seconds"],
    )

    tickers = config["tickers"]
    logger.info("Starting extract for %d tickers: %s", len(tickers), tickers)

    try:
        results = client.fetch_all(tickers)
    except FinnhubAuthError as exc:
        logger.error("Extract aborted: %s", exc)
        sys.exit(1)

    ingestion_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    project_root = Path(config["project_root"])

    for entity, records in results.items():
        if records:
            save_raw(records, entity, project_root, ingestion_date)
        else:
            logger.warning("No records extracted for %s", entity)

    logger.info(
        "Extract complete: %d quotes, %d profiles",
        len(results["quotes"]), len(results["profiles"]),
    )


if __name__ == "__main__":
    main()
