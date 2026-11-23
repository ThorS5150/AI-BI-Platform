"""Rule-based router (keyword version 2).

Deterministic on purpose: routing accuracy can be measured on a test set
(docs/11). An LLM router can replace this function later without changing the tools.

Rules:
- Forecast words route to forecast.
- Specific KPI words always route to kpi (turnover, per car, stock, growth, ...).
- Generic KPI words (units, sales, revenue, sold, ventes, ...) route to kpi only if the
  question has no forecast word. Otherwise "forecast the units" would also call kpi.
- Policy words route to rag.
- A question can route to several tools. Each tool is called at most once.
- If no keyword matches, the question goes to the policy search (rag).
"""
import re

MAX_TOOL_CALLS = 4

KPI_SPECIFIC = re.compile(
    r"\b(average discount|discount per unit|average revenue|revenue per unit|per car|"
    r"turnover|stock|inventory|test.?drives?|lead|zero.?sales|no sales|growth|"
    r"year[- ]over[- ]year|prior year|previous year)\b",
    re.IGNORECASE,
)
KPI_GENERIC = re.compile(
    r"\b(revenue|units?|sold|sell\w*|sales|vendu\w*|ventes?|chiffre)\b",
    re.IGNORECASE,
)
FORECAST_WORDS = re.compile(
    r"\b(forecast\w*|predict\w*|prognos\w*|prévision\w*|prévoi\w*|demand|demande|"
    r"expect\w*|project\w*|outlook|next (\d+ )?(weeks?|months?|quarters?))\b",
    re.IGNORECASE,
)
POLICY_WORDS = re.compile(
    r"\b(policy|policies|return|returns|warranty|financing|delivery|rules?|"
    r"politique|garantie|retour|financement|livraison)\b",
    re.IGNORECASE,
)


def route(question: str) -> list[str]:
    """Return the tools for a question, in call order, at most MAX_TOOL_CALLS."""
    is_forecast = bool(FORECAST_WORDS.search(question))
    tools = []
    if is_forecast:
        tools.append("forecast")
    if KPI_SPECIFIC.search(question) or (KPI_GENERIC.search(question) and not is_forecast):
        tools.append("kpi")
    if POLICY_WORDS.search(question):
        tools.append("rag")
    return tools[:MAX_TOOL_CALLS] or ["rag"]