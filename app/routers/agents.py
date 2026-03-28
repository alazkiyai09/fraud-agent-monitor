from fastapi import APIRouter, HTTPException, Path, status

from app.agents.pattern_detector import detect_patterns
from app.agents.report_generator import generate_report
from app.agents.risk_scorer import score_risk
from app.agents.state import MonitorState
from app.agents.transaction_analyzer import analyze_transaction
from app.models.request import AgentInvokeRequest
from app.models.response import AgentInvokeResponse

router = APIRouter(prefix="/agents", tags=["agents"])

_AGENT_FN = {
    "transaction_analyzer": analyze_transaction,
    "pattern_detector": detect_patterns,
    "risk_scorer": score_risk,
    "report_generator": generate_report,
}


def _build_state(payload: AgentInvokeRequest) -> MonitorState:
    return {
        "messages": [],
        "transaction": payload.transaction.model_dump(),
        "analysis": payload.analysis,
        "patterns": payload.patterns,
        "risk": payload.risk,
        "report": payload.report,
        "agent_trace": [],
        "error": None,
        "langsmith_trace_url": None,
    }


@router.post("/{name}/invoke", response_model=AgentInvokeResponse)
def invoke_agent(
    payload: AgentInvokeRequest,
    name: str = Path(..., description="transaction_analyzer | pattern_detector | risk_scorer | report_generator"),
) -> AgentInvokeResponse:
    handler = _AGENT_FN.get(name)
    if handler is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown agent: {name}")

    state = _build_state(payload)

    try:
        updates = handler(state)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    state.update(updates)
    return AgentInvokeResponse(agent=name, state=state)
