"""Read-only SQL guard for the agent's sql_tool.

Rules:
- Exactly one SELECT statement (an optional trailing semicolon is allowed).
- No CTEs (WITH), no write or DDL keywords.
- Every table after FROM or JOIN must be on the allowlist below.

Known limit: comma joins (FROM a, b) are not parsed. Only allowlisted tables
are reachable through this guard, so a comma join to another table is blocked
only if that table is not on the list. Keep the allowlist minimal.
"""
import re

ALLOWED_TABLES = frozenset({
    "workspace.platform.gold_fact_sales",
    "workspace.platform.gold_weekly_sales",
    "workspace.platform.gold_dim_date",
    "workspace.platform.gold_dim_dealer",
    "workspace.platform.gold_dim_location",
    "workspace.platform.gold_dim_model",
    "workspace.platform.gold_forecast_weekly",
})

FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|MERGE|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|"
    r"REPLACE|OVERWRITE|COPY|CALL|EXECUTE)\b",
    re.IGNORECASE,
)
TABLE_REF = re.compile(r"\b(?:FROM|JOIN)\s+([A-Za-z0-9_.`]+)", re.IGNORECASE)


class UnsafeSQL(ValueError):
    """Raised when a statement does not pass the read-only guard."""


def check_read_only(sql: str) -> str:
    """Return the cleaned statement if it passes all rules, otherwise raise UnsafeSQL."""
    text = sql.strip()
    if text.endswith(";"):
        text = text[:-1].rstrip()
    if ";" in text:
        raise UnsafeSQL("Only one statement is allowed.")
    if not re.match(r"^SELECT\b", text, re.IGNORECASE):
        raise UnsafeSQL("Only SELECT statements are allowed (CTEs are not supported).")
    if FORBIDDEN.search(text):
        raise UnsafeSQL("Write or DDL keyword found.")
    tables = [t.strip("`") for t in TABLE_REF.findall(text)]
    if not tables:
        raise UnsafeSQL("No table found after FROM or JOIN.")
    for table in tables:
        if table not in ALLOWED_TABLES:
            raise UnsafeSQL(f"Table not allowed: {table}")
    return text