# 01 Project Description

## Problem
Sales managers and dealers need answers to questions such as "Why did revenue drop in Q3?" or "Which policy applies to discounts?". The data is stored in tables, the policies in documents. Today both are queried separately.

## Target users
- Sales management (dashboards, forecasts)
- Business units (questions in natural language)

## Questions the platform should answer
1. How do revenue and units sold develop by region and product group?
2. What is the demand over the next 3 months?
3. What do internal policies say about a case?
4. Which combination of data and documents answers a mixed question?

## Success criteria
- The pipeline runs reproducibly from raw data to Gold tables.
- The RAG hit rate is documented on a test set of 25 questions.
- For test questions, the agent selects the correct tool in at least 80 % of cases (target value, checked in phase 4).
- Governance artifacts according to ISO/IEC 42001 exist and are linked.

## Non-goals
See [03_scope_und_grenzen.md](03_scope_und_grenzen.md).