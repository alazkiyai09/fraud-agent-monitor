import json
from pathlib import Path


def _load_patterns(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("patterns"), list):
        return data["patterns"]
    if isinstance(data, list):
        return data
    return []


def match_patterns(analysis: dict, patterns_path: str) -> list[dict]:
    anomalies = set(analysis.get("anomalies_detected", []))
    if not anomalies:
        return []

    matched: list[dict] = []
    for pattern in _load_patterns(patterns_path):
        indicators = set(pattern.get("indicators", []))
        overlap = anomalies.intersection(indicators)
        if not overlap:
            continue

        indicator_ratio = len(overlap) / max(len(indicators), 1)
        confidence = min(0.99, float(pattern.get("base_confidence", 0.4)) + indicator_ratio * 0.5)

        matched.append(
            {
                "pattern_name": pattern.get("name", pattern.get("typology", "unknown-pattern")),
                "confidence": round(confidence, 4),
                "typology": pattern.get("typology", "unknown"),
                "evidence": sorted(overlap),
            }
        )

    matched.sort(key=lambda row: row.get("confidence", 0.0), reverse=True)
    return matched
