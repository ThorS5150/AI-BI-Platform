# 11 Agent Evaluation

## Test sets
- `data/eval/agent_testset.csv` (set 1): 30 questions (26 English, 4 French). Written before run 1 by the same author as the router. Used for tuning since run 3.
- `data/eval/agent_testset_independent.csv` (set 2): 30 questions (24 English, 6 French). Written after run 1. Used for tuning since run 3.
- `data/eval/agent_testset_holdout.csv` (set 3): 30 questions (24 English, 6 French). Written before run 3. Its baseline misses were seen before the keyword change, so it is not a clean test.
- `data/eval/agent_testset_set4.csv` (set 4): 30 questions (24 English, 6 French). Written after the router v2 change, without changing the router afterwards. This is the cleanest set so far, but the same author wrote it and knows the keyword lists. It contains 13 KPI questions, of which 10 are pure KPI questions and 3 are mixed (KPI and policy).

Each row has the question and the expected tool set. Several tools are separated by `;`.

## Metrics
- **Routing accuracy:** share of questions where the predicted tool set equals the expected set exactly.
- **Precision and recall per tool:** kpi, forecast, rag.
- **SQL error rate:** share of generated SQL candidates that fail the guard or Spark. "Ok" means Spark accepted the statement. It does not mean the result is correct. Result values are not checked yet.

## Target
From docs/01: the agent selects the correct tool in at least 80 % of test questions.

## Scripts and notebook
- `scripts/eval_agent.py [testset.csv] [results.csv]`: routing evaluation. Needs no Databricks, no model and no langgraph.
- `scripts/gen_sql_candidates.py [testset.csv] [candidates.csv]`: generates SQL for the KPI questions with the local model (`LLM_PROVIDER` in `.env`). Writes `data/eval/sql_candidates.csv`.
- `notebooks/04_sql_eval.md`: executes the candidates in Databricks and counts guard and Spark errors.

## Router versions
- **v1 (runs 1 and 2):** keyword lists with generic KPI words ("units", "sales", "revenue") and forecast words ("forecast", "demand", "next N weeks").
- **v2 (runs 3 and 4):** adds specific KPI words ("turnover", "per car", "stock"), French words ("vendu", "prévision", "prévoir", "demande", "ventes"), forecast words ("expect", "project", "outlook"). Generic KPI words count only if the question has no forecast word. The KPI adapter in `modules/agents/adapters.py` got matching patterns.

## Routing results
| Run | Router | Test set | Routing accuracy | Status of the set | Note |
|---|---|---|---|---|---|
| 1 | v1 | set 1 | 27/30 (90 %) | untuned | Optimistic, same author as router |
| 2 | v1 | set 2 | 20/30 (67 %) | untuned | Target 80 % not reached |
| 3a | v1 | set 3 (holdout) | 19/30 (63 %) | baseline | Measured before the change |
| 3b | v2 | set 1 | 30/30 (100 %) | tuned | Not independent any more |
| 3c | v2 | set 2 | 30/30 (100 %) | tuned | Not independent any more |
| 3d | v2 | set 3 (holdout) | 29/30 (97 %) | not clean | See Limits |
| 4 | v2 | set 4 | 23/30 (77 %) | cleanest so far | Target 80 % not reached, no router change after writing the set |

Per tool, run 4 (set 4): kpi precision 0.75, recall 0.69; forecast precision 1.00, recall 0.67; rag precision 0.76, recall 1.00.

Decision (2026-11-21): the keyword router stays as it is (v2). No further keyword changes until a new test set exists.

## SQL error rate
| Run | Test set | Model | Candidates | Guard failures | Spark errors | SQL error rate | Note |
|---|---|---|---|---|---|---|---|
| 5 | set 4, KPI questions | local model from `.env` | 13 | 0 | 3 | 23 % (3/13) | before prompt and question changes |
| 6 | set 4, KPI questions | local model from `.env` | 13 | 0 | 0 | 0 % (0/13) | after kpi_part() and join hint |

Breakdown of run 5:
- Pure KPI questions (10): all 10 ran in Spark. Spark accepted them, values not checked.
- Mixed questions (3, KPI plus policy): all 3 failed.
  - Id 20 "revenue of 2024 and the delivery policy": invented GROUP BY with an aggregate (`GROUP_BY_AGGREGATE`).
  - Id 21 "units sold in 2022 and the warranty cover": invented column `d.warranty_cover` (`UNRESOLVED_COLUMN`).
  - Id 23 "margin per car in 2023 and the financing rules": `f.model` used, but `model` lives in `gold_dim_model`. The join is missing (`UNRESOLVED_COLUMN`). "Margin" is not in the KPI catalog.

Cause: the generator receives