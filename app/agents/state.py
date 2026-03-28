from typing import Annotated, Optional, TypedDict

try:
    from langgraph.graph.message import add_messages
except Exception:  # pragma: no cover
    def add_messages(existing, new):
        return (existing or []) + (new or [])


class TransactionData(TypedDict):
    transaction_id: str
    amount: float
    sender_account: str
    receiver_account: str
    timestamp: str
    description: str
    channel: str
    location: str


class AnalysisResult(TypedDict):
    features_extracted: dict
    anomalies_detected: list[str]
    velocity_score: float
    amount_deviation: float


class PatternMatch(TypedDict):
    pattern_name: str
    confidence: float
    typology: str
    evidence: list[str]


class RiskAssessment(TypedDict):
    composite_score: float
    risk_level: str
    risk_factors: list[dict]
    recommended_action: str


class MonitorState(TypedDict):
    messages: Annotated[list, add_messages]
    transaction: TransactionData
    analysis: Optional[AnalysisResult]
    patterns: Optional[list[PatternMatch]]
    risk: Optional[RiskAssessment]
    report: Optional[str]
    agent_trace: list[dict]
    error: Optional[str]
    langsmith_trace_url: Optional[str]
