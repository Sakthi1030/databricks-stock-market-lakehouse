# Architecture Decisions

This doc exists to answer *"why did you build it this way"* — the question interviewers
actually ask, versus *"what did you build"*, which the README already covers. Every entry
here reflects a real decision made (and in several cases, a real bug found and fixed) during
this build — not textbook advice copied in afterward.

## 1. Medallion architecture (Bronze → Silver → Gold)

**Decision:** three layers, each with a single, non-overlapping responsibility.

- **Bronze** — raw, append-only, exactly as the source API returned it plus lineage columns
  (`ingestion_date`, `bronze_load_timestamp`). No cleaning, no dedup, ever.
- **Silver** — cleaned, typed, deduplicated, conformed to a stable schema.
- **Gold** — dimensional model (star schema) and pre-aggregated marts, shaped for what BI/API
  consumers actually query.

**Why:** if a bug in Silver's transformation logic corrupts data, Bronze is untouched — the
fix is "correct the transform, replay from Bronze," not "re-extract from a source that may no
longer return the same data." Bronze is the audit trail; nothing downstream is trusted as the
source of truth for what actually happened.

**Trade-off accepted:** more storage (raw data persists forever) and more code (three
transformation stages instead of one). Worth it for the replay guarantee.

## 2. Two different merge strategies in Silver — Type 1 vs SCD Type 2

**Decision:** `silver.merge.upsert_quotes_type1` overwrites in place (one row per
`symbol, ingestion_date`); `silver.merge.upsert_profiles_scd2` keeps full history
(`effective_start_date`, `effective_end_date`, `is_current`).

**Why they're different:** a quote is a point-in-time fact — if the pipeline reruns the same
day, the old value should simply be replaced, no history of intraday reruns needed. A company
profile (name, exchange, industry, market cap) is a dimension whose *history* has value — "what
did we know about this company on a given date" is a real, answerable question with SCD2, and
an unanswerable one with Type 1.

**How the SCD2 merge actually works** (`silver/merge.py`): a two-step Delta `MERGE`, not one —
step 1 expires the current row for any symbol whose `attr_hash` changed (a SHA-256 hash of the
tracked columns, so "did anything change" is one comparison instead of four); step 2 appends a
new current-version row for every changed or new symbol. A single `MERGE` can't both expire an
old row and insert its replacement in one pass without ambiguity, hence two steps.

## 3. Delete-then-insert vs merge for Gold's recomputed marts

**Decision:** `top_movers`, `daily_market_summary`, and `sector_summary` use
`_replace_date_partition` (delete the day's rows, then insert the freshly computed set) —
*not* the same `MERGE`-based upsert that `fact_daily_quotes` and `dim_company` use.

**Why — this was a real production bug, not a hypothetical:** these three marts are fully
*recomputed* from Silver on every run, not naturally incremental facts. A row-level `MERGE`
only touches rows present in the new source. When a rerun's computed set is *smaller* than an
earlier run's for the same date (e.g. an intraday price recovery drops the loser count from 5
to 3), the extra rows from the earlier run are simply never matched by the new source — so
they're neither updated nor deleted, and linger forever. This showed up live: the React
dashboard displayed JPM and TSLA as "top losers" with *positive* percent-change values,
leftover from an earlier snapshot that day. Delete-then-insert on the date partition makes
this class of bug structurally impossible — the partition always exactly matches what was just
computed.

**The general principle:** merge-without-delete is correct for naturally incremental data
(one new fact per key per run). It is *not* correct for fully-recomputed aggregates, regardless
of how reasonable it looks at first ("just upsert everything" is the tempting shortcut here).

## 4. Surrogate keys via deterministic hash, not `monotonically_increasing_id()`

**Decision:** `dim_company.sk_company = xxhash64(symbol)`.

**Why not `monotonically_increasing_id()`:** it's not deterministic across separate
DataFrame computations or repartitions — the same row can get a different ID the next time the
dimension is rebuilt, silently breaking every fact-table foreign key that pointed at the old
value. `xxhash64(symbol)` always produces the same key for the same symbol, on any run, on any
cluster — rebuilding the dimension never invalidates existing fact-table joins. Verified with a
test (`test_surrogate_key_is_deterministic_for_same_symbol`) that calls the builder twice and
asserts the same key comes back both times.

## 5. Environment-aware paths, not a forked "Databricks version" of the code

**Decision:** `etl.utils.paths` detects `DATABRICKS_RUNTIME_VERSION` (set automatically on
every Databricks cluster) and switches between local filesystem paths and Databricks storage —
same function, same call sites, no branching in the calling code.

**Why this needed more than one attempt:** the "Databricks storage" side of this changed twice
during the build, from real failures, not preference:
1. Started with raw DBFS paths (`dbfs:/lakehouse/...`) — broke on serverless compute, which
   doesn't support the legacy `/dbfs` FUSE mount for plain file I/O (`OSError: Operation not
   supported`).
2. Moved everything to Unity Catalog Volumes (`/Volumes/workspace/default/lakehouse/...`) —
   fixed Bronze/Silver, but Gold (the BI-serving layer) needed to be *queryable as tables* from
   Power BI's Databricks connector, and a Volume is file storage, not a catalog table.
3. Gold specifically now resolves to Unity Catalog **managed tables**
   (`gold_table_ref` → `workspace.default.<name>`) via `saveAsTable`/`DeltaTable.forName`,
   while Bronze/Silver stay on Volume-backed paths.

**Also caught by testing, not manual review:** `spark_path()` mixed OS-native path separators
(from `pathlib.Path`) with a hardcoded `/` when appending an entity name, producing paths like
`C:\...\bronze/quotes` on Windows. Harmless in practice (Spark/Hadoop tolerates mixed
separators), but real — fixed by using `.as_posix()` consistently, since Spark/Databricks paths
are URI-style and should always be forward-slash regardless of host OS.

## 6. FastAPI as a mandatory layer between React and Databricks

**Decision:** React never talks to Databricks directly — only Power BI does, via its native
connector. React calls FastAPI, which holds the Databricks credential server-side.

**Why:** a Databricks token embedded in frontend JavaScript is visible to anyone who opens
browser DevTools — there is no way to ship a secret to a browser and keep it secret. FastAPI
is the boundary where the credential actually stays a credential.

**A consequence worth naming explicitly:** Power BI (Import mode) and React are *not*
equivalent freshness-wise. Power BI's `.pbix`/PBIP holds a point-in-time snapshot from the last
manual refresh; React queries live through FastAPI on every page load. "Why does Power BI show
yesterday's numbers" has a real, specific answer rooted in that mode choice — not a bug.

## 7. Parameterized SQL, verified by test — not just asserted

**Decision:** every user-supplied value in `backend/main.py` (e.g. `symbol`, `mover_type`)
travels as a bind parameter (`:symbol`) via `run_query(query, {"symbol": symbol})`, never
string-interpolated into SQL.

**Why a test and not just a code review:** `test_quote_history_passes_symbol_as_parameter_not_string_interpolation`
sends a real SQL injection payload as the `symbol` value and asserts the raw query string
never contains it, and that it was passed as a bind parameter instead. This is the difference
between "I'm pretty sure this is safe" and "this is verifiably safe" — a reviewer reading the
code has to trust the pattern was followed everywhere; the test proves it for the one endpoint
that actually accepts free-text user input.

## 8. Testing strategy: mock the DB for API tests, use a real Spark session for transforms

**Decision:** `tests/backend/` mocks `run_query` entirely (fast, hermetic, no live Databricks
dependency in CI). `tests/silver/` and `tests/gold/` run against a real local `SparkSession`
via a shared session-scoped fixture (`tests/conftest.py`) — no mocking of Spark itself.

**Why the split:** the backend layer's logic worth testing is routing, validation, and query
construction — none of which benefits from a real database round-trip, and a live-Databricks
dependency in CI would make tests slow and flaky. The transform layer's logic worth testing
*is* Spark behavior (window functions, joins, aggregations, `MERGE` semantics) — mocking Spark
there would mean testing nothing real. Each layer gets the testing strategy that matches what
actually needs verifying.

**A genuine gotcha this caught:** `spark.createDataFrame` cannot infer a schema for a column
that is `None` in every sample row (`CANNOT_DETERMINE_TYPE`) — an early version of the Gold
fact-table tests used `None` for an unused `quote_timestamp` column and failed for a reason
unrelated to the code under test. Fixed by using a real value instead — a small but real
lesson in what "unused" actually means when Spark still needs to type the column.

## 9. CI split into 4 jobs instead of one

**Decision:** `syntax-check` (no dependencies), `backend-tests` (minimal install, no PySpark),
`pyspark-tests` (full install + Java, isolated so `backend-tests` stays fast), `frontend`
(lint + Vitest + build).

**Why split rather than one big job:** PySpark installation and a Java setup step add real
time; keeping them out of the backend-tests job means a pure-API change gets fast CI feedback
without waiting on Spark. `syntax-check` costs nothing and catches import/syntax errors across
the whole pipeline before the heavier jobs even start.
