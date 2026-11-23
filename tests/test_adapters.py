"""Tests for the question adapters and the tool wiring used by the graph.

No Databricks and no model needed. The RAG and graph tests need the RAG dependencies
(sentence-transformers) and langgraph; they are skipped if langgraph is missing.
"""
import pytest

from modules.agents.adapters import DEFAULT_YEAR, kpi_from_question, make_tools


def fake_run(sql):
    return [{"sql": sql}]


class EmptyRetriever:
    def search(self, question, **kwargs):
        return []


class UnusedLLM:
    def chat(self, system, user):
        raise AssertionError("LLM must not be called without retrieved passages")


@pytest.mark.parametrize("question, expected", [
    ("What was the revenue in 2024?", ("revenue", 2024)),
    ("How many units were sold in 2022?", ("units_sold", 2022)),
    ("What is the average discount per unit in 2023?", ("avg_discount_per_unit", 2023)),
    ("What was the revenue growth compared to the prior year?", ("revenue_growth_yoy", DEFAULT_YEAR)),
    ("What share of rows had zero sales?", ("zero_sales_share", DEFAULT_YEAR)),
    ("What is the lead to test drive rate in 2021?", ("lead_to_test_drive_rate", 2021)),
    ("How many days of inventory do we have?", ("days_of_inventory", DEFAULT_YEAR)),
    ("What is the average revenue per unit in 2020?", ("avg_revenue_per_unit", 2020)),
])
def test_kpi_from_question(question, expected):
    assert kpi_from_question(question) == expected


def test_no_kpi_in_question_raises():
    with pytest.raises(ValueError):
        kpi_from_question("hello there")


def test_make_tools_kpi_runs_catalog_sql_for_the_year():
    tools = make_tools(fake_run, EmptyRetriever(), UnusedLLM())
    rows = tools["kpi"]("What was the revenue in 2022?")
    assert "d.year = 2022" in rows[0]["sql"]


def test_make_tools_forecast_reads_forecast_table():
    tools = make_tools(fake_run, EmptyRetriever(), UnusedLLM())
    rows = tools["forecast"]("What is the demand forecast?")
    assert "gold_forecast_weekly" in rows[0]["sql"]


def test_make_tools_rag_without_hits_returns_fallback():
    tools = make_tools(fake_run, EmptyRetriever(), UnusedLLM())
    out = tools["rag"]("What is the return policy?")
    assert out.found is False


def test_graph_end_to_end_with_fakes():
    pytest.importorskip("langgraph")
    from modules.agents.graph import build_graph

    graph = build_graph(make_tools(fake_run, EmptyRetriever(), UnusedLLM()))
    out = graph.invoke({"question": "Show the revenue and the return policy in 2023",
                        "pending": [], "results": {}, "calls": 0})
    assert set(out["results"]) == {"kpi", "rag"}
    assert "d.year = 2023" in out["results"]["kpi"][0]["sql"]