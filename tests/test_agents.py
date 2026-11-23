"""Tests for the agent: SQL guard, router, KPI catalog, forecast tool and graph wiring.

No Databricks and no model needed. The graph test is skipped if langgraph is not installed.
"""
import pytest

from modules.agents.guard import UnsafeSQL, check_read_only
from modules.agents.router import MAX_TOOL_CALLS, route
from modules.agents.tools import KPI_SQL, forecast_tool, kpi_tool, sql_tool


def fake_run(sql):
    return [{"sql": sql}]


# --- SQL guard -------------------------------------------------------------

def test_guard_allows_gold_select():
    sql = "SELECT SUM(units_sold) FROM workspace.default.gold_fact_sales"
    assert check_read_only(sql) == sql


def test_guard_allows_trailing_semicolon():
    sql = "SELECT SUM(units_sold) FROM workspace.default.gold_fact_sales;"
    assert check_read_only(sql) == "SELECT SUM(units_sold) FROM workspace.default.gold_fact_sales"


@pytest.mark.parametrize("bad", [
    "DELETE FROM workspace.default.gold_fact_sales",
    "SELECT 1; DROP TABLE workspace.default.gold_fact_sales",
    "SELECT * FROM workspace.default.bronze_sales_raw",
    "SELECT * FROM gold_fact_sales",
    "WITH x AS (SELECT 1) SELECT * FROM x",
    "SELECT 1",
    "SELECT * FROM workspace.default.gold_fact_sales f UPDATE x",
])
def test_guard_rejects(bad):
    with pytest.raises(UnsafeSQL):
        check_read_only(bad)


def test_sql_tool_uses_guard():
    with pytest.raises(UnsafeSQL):
        sql_tool("SELECT 1", fake_run)


# --- Router ----------------------------------------------------------------

def test_router_kpi():
    assert route("What was the revenue in 2024?") == ["kpi"]


def test_router_forecast():
    assert route("What is the demand over the next 3 months?") == ["forecast"]


def test_router_policy_only():
    assert route("Which policy applies to discounts?") == ["rag"]


def test_router_mixed_question():
    assert set(route("Show the revenue and the return policy")) == {"kpi", "rag"}


def test_router_fallback_to_policy_search():
    assert route("hello") == ["rag"]


def test_router_respects_call_cap():
    tools = route("forecast revenue units policy returns warranty delivery")
    assert len(tools) <= MAX_TOOL_CALLS


# --- KPI tool --------------------------------------------------------------

def test_kpi_rejects_unknown_name():
    with pytest.raises(ValueError):
        kpi_tool("profit", 2024, fake_run)


def test_kpi_rejects_year_out_of_range():
    with pytest.raises(ValueError):
        kpi_tool("revenue", 2030, fake_run)


def test_every_kpi_sql_passes_the_guard_and_uses_the_year():
    for name, build in KPI_SQL.items():
        sql = build(2024)
        check_read_only(sql)
        assert "d.year = " in sql, name


def test_kpi_tool_runs_catalog_sql():
    rows = kpi_tool("revenue", 2024, fake_run)
    assert "SUM(f.revenue)" in rows[0]["sql"]


# --- Forecast tool ---------------------------------------------------------

def test_forecast_total_reads_forecast_table():
    rows = forecast_tool(fake_run)
    assert "workspace.platform.gold_forecast_weekly" in rows[0]["sql"]


def test_forecast_rejects_injection():
    with pytest.raises(ValueError):
        forecast_tool(fake_run, dealer_key="1' OR '1'='1")


def test_forecast_series_query_uses_key():
    rows = forecast_tool(fake_run, dealer_key="D001")
    assert "dealer_key = 'D001'" in rows[0]["sql"]


# --- Graph -----------------------------------------------------------------

def test_graph_calls_each_routed_tool_once():
    pytest.importorskip("langgraph")
    from modules.agents.graph import build_graph

    calls = []

    def make(name):
        def tool(question):
            calls.append(name)
            return name
        return tool

    tools = {name: make(name) for name in ["forecast", "kpi", "rag"]}
    graph = build_graph(tools)
    out = graph.invoke({"question": "Show the revenue and the return policy",
                        "pending": [], "results": {}, "calls": 0})
    assert calls == ["kpi", "rag"]
    assert out["calls"] == 2