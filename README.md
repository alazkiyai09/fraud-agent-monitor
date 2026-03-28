# Multi-Agent Fraud Monitor

LangGraph-based fraud monitoring system with 4 specialized agents:

1. Transaction Analyzer
2. Pattern Detector
3. Risk Scorer
4. Report Generator

## API Endpoints

- `POST /monitor`: run full orchestration pipeline
- `POST /agents/{name}/invoke`: invoke a single agent for debugging
- `GET /health`: service + graph health

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

## Run Dashboard

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

## Evaluation

```bash
python3 eval/evaluate_agents.py --scenarios eval/test_scenarios.json
```
