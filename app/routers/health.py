from fastapi import APIRouter, Request

from app.models.response import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    return HealthResponse(
        status="healthy",
        graph_compiled=bool(getattr(request.app.state, "fraud_monitor_graph", None) is not None),
        agent_count=4,
        langsmith_connected=bool(getattr(request.app.state, "langsmith_connected", False)),
        llm_provider=str(getattr(request.app.state, "llm_provider", "unknown")),
    )
