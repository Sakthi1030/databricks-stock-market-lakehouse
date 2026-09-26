"""The raw zone: JSON files on the repo's `data` branch, read later by the Databricks Bronze job.

latest.json            the most recent run, whole (the website's instant fallback)
runs/<date>.json       one file per trading day
candidates.jsonl       every scored stock, per day        (key: date + symbol)
news.jsonl             every classified headline          (key: id)
outcomes.jsonl         what happened the next day         (key: date + symbol)
"""
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def upsert_jsonl(path: Path, rows: list[dict], key) -> None:
    merged = {key(r): r for r in read_jsonl(path)}
    merged.update({key(r): r for r in rows})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in merged.values()), encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def save_run(data_dir: Path, run: dict) -> None:
    day = run["market_date"]
    write_json(data_dir / "latest.json", run)
    write_json(data_dir / "runs" / f"{day}.json", run)
    upsert_jsonl(data_dir / "candidates.jsonl",
                 [{"date": day, **c} for c in run["candidates"]], key=lambda r: f"{r['date']}|{r['symbol']}")
    upsert_jsonl(data_dir / "news.jsonl",
                 [{"date": day, **n} for n in run["news"]], key=lambda r: r["id"])
