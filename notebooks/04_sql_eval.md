# 04 SQL Evaluation (Databricks)

Runs the SQL candidates from `scripts/gen_sql_candidates.py` against the Gold tables and counts errors.

Before running: upload `data/eval/sql_candidates.csv` to the workspace, for example to
`/Workspace/Users/<your-user>/sql_candidates.csv`, and set `CANDIDATES` below.

## Cell 1: Execute the candidates

```python
import pandas as pd

CANDIDATES = "/Workspace/Users/<your-user>/sql_candidates.csv"

c = pd.read_csv(CANDIDATES, keep_default_na=False)
results = []
for _, r in c.iterrows():
    if str(r["guard_ok"]).lower() != "true":
        results.append({"id": r["id"], "status": "guard_error", "error": r["guard_error"]})
        continue
    try:
        spark.sql(r["sql"]).collect()
        results.append({"id": r["id"], "status": "ok", "error": ""})
    except Exception as e:
        results.append({"id": r["id"], "status": "sql_error", "error": str(e)[:300]})

res = pd.DataFrame(results)
errors = (res["status"] != "ok").sum()
print(f"Candidates: {len(res)}")
print(res["status"].value_counts().to_string())
print(f"SQL error rate: {errors}/{len(res)} = {errors / len(res):.0%}")
display(res[res["status"] != "ok"])
```

## Cell 2: Show the failing statements

```python
failing = c.merge(res[res["status"] != "ok"], on="id")
display(failing[["id", "question", "sql", "status", "error"]])
```

## Reading the result
- `guard_error`: the statement was never sent to Spark (not a SELECT, a table outside the allowlist, or a write keyword).
- `sql_error`: Spark rejected it (syntax, unknown column, wrong join). Look at the message to see which kind.
- The error rate counts both kinds against all candidates.