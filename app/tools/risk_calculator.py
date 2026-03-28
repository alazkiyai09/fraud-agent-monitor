def calculate_risk(analysis: dict, patterns: list[dict]) -> dict:
    anomalies = analysis.get("anomalies_detected", []) if analysis else []
    anomaly_score = min(1.0, len(anomalies) / 5.0)
    velocity_score = float((analysis or {}).get("velocity_score", 0.0))
    amount_deviation = float((analysis or {}).get("amount_deviation", 0.0))
    amount_normalized = max(0.0, min(1.0, amount_deviation / 3.0))
    max_pattern_confidence = max((float(p.get("confidence", 0.0)) for p in patterns), default=0.0)

    anomaly_weight = 0.25
    pattern_weight = 0.35
    velocity_weight = 0.20
    amount_weight = 0.20

    composite_score = (
        anomaly_weight * anomaly_score
        + pattern_weight * max_pattern_confidence
        + velocity_weight * velocity_score
        + amount_weight * amount_normalized
    )

    composite_score = max(0.0, min(1.0, composite_score))

    if composite_score < 0.25:
        risk_level = "LOW"
        recommended_action = "APPROVE"
    elif composite_score < 0.50:
        risk_level = "MEDIUM"
        recommended_action = "REVIEW"
    elif composite_score < 0.80:
        risk_level = "HIGH"
        recommended_action = "ESCALATE"
    else:
        risk_level = "CRITICAL"
        recommended_action = "BLOCK"

    risk_factors = [
        {"factor": "anomaly_score", "weight": anomaly_weight, "value": round(anomaly_score, 4)},
        {
            "factor": "max_pattern_confidence",
            "weight": pattern_weight,
            "value": round(max_pattern_confidence, 4),
        },
        {"factor": "velocity_score", "weight": velocity_weight, "value": round(velocity_score, 4)},
        {
            "factor": "amount_deviation_normalized",
            "weight": amount_weight,
            "value": round(amount_normalized, 4),
        },
    ]

    return {
        "composite_score": round(composite_score, 4),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "recommended_action": recommended_action,
    }
