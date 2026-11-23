# 09 RAG Evaluation

## Test set
File: `data/eval/rag_testset.csv`, 28 questions:
- 24 questions with an expected source (document and section): 13 English, 11 French
- 4 negative questions with no answer in the policies (competitor vehicle price, central bank rate, loyalty program, cryptocurrency payments)

Independent test set, not used for tuning: `data/eval/rag_testset_independent.csv`, 15 questions (12 positive, 3 negative) with reference answers.

## Metrics
- **Top 1 (section level):** Is the expected section ranked first? Language is recorded separately and is not a matching criterion.
- **Top 3:** Is the expected section among the three best hits? Measured without and with the score threshold.
- **Negative questions:** Is the result empty when the threshold is applied?
- **Answer quality:** manual check of each answer against the policy text.

Scripts: `scripts/eval_rag.py` (retrieval, 28 questions), `scripts/eval_answer.py` (answer step, any test set as argument). Per-question results in `data/eval/`.

Matching is done at section level (e.g. 1.2), not per language chunk. An English question whose best hit is the French chunk of the correct section counts as a hit. A strict language-keyed evaluation gave Top 1 = 17/24 (71%) in an earlier run, so the Top 1 value depends on this definition.

## Threshold
`MIN_SCORE = 0.55` in `modules/rag/retriever.py`.

Best-hit scores (MiniLM, run 1; for bge-m3 see run 4):
- Positive questions: 0.558 to 0.908 (median 0.772)
- Negative questions: 0.438 to 0.616 (median 0.488)

Caveat: 0.55 was chosen on the same 28 questions that the evaluation uses, so this is tuning on the test set. The lowest positive score (0.558, question 24) is only 0.008 above the threshold. The value is provisional and must be checked against a larger, independent test set.

## Results

### Run 1: retrieval, model `paraphrase-multilingual-MiniLM-L12-v2`, section-level matching

| Metric | Result |
|---|---|
| Top 1 | 22/24 (92%) |
| Top 1 English | 12/13 |
| Top 1 French | 10/11 |
| Top 3 without threshold | 24/24 (100%) |
| Top 3 with threshold 0.55 | 24/24 (100%) |
| Negative questions empty with threshold | 3/4 (75%) |

### Run 2: answer step, local LLM via Ollama

Sources are taken from retrieval, not from the model. "Sources correct" counts the expected section among the cited sources for positive questions. Answer content is checked manually against the policy text.

| Model and prompt | Sources correct (positive) | Negatives correctly "not found" | Answer content correct (manual) |
|---|---|---|---|
| `qwen2.5:3b-instruct`, first prompt | 22/24 | 4/4 | not scored |
| `qwen2.5:3b-instruct`, strict prompt | 20/24 | 4/4 | not scored, e.g. Q8 answered "20000" instead of 300 km |
| `qwen2.5:7b-instruct`, strict prompt | 24/24 | 4/4 | 23/24 |
| `qwen2.5:7b-instruct`, prohibitions rule and cited sources (run 3) | 24/24 | 4/4 | 24/24 |

Run 3 changes: the prompt treats prohibitions and exclusions as answers. The model names the sections it used in a "Sources used:" line, and the code shows only those sections (retrieved sections only, top-1 as fallback). Sources now show one section per answer instead of all hits above the threshold.

Result of run 3: the 7B model with the run 3 prompt was the default. The test set and the prompt were both tuned on these 28 questions, so run 3 is not an independent result.

### Run 4: embedding model `BAAI/bge-m3` (default from now on)

Retrieval on the 28-question test set:

| Metric | Run 1 (MiniLM) | Run 4 (bge-m3) |
|---|---|---|
| Top 1 | 22/24 (92%) | 24/24 (100%) |
| Top 3 without threshold | 24/24 | 24/24 |
| Top 3 with threshold 0.55 | 24/24 | 24/24 |
| Negative questions empty | 3/4 | 3/4 |
| Top-1 score, positive (min / median / max) | 0.558 / 0.772 / 0.908 | 0.645 / 0.737 / 0.810 |
| Top-1 score, negative (min / median / max) | 0.438 / 0.488 / 0.616 | 0.413 / 0.505 / 0.592 |

Independent test set (15 questions, `data/eval/rag_testset_independent.csv`), answer step with `qwen2.5:7b-instruct`:
- Sources correct: 12/12 positive (MiniLM: 10/12)
- Negatives correctly "not found": 3/3
- Answer content (manual): 8 correct, 2 partly correct, 2 wrong (questions 2 and 12). Questions 3, 6 and 9 improved over MiniLM, none got worse.
- Question 3 ranks section 4.2 third with score 0.56, just above the threshold.

The 28-question set was used to tune the threshold and the prompt. On the independent set, a negative question scores 0.597, above positive question 3 at 0.56. No single threshold separates the two groups there, so the answer step carries the negative filter. The threshold stays at 0.55; run 4 gives no reason to change it.

## Known errors
0. **Question 4, 12 % discount (French), fixed in run 3:** Run 2 answered "Not found." although section 1.2 says discounts above 10 % are not permitted. Run 3 answers "No" with the rule. Open risk: the source metric alone counts a wrong answer as passed, so answer content must stay in the manual check.
1. **Question 12, "delivery radius" (English), fixed in run 4:** MiniLM ranked section 3.3 first. bge-m3 ranks section 3.1 first.
2. **Question 10, refund fees (French), fixed in run 4:** MiniLM ranked section 4.4 first. bge-m3 ranks section 2.3 first.
3. **Question 27, loyalty program (English, negative):** Best score 0.616 with MiniLM is above the threshold. Section 1.1 is returned although the topic does not appear in the policies. The answer step must check whether the section answers the question.
4. **Independent set, question 2 (French, used car from 2016):** The model answers "Oui". A 2016 car is over 5 years old, so the correct answer is "Non". Open.
5. **Independent set, question 12 (French, 3 % promotion):** The model answers "No" and misreads "above 3 %". Correct answer: "Oui". Open.

## Consequences for the answer step
- The answer step receives all hits above the threshold, not only the first one.
- Before answering, it checks whether the section actually answers the question. Otherwise it returns "nothing found". This catches question 27.
- The model names the sections it used. Only those are shown as sources, with the top-1 hit as fallback.
- Errors 4 and 5 are reasoning errors of the 7B model on conditions and limits. Ranking changes do not fix them; a larger model is the next test.