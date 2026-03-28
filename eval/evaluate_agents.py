import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.graph import build_fraud_monitor_graph


def run_scenarios(scenarios: list[dict]) -> dict:
    graph = build_fraud_monitor_graph()

    total = len(scenarios)
    pattern_hits = 0
    risk_hits = 0
    low_false_positive = 0
    low_total = 0

    for scenario in scenarios:
        state = {
            "messages": [],
            "transaction": scenario["transaction"],
            "analysis": None,
            "patterns": None,
            "risk": None,
            "report": None,
            "agent_trace": [],
            "error": None,
            "langsmith_trace_url": None,
        }
        result = graph.invoke(state)

        detected_typologies = {row.get("typology") for row in (result.get("patterns") or [])}
        expected_typologies = set(scenario.get("expected_typologies", []))
        if expected_typologies.issubset(detected_typologies):
            pattern_hits += 1

        expected_risk = scenario.get("expected_risk_level")
        if (result.get("risk") or {}).get("risk_level") == expected_risk:
            risk_hits += 1

        if expected_risk == "LOW":
            low_total += 1
            if (result.get("risk") or {}).get("risk_level") != "LOW":
                low_false_positive += 1

    pattern_accuracy = pattern_hits / total if total else 0.0
    risk_accuracy = risk_hits / total if total else 0.0
    false_positive_rate = low_false_positive / low_total if low_total else 0.0

    return {
        "scenario_count": total,
        "pattern_detection_accuracy": round(pattern_accuracy, 4),
        "risk_classification_accuracy": round(risk_accuracy, 4),
        "false_positive_rate_low_risk": round(false_positive_rate, 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Multi-Agent Fraud Monitor")
    parser.add_argument("--scenarios", default="eval/test_scenarios.json")
    parser.add_argument("--output", default="eval/results/metrics.json")
    args = parser.parse_args()

    scenarios = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    metrics = run_scenarios(scenarios)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
