# 02 Architektur

## Overview
```
Raw data (CSV, policy PDFs)
│
▼
┌─────────────────────────────┐ ┌──────────────────────────┐
│ Databricks Free Edition │ │ Local (Docker) │
│ Bronze → Silver → Gold │───────▶│ RAG (FAISS + embeddings) │
│ Delta tables, MLflow │ │ LangGraph agent │
│ Great Expectations │ │ FastAPI │
└─────────────────────────────┘ └────────────┬─────────────┘
│ │
▼ ▼
Power BI dashboards Streamlit frontend (chat, sources, tool display)
```

## Reasoning for the split
The Free Edition covers pipelines, Delta and MLflow. Vector Search and Model Serving are limited or not available. RAG and the agent therefore run locally. This is stated openly in the README.

## Decisions
- Medallion architecture for clear responsibilities per layer.
- LangGraph instead of the Mosaic AI Agent Framework, so the agent stays portable.
- FAISS instead of Vector Search, because it runs locally.
- Frontend decision:
  - **Streamlit** for the question-and-answer interface (RAG and agent). It shows answers, sources and the tool used. Quick to build, good for demo GIFs.
  - **Power BI** for dashboards on the Gold tables. Screenshots are stored in `docs/screenshots/`.
  - **FastAPI** as the interface between the frontend and the agent/RAG. This makes the frontend replaceable, e.g. by React in a later stage.

## Build order (decided 2026-11-22)
1. Wire the SQL tool into the agent graph, with the guard in front of every run (docs/13, next steps).
2. FastAPI endpoint for questions to the agent and the RAG (`api/`).
3. Streamlit page: question input, answer, sources, tool used. Calls FastAPI only.
4. Docker for the local stack (FastAPI and Streamlit).

Power BI dashboards on the Gold tables run in parallel and do not depend on the steps above.