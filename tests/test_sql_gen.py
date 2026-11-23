"""Tests for SQL extraction and generation with a fake LLM. No model needed."""
import pytest

from modules.agents.guard import UnsafeSQL, check_read_only
from modules.agents.sql_gen import SYSTEM_PROMPT, extract_sql, generate_sql, kpi_part

REVENUE_2024 = (
    "SELECT SUM(f.revenue) AS value FROM workspace.default.gold_fact_sales f "
    "JOIN workspace.default.gold_dim_date d ON f.date_key = d.date_key WHERE d.year = 2024"
)


class FakeLLM:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def chat(self, system, user):
        self.calls.append((system, user))
        return self.reply


def test_extract_plain_sql_strips_semicolon():
    assert extract_sql("SELECT 1 FROM workspace.default.gold_fact_sales;") == \
        "SELECT 1 FROM workspace.default.gold_fact_sales"


def test_extract_strips_code_fence():
    text = "```sql\n" + REVENUE_2024 + "\n```"
    assert extract_sql(text) == REVENUE_2024


def test_extract_skips_preamble():
    text = "Here is the query:\n" + REVENUE_2024
    assert extract_sql(text) == REVENUE_2024


def test_extract_returns_empty_without_select():
    assert extract_sql("I cannot answer that.") == ""


def test_generate_sql_sends_schema_prompt_and_question():
    llm = FakeLLM(REVENUE_2024)
    sql = generate_sql("What was the revenue in 2024?", llm)
    system, user = llm.calls[0]
    assert "workspace.default.gold_fact_sales" in system
    assert system == SYSTEM_PROMPT
    assert user == "What was the revenue in 2024?"
    assert check_read_only(sql) == REVENUE_2024


def test_write_statement_from_model_is_rejected_by_guard():
    sql = generate_sql("Delete all sales", FakeLLM("DROP TABLE workspace.default.gold_fact_sales"))
    assert sql == ""
    with pytest.raises(UnsafeSQL):
        check_read_only(sql)


@pytest.mark.parametrize("question, expected", [
    ("revenue of 2024 and the delivery policy", "revenue of 2024"),
    ("units sold in 2022 and the warranty cover", "units sold in 2022"),
    ("What was the revenue in 2024?", "What was the revenue in 2024?"),
    ("What is the return policy and the financing rules?", "What is the return policy and the financing rules?"),
])
def test_kpi_part_drops_policy_clauses(question, expected):
    assert kpi_part(question) == expected


def test_system_prompt_has_model_join_and_column_rule():
    assert "f.model_key = m.model_key" in SYSTEM_PROMPT
    assert "Never invent a column" in SYSTEM_PROMPT