# 13 Agent Design (LangGraph)

Status: v1 skeleton. Router, tools, SQL guard and graph wiring are implemented and tested (tests/test_agents.py). Not yet implemented: SQL generation from the question, question-to-argument adapters, LLM router, evaluation run (docs/11).

## Tools
1. `sql_tool`: read-only SELECT on allowlisted Gold tables. Guard in `modules/agents/guard.py`.
2. `kpi_tool`: one KPI from the catalog in docs/07, calendar year filter only. Unknown KPI names are rejected.
3. `rag_tool`: policy search and answer, using `modules/rag`.
4. `forecast_tool`: batch forecast table `workspace.platform.gold_forecast_weekly` (docs/10). Totals use `forecast_units`, series queries show `forecast_units_rounded`.

## Routing
v1 uses a rule-based router (`modules/agents/router.py`) with keyword lists for forecast, KPI and policy questions. A question can call several tools in order. If no keyword matches, the question goes to the policy search.

Reason for the rule-based router: it is deterministic, and its accuracy can be measured on the test set in docs/11. An LLM router can replace it later without changing the tools.

## Graph
Question → Router → tool (one call per step, repeated for each routed tool) → End

Built as a LangGraph `StateGraph` in `modules/agents/graph.py`. Tools are injected as callables, so the graph can be tested with fakes.

## Protection rules
- SQL is read-only: one SELECT statement, no CTEs, no write or DDL keywords.
- Only allowlisted tables may appear after FROM or JOIN (Gold tables and the forecast table).
- KPI names are limited to the catalog. Years are limited to 2020 to 2025.
- Forecast keys may only contain letters, digits, `_` and `-`.
- Maximum tool calls per question: 4. The router returns at most 4 tools, and the graph stops at 4 calls. Each tool runs at most once per question.

## Known limits
- SQL generation (`modules/agents/sql_gen.py`) produces candidates with a local model. The graph does not call it yet. Every candidate passes the guard before it may run.
- The router uses keywords. "Discount" alone is not a KPI keyword, so "Which policy applies to discounts?" goes to policy search. "Average discount" routes to the KPI.
- The guard does not parse comma joins (`FROM a, b`). Only allowlisted tables are reachable, which limits the risk.
- The adapters that turn a question into tool arguments (KPI name, year, keys) are not implemented yet.

## SQL generation
- `modules/agents/sql_gen.py`: system prompt with the Gold schema and the KPI rules, the `kpi_part()` filter that removes policy clauses, extraction of the SELECT statement from the model answer, and a guard check.
- `scripts/gen_sql_candidates.py`: runs locally on the KPI questions of a test set and writes `data/eval/sql_candidates.csv`.
- `notebooks/04_sql_eval.md`: executes the candidates in Databricks and counts guard errors and Spark errors (SQL error rate).

## Next steps
1. Check the values of the SQL candidates against a reference (docs/11, next steps). Spark acceptance is not correctness.
2. Wire the generated SQL into the graph, with the guard in front of every run.
3. Routing: no further keyword changes until a new test set is available (docs/11).