from datetime import datetime
from time import perf_counter

from app.agents.state import MonitorState
from app.tools.transaction_lookup import lookup_transaction_context

REPORTING_THRESHOLD = 50000.0


def _is_unusual_time(timestamp: str) -> bool:
    value = timestamp.replace("Z", "+00:00")
    hour = datetime.fromisoformat(value).hour
    return hour < 8 or hour >= 20


def analyze_transaction(state: MonitorState) -> dict:
    started = perf_counter()
    transaction = state["transaction"]

    context = lookup_transaction_context(
        sender_account=transaction["sender_account"],
        receiver_account=transaction["receiver_account"],
        location=transaction["location"],
    )

    amount = float(transaction["amount"])
    avg_amount = max(1.0, float(context["sender_avg_amount"]))

    amount_deviation = abs(amount - avg_amount) / avg_amount
    velocity_multiplier = float(context["sender_txn_count_24h"]) / max(1.0, float(context["sender_avg_frequency_24h"]))
    velocity_score = max(0.0, min(1.0, velocity_multiplier / 5.0))

    anomalies: list[str] = []
    if amount < REPORTING_THRESHOLD and amount >= REPORTING_THRESHOLD * 0.95:
        anomalies.append("amount_near_threshold")
    if float(context["receiver_account_age_days"]) < 30:
        anomalies.append("new_receiver")
    if _is_unusual_time(transaction["timestamp"]):
        anomalies.append("unusual_timing")
    if velocity_multiplier > 3.0:
        anomalies.append("velocity_spike")
    if transaction["location"] != context["registration_location"]:
        anomalies.append("geographic_mismatch")

    analysis = {
        "features_extracted": {
            "velocity_multiplier": round(velocity_multiplier, 4),
            "amount_percent_of_threshold": round(amount / REPORTING_THRESHOLD, 4),
            "receiver_account_age_days": context["receiver_account_age_days"],
            "amount": amount,
        },
        "anomalies_detected": anomalies,
        "velocity_score": round(velocity_score, 4),
        "amount_deviation": round(amount_deviation, 4),
    }

    duration_ms = (perf_counter() - started) * 1000
    trace = list(state.get("agent_trace", []))
    trace.append(
        {
            "agent": "transaction_analyzer",
            "duration_ms": round(duration_ms, 3),
            "status": "complete",
            "anomalies": len(anomalies),
        }
    )

    return {"analysis": analysis, "agent_trace": trace, "error": None}
