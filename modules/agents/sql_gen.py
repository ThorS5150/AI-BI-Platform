"""SQL generation for sql_tool: question -> one read-only SELECT on the Gold tables.

The model's answer is cleaned here, then checked by modules/agents/guard.py before it
runs. A statement that fails the guard is never executed.
"""
import re

from modules.agents.router import POLICY_WORDS

SYSTEM_PROMPT = """You write one Spark SQL SELECT statement that answers a question about
car sales data. Use only these tables and columns:

- workspace.default.gold_fact_sales AS f: date_key, dealer_key, model_key, units_sold,
  base_price, discount, final_price, revenue, inventory_available, online_leads,
  test_drives_booked, promotion_type. One row per dealer, model and day.
- workspace.default.gold_dim_date AS d: date_key, date, year, month, week_of_year,
  day_of_week, is_weekend. Join with f.date_key = d.date_key.
- workspace.default.gold_dim_dealer: dealer_key, dealer_id, location_key.
- workspace.platform.gold_dim_location: location_key, city, region.
- workspace.default.gold_dim_model: model_key, model, brand, vehicle_category, fuel_type,
  transmission. Model attributes (model, brand, vehicle_category, fuel_type, transmission)
  are in gold_dim_model, not in gold_fact_sales. Join: f.model_key = m.model_key.

Rules:
- Output only the SQL statement. No explanation, no markdown.
- One SELECT statement. No WITH, no semicolons in the middle, no write statements.
- Use only the columns listed above. Never invent a column or a table.
- Years are calendar years between 2020 and 2025, filtered with d.year.
- Ratios are computed from sums, never as averages of row ratios. Use NULLIF(denominator, 0).
- discount is an amount in CAD per unit: average discount = SUM(f.discount * f.units_sold) / SUM(f.units_sold).
- revenue is in CAD. units_sold is a count of units.
- Always aggregate. Never return raw rows.
- Year over year: compare with d.year - 1 in the same statement, returning one row with both totals and the difference. Never compare with the previous month.
- If the question asks for a metric that cannot be computed from the columns above (for example margin, cost or profit), output exactly: CANNOT_ANSWER
"""

FENCE = re.compile(r"```(?:sql)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
SELECT_RE = re.compile(r"\bSELECT\b", re.IGNORECASE)
CLAUSE_SPLIT = re.compile(r"\s*(?:,|;|\band\b|\bund\b|\bet\b)\s*", re.IGNORECASE)


def kpi_part(question: str) -> str:
    """Keep only the clauses without policy words, so the SQL prompt sees the KPI part.

    "revenue of 2024 and the delivery policy" -> "revenue of 2024".
    If every clause is a policy clause, the full question is returned.
    """
    clauses = [c for c in CLAUSE_SPLIT.split(question) if c.strip()]
    kept = [c for c in clauses if not POLICY_WORDS.search(c)]
    return " and ".join(kept) if kept else question


def extract_sql(text: str) -> str:
    """Return the SELECT statement from a model answer, or "" if there is none."""
    fenced = FENCE.search(text)
    body = fenced.group(1) if fenced else text
    match = SELECT_RE.search(body)
    if not match:
        return ""
    return body[match.start():].strip().rstrip(";").strip()


def generate_sql(question: str, llm) -> str:
    """Ask the model for SQL. Returns "" if the answer contains no SELECT."""
    return extract_sql(llm.chat(SYSTEM_PROMPT, question))