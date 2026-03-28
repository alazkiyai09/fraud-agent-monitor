from pydantic import BaseModel, Field


class TransactionInput(BaseModel):
    transaction_id: str = Field(...)
    amount: float = Field(..., ge=0)
    sender_account: str = Field(...)
    receiver_account: str = Field(...)
    timestamp: str = Field(..., description="ISO-8601 timestamp")
    description: str = Field(default="")
    channel: str = Field(default="online_banking")
    location: str = Field(default="unknown")


class MonitorRequest(BaseModel):
    transaction: TransactionInput


class AgentInvokeRequest(BaseModel):
    transaction: TransactionInput
    analysis: dict | None = None
    patterns: list[dict] | None = None
    risk: dict | None = None
    report: str | None = None
