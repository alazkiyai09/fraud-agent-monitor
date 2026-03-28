def build_sar_report(transaction: dict, analysis: dict, patterns: list[dict], risk: dict) -> str:
    pattern_lines = []
    for pattern in patterns:
        evidence = ", ".join(pattern.get("evidence", []))
        pattern_lines.append(
            f"- {pattern.get('pattern_name')} ({pattern.get('typology')}), confidence={pattern.get('confidence')}: {evidence}"
        )

    if not pattern_lines:
        pattern_lines.append("- No typology matches exceeded confidence threshold")
    pattern_block = "\n".join(pattern_lines)

    anomaly_lines = "\n".join(f"- {item}" for item in analysis.get("anomalies_detected", [])) or "- None"
    factor_lines = "\n".join(
        f"- {item.get('factor')}: value={item.get('value')} (weight={item.get('weight')})"
        for item in risk.get("risk_factors", [])
    ) or "- None"

    return (
        "## Suspicious Activity Report\n\n"
        "### Transaction Summary\n"
        f"- ID: {transaction.get('transaction_id')}\n"
        f"- Amount: {transaction.get('amount')}\n"
        f"- Sender: {transaction.get('sender_account')}\n"
        f"- Receiver: {transaction.get('receiver_account')}\n"
        f"- Timestamp: {transaction.get('timestamp')}\n"
        f"- Channel: {transaction.get('channel')}\n"
        f"- Location: {transaction.get('location')}\n\n"
        "### Analysis Findings\n"
        f"{anomaly_lines}\n\n"
        "### Pattern Matches\n"
        f"{pattern_block}\n\n"
        "### Risk Assessment\n"
        f"- Composite score: {risk.get('composite_score')}\n"
        f"- Risk level: {risk.get('risk_level')}\n"
        f"- Recommended action: {risk.get('recommended_action')}\n"
        f"{factor_lines}\n\n"
        "### Recommended Actions\n"
        f"- Immediate: {risk.get('recommended_action')}\n"
        "- Investigation: validate account ownership, counterparty legitimacy, and transaction purpose\n"
        "- Compliance: file regulatory report if required by jurisdiction\n"
    )
