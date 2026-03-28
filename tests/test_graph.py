from app.agents.graph import build_fraud_monitor_graph, should_escalate


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
