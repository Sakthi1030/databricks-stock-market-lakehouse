import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config() -> dict:
    """Load config.yaml and merge in secrets from .env.

    Deliberately does NOT validate FINNHUB_API_KEY here — Bronze, Silver, and Gold all call
    this function too, and none of them use that key. Validation belongs at the point of use
    (FinnhubClient already raises FinnhubAuthError if it's missing), not in generic config
    loading that every layer depends on.
    """
    load_dotenv(PROJECT_ROOT / ".env")

    config_path = PROJECT_ROOT / "config" / "config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    api_key = os.getenv("FINNHUB_API_KEY")
    if api_key == "your_finnhub_api_key_here":
        api_key = None
    config["api"]["finnhub"]["api_key"] = api_key
    config["environment"] = os.getenv("ENVIRONMENT", "dev")
    config["project_root"] = str(PROJECT_ROOT)
    return config
