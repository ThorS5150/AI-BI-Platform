"""Runs the answer step on the RAG test set and writes data/eval/rag_answers*.csv."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.llm.factory import get_llm  # noqa: E402
from modules.rag.answer import answer  # noqa: E402
from modules.rag.chunking import _PROJECT_ROOT  # noqa: E402
from modules.rag.retriever import Retriever  # noqa: E402

if len(sys.argv) > 1:  # e.g. python scripts\eval_answer.py data\eval\rag_testset_independent.csv
    TESTSET = Path(sys.argv[1])
    RESULTS = _PROJECT_ROOT / "data" / "eval" / f"rag_answers_{TESTSET.stem}.csv"
else:
    TESTSET = _PROJECT_ROOT / "data" / "eval" / "rag_testset.csv"
    RESULTS = _PROJECT_ROOT / "data" / "eval" / "rag_answers.csv"


def main():
    retriever = Retriever()
    llm = get_llm()  # LLM_PROVIDER in .env: 'local' (Ollama) or 'huggingface'
    with TESTSET.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    results = []
    for row in rows:
        result = answer(row["question"], retriever, llm)

        # Diagnostics: full ranking without threshold, best chunk score per section
        ranked = retriever.search(row["question"], k=len(retriever.chunks), min_score=-1.0)
        best_per_section = {}
        for h in ranked:  # sorted by score, so the first occurrence is the best chunk of that section
            best_per_section.setdefault(f"{h.chunk.doc} {h.chunk.section}", h.score)
        ordering = list(best_per_section.items())
        top1, top1_score = ordering[0][0], round(ordering[0][1], 3)
        expected_key = "none" if row["expected_doc"] == "none" else f"{row['expected_doc']} {row['expected_section']}"
        exp_rank = next((i + 1 for i, (k, _) in enumerate(ordering) if k == expected_key), "")
        exp_score = round(best_per_section[expected_key], 3) if expected_key in best_per_section else ""

        negative = row["expected_doc"] == "none"
        expected = "none" if negative else expected_key
        if negative:
            expected_in_sources = ""
            passed = not result.found
        else:
            expected_in_sources = expected in result.sources
            passed = result.found and expected_in_sources
        status = "OK " if passed else "ERR"
        print(f"{row['id']:>2} {status} expected={expected} -> {result.sources or 'NOT_FOUND'} "
              f"[top1={top1} {top1_score} | expected rank={exp_rank} score={exp_score}]")
        results.append({
            "id": row["id"],
            "language": row["language"],
            "question": row["question"],
            "expected": expected,
            "found": result.found,
            "top1": top1,
            "top1_score": top1_score,
            "expected_rank": exp_rank,
            "expected_score": exp_score,
            "expected_in_sources": expected_in_sources,
            "passed": passed,
            "sources": "; ".join(result.sources),
            "answer": result.text.replace("\n", " "),
            "reference": row.get("reference_answer", ""),
        })

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    positives = [r for r in results if r["expected"] != "none"]
    negatives = [r for r in results if r["expected"] == "none"]
    print(f"Positive: answered with expected source {sum(r['passed'] for r in positives)}/{len(positives)}")
    print(f"Negative: correctly not answered {sum(r['passed'] for r in negatives)}/{len(negatives)}")
    print(f"Results written to {RESULTS}")


if __name__ == "__main__":
    main()