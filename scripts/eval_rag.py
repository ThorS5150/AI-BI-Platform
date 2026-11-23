"""Retrieval evaluation against data/eval/rag_testset.csv (no language model needed).

A hit means the same policy section (document + section number), regardless of
language. The English and French versions of a section are the same rule, so
matching on language would count a correct answer as a miss. The language is
still recorded per question, so cross-language matches stay visible.

Measures:
- Top 1 (ranking) and Top 3, each without and with the score threshold.
- Negative questions: stays empty with the threshold applied.
- Best-hit scores, used to calibrate MIN_SCORE.

Run from the project folder: python scripts/eval_rag.py
"""
import csv
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.rag.retriever import MIN_SCORE, TOP_K, Retriever  # noqa: E402

TESTSET = ROOT / "data" / "eval" / "rag_testset.csv"
RESULTS = ROOT / "data" / "eval" / "rag_retrieval_results.csv"


def section_key(chunk):
    return (chunk.doc, chunk.section)


def main():
    retriever = Retriever()
    rows = list(csv.DictReader(TESTSET.open(encoding="utf-8")))
    results = []
    pos_top1, pos_top3, pos_thresh = 0, 0, 0
    pos_total = neg_total = neg_ok = 0
    pos_scores, neg_scores = [], []
    per_lang = {"en": [0, 0], "fr": [0, 0]}
    cross_language_top1 = 0

    for row in rows:
        all_hits = retriever.search(row["question"], k=TOP_K, min_score=-1.0)
        filtered = [h for h in all_hits if h.score >= MIN_SCORE]
        top1 = all_hits[0] if all_hits else None
        top1_score = top1.score if top1 else 0.0

        if row["expected_doc"] == "none":
            neg_total += 1
            passed = len(filtered) == 0
            neg_ok += passed
            neg_scores.append(top1_score)
            in_top1 = in_top3 = above = ""
        else:
            pos_total += 1
            key = (row["expected_doc"], row["expected_section"])
            in_top1 = bool(all_hits) and section_key(top1.chunk) == key
            in_top3 = any(section_key(h.chunk) == key for h in all_hits)
            above = any(section_key(h.chunk) == key for h in filtered)
            pos_top1 += in_top1
            pos_top3 += in_top3
            pos_thresh += above
            pos_scores.append(top1_score)
            per_lang[row["language"]][0] += 1
            per_lang[row["language"]][1] += above
            if in_top1 and top1.chunk.language != row["language"]:
                cross_language_top1 += 1
            passed = above

        results.append({
            "id": row["id"],
            "language": row["language"],
            "question": row["question"],
            "expected": f"{row['expected_doc']} {row['expected_section']}",
            "top1": f"{top1.chunk.doc} {top1.chunk.section} ({top1.chunk.language})" if top1 else "-",
            "top1_score": round(top1_score, 3),
            "expected_in_top1": in_top1,
            "expected_in_top3": in_top3,
            "expected_above_threshold": above,
            "passed": passed,
        })

    with RESULTS.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"Positive questions: {pos_total}")
    print(f"  Top 1 (ranking):                 {pos_top1}/{pos_total} = {pos_top1 / pos_total:.0%}")
    print(f"    of which correct section, other language: {cross_language_top1}")
    print(f"  Top {TOP_K} without threshold:          {pos_top3}/{pos_total} = {pos_top3 / pos_total:.0%}")
    print(f"  Top {TOP_K} with threshold {MIN_SCORE}:        {pos_thresh}/{pos_total} = {pos_thresh / pos_total:.0%}")
    for lang, (total, hit) in per_lang.items():
        print(f"    {lang}: {hit}/{total}")
    print(f"Negative questions: {neg_total}")
    print(f"  Correctly empty with threshold {MIN_SCORE}: {neg_ok}/{neg_total}")
    print()
    print("Top-1 score, positive questions: min {:.3f} | median {:.3f} | max {:.3f}".format(
        min(pos_scores), statistics.median(pos_scores), max(pos_scores)))
    print("Top-1 score, negative questions: min {:.3f} | median {:.3f} | max {:.3f}".format(
        min(neg_scores), statistics.median(neg_scores), max(neg_scores)))
    print()
    print("Details:", RESULTS)


if __name__ == "__main__":
    main()