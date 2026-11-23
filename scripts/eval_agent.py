"""Routing evaluation for the agent router (docs/11).

Usage:
  python scripts/eval_agent.py [testset.csv] [results.csv]

Defaults: data/eval/agent_testset.csv and data/eval/agent_results.csv.
The testset must be comma-separated UTF-8 with the header: id,language,question,expected
Multiple expected tools are separated by ';' inside the expected column.
Needs no Databricks, no model and no langgraph.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.agents.router import route  # noqa: E402

TOOLS = ["kpi", "forecast", "rag"]
REQUIRED = {"question", "expected"}


def load_testset(path: Path) -> list[dict]:
    # utf-8-sig removes a BOM that Excel sometimes adds at the start of the file
    with path.open(encoding="utf-8-sig", newline="") as f:
        header_line = f.readline()
        if ";" in header_line and "," not in header_line:
            raise SystemExit(
                f"{path} uses ';' as separator. Save it as comma-separated UTF-8 "
                f"with the header id,language,question,expected."
            )
        f.seek(0)
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"{path} has no rows.")
    missing = REQUIRED - set(rows[0].keys())
    if missing:
        raise SystemExit(f"{path} is missing columns {sorted(missing)}. Found: {list(rows[0].keys())}")
    return rows


def main():
    testset = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "eval" / "agent_testset.csv"
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data" / "eval" / "agent_results.csv"
    rows = load_testset(testset)

    tp, fp, fn = Counter(), Counter(), Counter()
    exact = 0
    results = []
    for row in rows:
        expected = set(row["expected"].split(";"))
        predicted = set(route(row["question"]))
        passed = expected == predicted
        exact += passed
        for tool in TOOLS:
            if tool in predicted and tool in expected:
                tp[tool] += 1
            elif tool in predicted:
                fp[tool] += 1
            elif tool in expected:
                fn[tool] += 1
        results.append({
            "id": row.get("id", ""),
            "question": row["question"],
            "expected": row["expected"],
            "predicted": ";".join(sorted(predicted)),
            "passed": passed,
        })

    print(f"Testset: {testset.name}")
    print(f"Routing accuracy (exact tool set): {exact}/{len(rows)} = {exact / len(rows):.0%}")
    for tool in TOOLS:
        p = tp[tool] / (tp[tool] + fp[tool]) if tp[tool] + fp[tool] else float("nan")
        r = tp[tool] / (tp[tool] + fn[tool]) if tp[tool] + fn[tool] else float("nan")
        print(f"  {tool:9s} precision {p:.2f}  recall {r:.2f}")

    print("Mismatches:")
    for result in results:
        if not result["passed"]:
            print(f"  {result['id']}: expected {result['expected']}, got {result['predicted']} | {result['question']}")

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print("Written:", out_path)


if __name__ == "__main__":
    main()