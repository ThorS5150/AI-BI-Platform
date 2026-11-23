"""Adapters: turn a question into tool arguments, and wire the tools for the graph.

v1 limits:
- The KPI name comes from keywords; the year from the question, or DEFAULT_YEAR.
- forecast_tool returns company-wide weekly totals. Series-level keys are not parsed yet.
- Every keyword the router sends to kpi must have a KPI pattern here, otherwise
  kpi_from_question raises ValueError.
"""
import re

from .tools import forecast_tool, kpi_tool, rag_tool

DEFAULT_YEAR = 2025

YEAR_RE = re.compile(r"\b(20[2][0-5])\b")

# Most specific patterns first. The first match wins.
KPI_PATTERNS = [
    (re.compile(r"growth|year[- ]over[- ]year|yoy", re.IGNORECASE), "revenue_growth_yoy"),
    (re.compile(r"prior year|previous year", re.IGNORECASE), "revenue_prior_year"),
    (re.compile(r"average revenue|revenue per (unit|car)|per car|average price", re.IGNORECASE),
     "avg_revenue_per_unit"),
    (re.compile(r"average discount|discount per unit", re.IGNORECASE), "avg_discount_per_unit"),
    (re.compile(r"test.?drive|lead", re.IGNORECASE), "lead_to_test_drive_rate"),
    (re.compile(r"inventory|stock", re.IGNORECASE), "days_of_inventory"),
    (re.compile(r"zero.?sales|no sales", re.IGNORECASE), "zero_sales_share"),
    (re.compile(r"\bunits?\b|sold|\bsell\w*|vendu\w*", re.IGNORECASE), "units_sold"),
    (re.compile(r"revenue|sales|turnover|chiffre|ventes?", re.IGNORECASE), "revenue"),
]


def kpi_from_question(question: str) -> tuple[str, int]:
    """Return (KPI name, year) for a question. Raises ValueError if no KPI matches."""
    name = next((kpi for pattern, kpi in KPI_PATTERNS if pattern.search(question)), None)
    if name is None:
        raise ValueError("No KPI found in question.")
    match = YEAR_RE.search(question)
    year = int(match.group(1)) if match else DEFAULT_YEAR
    return name, year


def make_tools(run, retriever, llm) -> dict:
    """Tools for the graph. Each takes the question and returns its result."""

    def kpi(question: str):
        name, year = kpi_from_question(question)
        return kpi_tool(name, year, run)

    def forecast(question: str):
        return forecast_tool(run)

    def rag(question: str):
        return rag_tool(question, retriever, llm)

    return {"kpi": kpi, "forecast": forecast, "rag": rag}