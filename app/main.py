from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.graph import build_fraud_monitor_graph
from app.config import get_settings
from app.routers import agents_router, health_router, monitor_router

settings = get_settings()
settings.apply_langsmith_env()

app = FastAPI(
    title="Multi-Agent Fraud Monitor",
    version="0.1.0",
    description="LangGraph-based multi-agent fraud monitoring pipeline.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(monitor_router)
app.include_router(agents_router)

app.state.fraud_monitor_graph = build_fraud_monitor_graph()
app.state.langsmith_connected = bool(settings.langsmith_api_key)
app.state.llm_provider = settings.llm_provider
app.state.agent_timeout_seconds = settings.agent_timeout_seconds
app.state.langchain_project = settings.langchain_project


@app.get("/")
def root() -> dict:
    return {
        "name": "Multi-Agent Fraud Monitor",
        "status": "running",
        "docs": "/docs",
    }
