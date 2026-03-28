from app.tools.pattern_database import match_patterns
from app.tools.risk_calculator import calculate_risk
from app.tools.sar_template import build_sar_report
from app.tools.transaction_lookup import lookup_transaction_context


def test_transaction_lookup_returns_context_fields():
    context = lookup_transaction_context("ACC-001-SENDER", "ACC-999-RECEIVER", "Jakarta")
    assert context["receiver_account_age_days"] == 7
    assert context["sender_txn_count_24h"] >= 1


def test_pattern_database_matches_anomaly_overlap():
    analysis = {"anomalies_detected": ["amount_near_threshold", "velocity_spike"]}
    matches = match_patterns(analysis=analysis, patterns_path="data/fraud_patterns.json")
    assert matches
    assert matches[0]["typology"] in {"smurfing", "mule_account", "bust_out"}


def test_risk_calculator_outputs_valid_levels_and_action():
    risk = calculate_risk(
        analysis={"anomalies_detected": ["a", "b", "c"], "velocity_score": 0.8, "amount_deviation": 2.0},
        patterns=[{"confidence": 0.9}],
    )
    assert 0.0 <= risk["composite_score"] <= 1.0
    assert risk["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert risk["recommended_action"] in {"APPROVE", "REVIEW", "ESCALATE", "BLOCK"}


def test_sar_template_contains_required_sections():
    report = build_sar_report(
        transaction={
            "transaction_id": "TXN-1",
            "amount": 1000,
            "sender_account": "A",
            "receiver_account": "B",
            "timestamp": "2026-01-01T10:00:00Z",
            "channel": "online",
            "location": "Jakarta",
        },
        analysis={"anomalies_detected": ["velocity_spike"]},
        patterns=[{"pattern_name": "Structuring", "typology": "smurfing", "confidence": 0.7, "evidence": ["x"]}],
        risk={
            "composite_score": 0.7,
            "risk_level": "HIGH",
            "recommended_action": "ESCALATE",
            "risk_factors": [{"factor": "velocity_score", "weight": 0.2, "value": 0.8}],
        },
    )

    assert "## Suspicious Activity Report" in report
    assert "### Transaction Summary" in report
    assert "### Risk Assessment" in report
