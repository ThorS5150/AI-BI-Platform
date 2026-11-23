"""Agent tools.

Each tool receives its runner (a function that executes SQL) or its retriever and model
as arguments. Nothing connects to Databricks at import time, so the tools can be tested
with fakes. In Databricks, pass spark_runner(spark).
"""
import re
from typing import Callable
from modules.rag.answer import answer
from .guard import check_read_only

Runner = Callable[[str], list[dict]]

FACT = "workspace.default.gold_fact_sales"
DATE = "workspace.default.gold_dim_date"
FORECAST = "workspace.platform.gold_forecast_weekly"
YEARS = range(2020, 2026)
KEY_RE = re.compile(r"^[A-Za-z0-9_\-]{1,32}$")


def spark_runner(spark) -> Runner:
    """Runner for Databricks notebooks: executes SQL on the given SparkSession."""
    def run(sql: str) -> list[dict]:
        return [row.asDict() for row in spark.sql(sql).collect()]
    return run


def sql_tool(sql: str, run: Runner) -> list[dict]:
    """Run a read-only SELECT on the allowlisted Gold tables."""
    return run(check_read_only(sql))


def rag_tool(question: str, retriever, llm):
    """Answer a policy question from the retrieved passages (modules/rag).""" 
    return answer(question, retriever, llm)


def _base(year: int) -> str:
    return f"FROM {FACT} f JOIN {DATE} d ON f.date_key = d.date_key WHERE d.year = {year}"


# KPI catalog from docs/07. Only these names are accepted. Filter: calendar year only.
# days_of_inventory: AVG(inventory) / AVG(units) per row equals SUM(inventory) / SUM(units).
KPI_SQL = {
    "revenue": lambda y: f"SELECT SUM(f.revenue) AS value {_base(y)}",
    "units_sold": lambda y: f"SELECT SUM(f.units_sold) AS value {_base(y)}",
    "avg_revenue_per_unit": lambda y: (
        f"SELECT SUM(f.revenue) / NULLIF(SUM(f.units_sold), 0) AS value {_base(y)}"
    ),
    "revenue_prior_year": lambda y: f"SELECT SUM(f.revenue) AS value {_base(y - 1)}",
    "revenue_growth_yoy": lambda y: (
        f"SELECT (SELECT SUM(f.revenue) {_base(y)}) / "
        f"NULLIF((SELECT SUM(f.revenue) {_base(y - 1)}), 0) - 1 AS value"
    ),
    "avg_discount_per_unit": lambda y: (
        f"SELECT SUM(f.discount * f.units_sold) / NULLIF(SUM(f.units_sold), 0) AS value {_base(y)}"
    ),
    "lead_to_test_drive_rate": lambda y: (
        f"SELECT SUM(f.test_drives_booked) / NULLIF(SUM(f.online_leads), 0) AS value {_base(y)}"
    ),
    "days_of_inventory": lambda y: (
        f"SELECT SUM(f.inventory_available) / NULLIF(SUM(f.units_sold), 0) AS value {_base(y)}"
    ),
    "zero_sales_share": lambda y: (
        f"SELECT SUM(CASE WHEN f.units_sold = 0 THEN 1 ELSE 0 END) / COUNT(*) AS value {_base(y)}"
    ),
}


def kpi_tool(name: str, year: int, run: Runner) -> list[dict]:
    """Return one KPI value for one calendar year. Unknown KPI names are rejected."""
    if name not in KPI_SQL:
        raise ValueError(f"Unknown KPI: {name}. Allowed: {sorted(KPI_SQL)}")
    if int(year) not in YEARS:
        raise ValueError(f"Year out of range: {year}")
    return run(check_read_only(KPI_SQL[name](int(year))))


def forecast_tool(run: Runner, dealer_key=None, model_key=None) -> list[dict]:
    """Read the batch forecast.

    With a dealer or model key: weekly rows for that series (rounded units).
    Without keys: weekly totals (sum of expected units, docs/10).
    """
    conditions = []
    for column, value in (("dealer_key", dealer_key), ("model_key", model_key)):
        if value is not None:
            if not KEY_RE.match(str(value)):
                raise ValueError(f"Invalid {column}: {value!r}")
            conditions.append(f"{column} = '{value}'")
    if conditions:
        sql = (
            f"SELECT week_start, dealer_key, model_key, forecast_units_rounded "
            f"FROM {FORECAST} WHERE {' AND '.join(conditions)} ORDER BY week_start"
        )
    else:
        sql = (
            f"SELECT week_start, ROUND(SUM(forecast_units)) AS forecast_units "
            f"FROM {FORECAST} GROUP BY week_start ORDER BY week_start"
        )
    return run(check_read_only(sql))