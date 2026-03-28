from time import perf_counter

from fastapi import APIRouter, HTTPException, Request, status

from app.agents.state import MonitorState
from app.models.request import MonitorRequest
from app.models.response import MonitorResponse

router = APIRouter(tags=["monitor"])


def _build_initial_state(payload: MonitorRequest) -> MonitorState:
    return {
        "messages": [],
        "transaction": payload.transaction.model_dump(),
        "analysis": None,
        "patterns": None,
        "risk": None,
        "report": None,
        "agent_trace": [],
        "error": None,
        "langsmith_trace_url": None,
    }


@router.post("/monitor", response_model=MonitorResponse)
def run_monitor(payload: MonitorRequest, request: Request) -> MonitorResponse:
    graph = getattr(request.app.state, "fraud_monitor_graph", None)
    if graph is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Fraud monitor graph unavailable")

    started = perf_counter()
    state = _build_initial_state(payload)

    try:
        result = graph.invoke(state)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    total_time_ms = (perf_counter() - started) * 1000

    timeout_ms = float(getattr(request.app.state, "agent_timeout_seconds", 30)) * 1000
    for trace in result.get("agent_trace", []):
        if float(trace.get("duration_ms", 0.0)) > timeout_ms:
            raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Agent timeout exceeded")

    langsmith_trace_url = None
    if getattr(request.app.state, "langsmith_connected", False):
        transaction_id = result.get("transaction", {}).get("transaction_id", "unknown")
        langsmith_trace_url = (
            f"https://smith.langchain.com/o/default/projects/p/{request.app.state.langchain_project}"
            f"?q={transaction_id}"
        )

    return MonitorResponse(
        transaction_id=result["transaction"]["transaction_id"],
        analysis=result.get("analysis"),
        patterns=result.get("patterns"),
        risk=result.get("risk"),
        report=result.get("report"),
        agent_trace=result.get("agent_trace", []),
        total_time_ms=round(total_time_ms, 3),
        langsmith_trace_url=langsmith_trace_url,
        error=result.get("error"),
    )
