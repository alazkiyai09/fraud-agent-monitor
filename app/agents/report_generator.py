from time import perf_counter

from app.agents.state import MonitorState
from app.tools.sar_template import build_sar_report


def generate_report(state: MonitorState) -> dict:
    started = perf_counter()

    transaction = state.get("transaction")
    analysis = state.get("analysis")
    patterns = state.get("patterns") or []
    risk = state.get("risk")

    if not transaction or not analysis or not risk:
        raise ValueError("transaction, analysis, and risk are required for report generation")

    report = build_sar_report(transaction=transaction, analysis=analysis, patterns=patterns, risk=risk)

    duration_ms = (perf_counter() - started) * 1000
    trace = list(state.get("agent_trace", []))
    trace.append(
        {
            "agent": "report_generator",
            "duration_ms": round(duration_ms, 3),
            "status": "complete",
            "report_generated": True,
        }
    )

    return {"report": report, "agent_trace": trace, "error": None}
