from time import perf_counter

from app.agents.state import MonitorState
from app.tools.risk_calculator import calculate_risk


def score_risk(state: MonitorState) -> dict:
    started = perf_counter()

    analysis = state.get("analysis")
    if not analysis:
        raise ValueError("analysis is required before scoring risk")

    patterns = state.get("patterns") or []
    risk = calculate_risk(analysis=analysis, patterns=patterns)

    duration_ms = (perf_counter() - started) * 1000
    trace = list(state.get("agent_trace", []))
    trace.append(
        {
            "agent": "risk_scorer",
            "duration_ms": round(duration_ms, 3),
            "status": "complete",
            "risk_level": risk["risk_level"],
            "score": risk["composite_score"],
        }
    )

    return {"risk": risk, "agent_trace": trace, "error": None}
