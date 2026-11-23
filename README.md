# AI Business Intelligence Platform

Platform for dealer and sales data: data pipeline (Databricks), BI dashboards, a RAG module for document questions, and a LangGraph agent that orchestrates SQL, RAG and forecasts. Governance according to ISO/IEC 42001.

## Status
Completed: Phase 0 and 1 (data pipeline with Great Expectations checks), Phase 2 (KPIs and demand forecast with LightGBM as champion model), Phase 3 (RAG with evaluation).
Next: agent (Phase 4) and governance (Phase 5).

## Architecture
See [docs/02_architektur.md](docs/02_architektur.md).

## Documents
| Phase | Document |
|---|---|
| 0 | [Project description](docs/01_projektbeschreibung.md), [Architecture](docs/02_architektur.md), [Scope](docs/03_scope_und_grenzen.md) |
| 1 | [Data source](docs/04_datenquelle.md), [Data model](docs/05_datenmodell.md), [Data quality](docs/06_datenqualitaet.md) |
| 2 | [KPI definitions](docs/07_kpi_definitionen.md), [Forecast concept](docs/10_forecast_concept.md) |
| 3 | [RAG concept](docs/08_rag_konzept.md), [RAG evaluation](docs/09_rag_evaluation.md) |
| 4 | [Agent design](docs/13_agent_design.md), [Agent evaluation](docs/11_agent_evaluation.md) |
| 5 | [AI policy](governance/01_ai_policy.md), [Risk assessment](governance/02_risikobewertung.md), [Model card](governance/03_modelldokumentation.md), [Fairness report](governance/04_fairness_bericht.md), [Monitoring plan](governance/05_monitoring_plan.md) |
| 6 | [Lessons learned](docs/12_lessons_learned.md) |

## What runs where
- **Databricks Free Edition:** ingestion, PySpark transformations, Delta tables (Bronze/Silver/Gold), MLflow tracking
- **Local:** RAG with FAISS, LangGraph agent, FastAPI, Streamlit frontend, Docker
- **Power BI:** dashboards on the Gold tables

## Getting started
To be added.