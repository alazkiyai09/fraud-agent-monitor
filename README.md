# Fraud Agent Monitor

Multi-agent fraud monitoring system using LangGraph + LangSmith + FastAPI + Streamlit.

## Live Demo (Deployment Placeholder)

- API base URL: `https://fraud-monitor-api-xxxxx-as.a.run.app`
- API docs: `https://fraud-monitor-api-xxxxx-as.a.run.app/docs`
- Streamlit dashboard: `https://fraud-monitor.streamlit.app`
- Status: `pending deployment`

## Agent Pipeline

1. Transaction Analyzer
2. Pattern Detector
3. Risk Scorer
4. Report Generator

## API Endpoints

- `POST /monitor`
- `POST /agents/{name}/invoke`
- `GET /health`

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

## Dashboard

```bash
streamlit run dashboard/app.py
```

## Docker Compose

```bash
docker compose up --build
```

## Tests

```bash
pytest --cov=app --cov-report=term-missing -v
```

Update live links above once deployed.
