from app.agents.pattern_detector import detect_patterns
from app.agents.report_generator import generate_report
from app.agents.risk_scorer import score_risk
from app.agents.transaction_analyzer import analyze_transaction


def _base_state(sample_transaction: dict) -> dict:
    return {
        "messages": [],
        "transaction": sample_transaction,
        "analysis": None,
        "patterns": None,
        "risk": None,
        "report": None,
        "agent_trace": [],
        "error": None,
        "langsmith_trace_url": None,
    }


def test_transaction_analyzer_detects_expected_anomalies(sample_transactions):
    state = _base_state(sample_transactions[0])
    updates = analyze_transaction(state)

    analysis = updates["analysis"]
    assert "amount_near_threshold" in analysis["anomalies_detected"]
    assert analysis["velocity_score"] >= 0.0


def test_pattern_detector_matches_known_typologies(sample_transactions):
    state = _base_state(sample_transactions[0])
    state.update(analyze_transaction(state))

    updates = detect_patterns(state)
    assert isinstance(updates["patterns"], list)
    assert len(updates["patterns"]) >= 1


def test_risk_scorer_produces_risk_assessment(sample_transactions):
    state = _base_state(sample_transactions[0])
    state.update(analyze_transaction(state))
    state.update(detect_patterns(state))

    updates = score_risk(state)
    assert updates["risk"]["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_report_generator_outputs_markdown(sample_transactions):
    state = _base_state(sample_transactions[0])
    state.update(analyze_transaction(state))
    state.update(detect_patterns(state))
    state.update(score_risk(state))

    updates = generate_report(state)
    assert "## Suspicious Activity Report" in updates["report"]
