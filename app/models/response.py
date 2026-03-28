from pydantic import BaseModel, Field


class MonitorResponse(BaseModel):
    transaction_id: str
    analysis: dict | None = None
    patterns: list[dict] | None = None
    risk: dict | None = None
    report: str | None = None
    agent_trace: list[dict] = Field(default_factory=list)
    total_time_ms: float
    langsmith_trace_url: str | None = None
    error: str | None = None


class AgentInvokeResponse(BaseModel):
    agent: str
    state: dict


class HealthResponse(BaseModel):
    status: str
    graph_compiled: bool
    agent_count: int
    langsmith_connected: bool
    llm_provider: str
