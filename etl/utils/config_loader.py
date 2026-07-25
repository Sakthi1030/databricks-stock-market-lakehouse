import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config() -> dict:
    """Load config.yaml and merge in secrets from .env. Fails fast if the API key is missing."""
    load_dotenv(PROJECT_ROOT / ".env")

    config_path = PROJECT_ROOT / "config" / "config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key or api_key == "your_finnhub_api_key_here":
        raise EnvironmentError(
            "FINNHUB_API_KEY is missing or unset. Copy .env.example to .env and set a real key from finnhub.io."
        )

    config["api"]["finnhub"]["api_key"] = api_key
    config["environment"] = os.getenv("ENVIRONMENT", "dev")
    config["project_root"] = str(PROJECT_ROOT)
    return config
