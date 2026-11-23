"""Generate SQL candidates for the KPI questions of a test set (docs/11, SQL error rate).

Run locally, where the LLM is available (LLM_PROVIDER in .env, e.g. Ollama).
Writes data/eval/sql_candidates.csv: one row per question with the generated SQL and
the guard result. Execution happens in Databricks (notebooks/04_sql_eval.md).

Usage:
  python scripts/gen_sql_candidates.py [testset.csv] [candidates.csv]
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.agents.guard import UnsafeSQL, check_read_only  # noqa: E402
from modules.agents.sql_gen import generate_sql, kpi_part  # noqa: E402
from modules.llm.factory import get_llm  # noqa: E402


def main():
    testset = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "eval" / "agent_testset_set4.csv"
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data" / "eval" / "sql_candidates.csv"

    with testset.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if "kpi" in r["expected"].split(";")]
    if not rows:
        raise SystemExit("No KPI questions in the testset.")

    llm = get_llm()
    results = []
    for row in rows:
        sql = generate_sql(kpi_part(row["question"]), llm)
        try:
            check_read_only(sql)
            guard_ok, guard_error = True, ""
        except UnsafeSQL as error:
            guard_ok, guard_error = False, str(error)
        results.append({
            "id": row.get("id", ""),
            "question": row["question"],
            "sql": sql,
            "guard_ok": guard_ok,
            "guard_error": guard_error,
        })
        print(f"{row.get('id', '')}: guard {'ok' if guard_ok else 'FAILED'} {guard_error}")

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    failed = sum(not r["guard_ok"] for r in results)
    print(f"Candidates: {len(results)}, guard failures: {failed}")
    print("Written:", out_path)


if __name__ == "__main__":
    main()