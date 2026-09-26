# Radar data (raw zone)

Written by the `NSE News Radar` GitHub Action on every trading day; read by the Databricks
Bronze job and, as a fallback, by the API. Code lives on `master`.

- `latest.json`: the most recent 2 PM run
- `runs/<date>.json`: one file per trading day
- `candidates.jsonl`, `news.jsonl`, `outcomes.jsonl`: append-only history (upserted by key)

`react/vercel.json` only stops Vercel from deploying this branch.
