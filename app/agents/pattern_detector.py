from time import perf_counter

from app.agents.state import MonitorState
from app.config import get_settings
from app.tools.pattern_database import match_patterns


def detect_patterns(state: MonitorState) -> dict:
    started = perf_counter()
    analysis = state.get("analysis")
    if not analysis:
        raise ValueError("analysis is required before pattern detection")

    settings = get_settings()
    patterns = match_patterns(analysis=analysis, patterns_path=settings.fraud_patterns_path)

    duration_ms = (perf_counter() - started) * 1000
    trace = list(state.get("agent_trace", []))
    trace.append(
        {
            "agent": "pattern_detector",
            "duration_ms": round(duration_ms, 3),
            "status": "complete",
            "matches": len(patterns),
        }
    )

    return {"patterns": patterns, "agent_trace": trace, "error": None}
