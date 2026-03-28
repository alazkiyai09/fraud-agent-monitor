from app.agents.pattern_detector import detect_patterns
from app.agents.report_generator import generate_report
from app.agents.risk_scorer import score_risk
from app.agents.state import MonitorState
from app.agents.transaction_analyzer import analyze_transaction


def should_escalate(state: MonitorState) -> str:
    risk = state.get("risk")
    if risk and risk.get("risk_level") in {"MEDIUM", "HIGH", "CRITICAL"}:
        return "generate_report"
    return "end"


class FallbackCompiledGraph:
    def invoke(self, state: MonitorState) -> MonitorState:
        working = dict(state)
        working.update(analyze_transaction(working))
        working.update(detect_patterns(working))
        working.update(score_risk(working))
        if should_escalate(working) == "generate_report":
            working.update(generate_report(working))
        return working


def build_fraud_monitor_graph():
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return FallbackCompiledGraph()

    graph = StateGraph(MonitorState)

    graph.add_node("analyze_transaction", analyze_transaction)
    graph.add_node("detect_patterns", detect_patterns)
    graph.add_node("score_risk", score_risk)
    graph.add_node("generate_report", generate_report)

    graph.set_entry_point("analyze_transaction")
    graph.add_edge("analyze_transaction", "detect_patterns")
    graph.add_edge("detect_patterns", "score_risk")
    graph.add_conditional_edges(
        "score_risk",
        should_escalate,
        {
            "generate_report": "generate_report",
            "end": END,
        },
    )
    graph.add_edge("generate_report", END)

    return graph.compile()


fraud_monitor = build_fraud_monitor_graph()
