import time

from fastapi.testclient import TestClient

from app.config import get_settings
from app.agents.graph import build_fraud_monitor_graph, should_escalate
from app.main import app
from app.rate_limit import rate_limiter


def _state(txn):
    return {
        "messages": [],
        "transaction": txn,
        "analysis": None,
        "patterns": None,
        "risk": None,
        "report": None,
        "agent_trace": [],
        "error": None,
        "langsmith_trace_url": None,
    }


def test_should_escalate_routing_logic():
    assert should_escalate({"risk": {"risk_level": "LOW"}}) == "end"
    assert should_escalate({"risk": {"risk_level": "MEDIUM"}}) == "generate_report"
    assert should_escalate({"risk": {"risk_level": "HIGH"}}) == "generate_report"


def test_graph_compiles_and_runs_high_risk(sample_transactions):
    graph = build_fraud_monitor_graph()
    result = graph.invoke(_state(sample_transactions[0]))

    assert result["analysis"] is not None
    assert result["patterns"] is not None
    assert result["risk"] is not None
    assert result["risk"]["risk_level"] in {"MEDIUM", "HIGH", "CRITICAL"}
    assert result.get("report")
    assert len(result.get("agent_trace", [])) >= 4


def test_graph_low_risk_skips_report(sample_transactions):
    graph = build_fraud_monitor_graph()
    result = graph.invoke(_state(sample_transactions[1]))

    assert result["risk"]["risk_level"] == "LOW"
    assert result.get("report") in {None, ""}
    assert len(result.get("agent_trace", [])) == 3


def test_monitor_endpoint_runs_pipeline(client, sample_transactions):
    response = client.post("/monitor", json={"transaction": sample_transactions[0]})

    assert response.status_code == 200
    payload = response.json()
    assert payload["transaction_id"] == sample_transactions[0]["transaction_id"]
    assert payload["risk"]["risk_level"] in {"MEDIUM", "HIGH", "CRITICAL"}
    assert len(payload["agent_trace"]) >= 4


def test_agent_invoke_endpoint_for_single_agent(client, sample_transactions):
    response = client.post(
        "/agents/transaction_analyzer/invoke",
        json={"transaction": sample_transactions[0]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["agent"] == "transaction_analyzer"
    assert payload["state"]["analysis"] is not None


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["graph_compiled"] is True


def test_monitor_endpoint_enforces_timeout(client, sample_transactions):
    class SlowGraph:
        def invoke(self, state):
            time.sleep(0.05)
            return state

    original_graph = client.app.state.fraud_monitor_graph
    original_timeout = client.app.state.agent_timeout_seconds
    client.app.state.fraud_monitor_graph = SlowGraph()
    client.app.state.agent_timeout_seconds = 0.01

    try:
        response = client.post("/monitor", json={"transaction": sample_transactions[0]})
    finally:
        client.app.state.fraud_monitor_graph = original_graph
        client.app.state.agent_timeout_seconds = original_timeout

    assert response.status_code == 408
    assert response.json()["detail"] == "Agent timeout exceeded"


def test_agent_invoke_hides_internal_errors(client, sample_transactions):
    from app import routers

    original_handler = routers.agents._AGENT_FN["transaction_analyzer"]

    def broken_handler(state):
        raise RuntimeError("internal explosion")

    routers.agents._AGENT_FN["transaction_analyzer"] = broken_handler
    try:
        response = client.post(
            "/agents/transaction_analyzer/invoke",
            json={"transaction": sample_transactions[0]},
        )
    finally:
        routers.agents._AGENT_FN["transaction_analyzer"] = original_handler

    assert response.status_code == 500
    assert response.json()["detail"] == "Agent invocation failed."


def test_monitor_requires_api_key_when_configured(monkeypatch, sample_transactions):
    monkeypatch.setenv("API_KEY", "test-api-key")
    get_settings.cache_clear()
    rate_limiter.clear()

    try:
        with TestClient(app) as client:
            unauthorized = client.post("/monitor", json={"transaction": sample_transactions[0]})
            authorized = client.post(
                "/monitor",
                json={"transaction": sample_transactions[0]},
                headers={"X-API-Key": "test-api-key"},
            )
    finally:
        rate_limiter.clear()
        get_settings.cache_clear()

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


def test_monitor_rate_limit_returns_429(monkeypatch, sample_transactions):
    monkeypatch.setenv("API_KEY", "test-api-key")
    monkeypatch.setenv("RATE_LIMIT_MONITOR_PER_MINUTE", "1")
    get_settings.cache_clear()
    rate_limiter.clear()

    try:
        with TestClient(app) as client:
            headers = {
                "X-API-Key": "test-api-key",
                "X-Forwarded-For": "203.0.113.25",
            }
            first = client.post("/monitor", json={"transaction": sample_transactions[0]}, headers=headers)
            second = client.post("/monitor", json={"transaction": sample_transactions[0]}, headers=headers)
    finally:
        rate_limiter.clear()
        get_settings.cache_clear()

    assert first.status_code == 200
    assert second.status_code == 429
