from __future__ import annotations

import json
from datetime import datetime, time as dtime, timedelta, timezone

import pandas as pd
import streamlit as st

from components.shared_components import (
    api_call_with_retry,
    build_headers,
    get_setting,
    show_api_status,
    show_footer,
)
from components.shared_theme import THEME, risk_color, risk_emoji

API_URL = get_setting("API_URL", "https://fraud-monitor-api-5tphgb6fsa-as.a.run.app").rstrip("/")
API_KEY = get_setting("API_KEY", "")
HEADERS = build_headers(API_KEY)

TEST_SCENARIOS = {
    "🔴 Suspicious Wire Transfer": {
        "transaction_id": "TXN-2026-0042",
        "amount": 49999.00,
        "sender_account": "ACC-001-SENDER",
        "receiver_account": "ACC-999-RECEIVER",
        "timestamp": "2026-03-28T14:30:00Z",
        "description": "Wire transfer - business payment",
        "channel": "online_banking",
        "location": "Jakarta",
    },
    "🟡 Unusual Pattern": {
        "transaction_id": "TXN-2026-0088",
        "amount": 15000.00,
        "sender_account": "ACC-002-SENDER",
        "receiver_account": "ACC-888-RECEIVER",
        "timestamp": "2026-03-28T03:15:00Z",
        "description": "ATM withdrawal - cash advance",
        "channel": "atm",
        "location": "Surabaya",
    },
    "🟢 Normal Payment": {
        "transaction_id": "TXN-2026-0100",
        "amount": 500.00,
        "sender_account": "ACC-003-SENDER",
        "receiver_account": "ACC-777-RECEIVER",
        "timestamp": "2026-03-28T10:00:00Z",
        "description": "Monthly subscription payment",
        "channel": "online_banking",
        "location": "Jakarta",
    },
}

TEMPLATE_LIBRARY = {
    "🧾 Supplier Invoice (Routine)": {
        "transaction_id": "TPL-2026-1001",
        "amount": 4200.00,
        "sender_account": "ACC-411-SUPPLIER",
        "receiver_account": "ACC-920-VENDOR",
        "timestamp": "2026-03-28T09:15:00Z",
        "description": "Supplier invoice settlement for office equipment",
        "channel": "online_banking",
        "location": "Jakarta",
    },
    "💳 Card-Not-Present Burst": {
        "transaction_id": "TPL-2026-1108",
        "amount": 7800.00,
        "sender_account": "ACC-120-CARD",
        "receiver_account": "ACC-877-MERCHANT",
        "timestamp": "2026-03-28T22:45:00Z",
        "description": "Rapid sequence of card-not-present transactions",
        "channel": "mobile",
        "location": "Bandung",
    },
    "🏧 ATM Cash-Out Chain": {
        "transaction_id": "TPL-2026-1212",
        "amount": 12500.00,
        "sender_account": "ACC-302-ATM",
        "receiver_account": "ACC-812-CASH",
        "timestamp": "2026-03-28T03:30:00Z",
        "description": "Multiple ATM withdrawals in short interval",
        "channel": "atm",
        "location": "Surabaya",
    },
    "🌍 Cross-Border Wire (High Risk)": {
        "transaction_id": "TPL-2026-1315",
        "amount": 48500.00,
        "sender_account": "ACC-090-EXPORT",
        "receiver_account": "ACC-990-OFFSHORE",
        "timestamp": "2026-03-28T01:40:00Z",
        "description": "Cross-border wire to new offshore beneficiary",
        "channel": "online_banking",
        "location": "Jakarta",
    },
    "🪙 Crypto Funding Funnel": {
        "transaction_id": "TPL-2026-1418",
        "amount": 32000.00,
        "sender_account": "ACC-256-WALLET",
        "receiver_account": "ACC-709-EXCHANGE",
        "timestamp": "2026-03-28T18:05:00Z",
        "description": "Large transfer toward crypto exchange funding wallet",
        "channel": "mobile",
        "location": "Medan",
    },
    "📉 Dormant Account Reactivation": {
        "transaction_id": "TPL-2026-1521",
        "amount": 19800.00,
        "sender_account": "ACC-044-DORMANT",
        "receiver_account": "ACC-615-NEW",
        "timestamp": "2026-03-28T23:25:00Z",
        "description": "Dormant account reactivated with sudden outbound transfer",
        "channel": "branch",
        "location": "Denpasar",
    },
}

VARIATION_LABELS = {
    0: "Base Template",
    1: "Slight Shift",
    2: "Off-Hour Drift",
    3: "Counterparty Change Signal",
    4: "Velocity Spike",
    5: "Critical Edge Case",
}
LOCATION_VARIANTS = ["Jakarta", "Surabaya", "Bandung", "Medan", "Denpasar", "Makassar"]
CHANNELS = ["online_banking", "mobile", "branch", "atm"]
RUN_STATES = ["Idle", "Queued", "Processing", "Success", "Error"]


st.set_page_config(page_title="Fraud Monitor Demo", page_icon="🕵️", layout="wide")

st.markdown(
    f"""
    <style>
      .stApp {{
        background: linear-gradient(180deg, {THEME['background']} 0%, #111827 100%);
      }}
      .main-header {{
        font-size: 2rem;
        font-weight: 700;
      }}
      .sub-header {{
        color: #94A3B8;
        margin-bottom: 1.1rem;
      }}
      .timeline-node {{
        border-left: 3px solid #334155;
        padding-left: 0.8rem;
        margin-bottom: 0.65rem;
      }}
      .run-state-pill {{
        display: inline-block;
        border-radius: 999px;
        font-weight: 700;
        padding: 0.25rem 0.65rem;
      }}
      .state-idle {{ background:#334155; color:#E2E8F0; }}
      .state-queued {{ background:#A16207; color:#FEF3C7; }}
      .state-processing {{ background:#1D4ED8; color:#DBEAFE; }}
      .state-success {{ background:#166534; color:#DCFCE7; }}
      .state-error {{ background:#991B1B; color:#FEE2E2; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _parse_timestamp(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _iso_timestamp(date_value, time_value) -> str:
    dt = datetime.combine(date_value, time_value)
    dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _init_state() -> None:
    base = TEST_SCENARIOS["🔴 Suspicious Wire Transfer"]
    parsed = _parse_timestamp(base["timestamp"])
    default_template = next(iter(TEMPLATE_LIBRARY))

    defaults = {
        "tx_transaction_id": base["transaction_id"],
        "tx_amount": float(base["amount"]),
        "tx_sender_account": base["sender_account"],
        "tx_receiver_account": base["receiver_account"],
        "tx_date": parsed.date(),
        "tx_time": parsed.time().replace(tzinfo=None),
        "tx_description": base["description"],
        "tx_channel": base["channel"],
        "tx_location": base["location"],
        "template_name": default_template,
        "template_variation": 0,
        "start_mode": "Template Library",
        "pending_transaction_update": None,
        "monitor_result": None,
        "monitor_run_state": "Idle",
        "monitor_run_detail": "Ready to analyze a transaction",
        "last_monitor_error": "",
        "advanced_json_mode": False,
        "tx_json_payload": json.dumps({"transaction": base}, indent=2),
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _set_monitor_run_state(state: str, detail: str) -> None:
    if state not in RUN_STATES:
        state = "Error"
    st.session_state.monitor_run_state = state
    st.session_state.monitor_run_detail = detail


def _render_monitor_state() -> None:
    state = st.session_state.monitor_run_state
    st.markdown(
        f"<span class='run-state-pill state-{state.lower()}'>{state}</span> "
        f"<span style='color:#94A3B8'>{st.session_state.monitor_run_detail}</span>",
        unsafe_allow_html=True,
    )


def _queue_transaction_update(scenario: dict) -> None:
    st.session_state.pending_transaction_update = dict(scenario)


def _apply_pending_transaction_update() -> None:
    pending = st.session_state.pending_transaction_update
    if not pending:
        return

    parsed = _parse_timestamp(pending["timestamp"])
    st.session_state.tx_transaction_id = pending["transaction_id"]
    st.session_state.tx_amount = float(pending["amount"])
    st.session_state.tx_sender_account = pending["sender_account"]
    st.session_state.tx_receiver_account = pending["receiver_account"]
    st.session_state.tx_date = parsed.date()
    st.session_state.tx_time = parsed.time().replace(tzinfo=None)
    st.session_state.tx_description = pending["description"]
    st.session_state.tx_channel = pending["channel"]
    st.session_state.tx_location = pending["location"]
    st.session_state.tx_json_payload = json.dumps({"transaction": pending}, indent=2)
    st.session_state.pending_transaction_update = None
    st.session_state.monitor_result = None
    _set_monitor_run_state("Idle", "Preset loaded. Review advanced edits or run analysis.")


def _queue_scenario(name: str) -> None:
    _queue_transaction_update(TEST_SCENARIOS[name])


def _normalize_variation(value) -> int:
    if isinstance(value, int):
        return max(0, min(5, value))
    if isinstance(value, float):
        return max(0, min(5, int(value)))
    if isinstance(value, str):
        raw = value.strip()
        if raw.isdigit():
            return max(0, min(5, int(raw)))
        if raw.startswith("V"):
            digits = "".join(ch for ch in raw[1:] if ch.isdigit())
            if digits:
                return max(0, min(5, int(digits)))
    return 0


def _format_variation_option(value) -> str:
    normalized = _normalize_variation(value)
    return f"V{normalized} · {VARIATION_LABELS[normalized]}"


def _build_template_variation(name: str, variation: int) -> dict:
    base = dict(TEMPLATE_LIBRARY[name])
    variation = _normalize_variation(variation)
    amount = float(base["amount"])
    shifted = _parse_timestamp(base["timestamp"])

    profiles = {
        0: {"multiplier": 1.00, "minute_shift": 0, "hour": None, "channel": None},
        1: {"multiplier": 1.08 if amount >= 10000 else 1.04, "minute_shift": 19, "hour": None, "channel": None},
        2: {"multiplier": 1.14 if amount >= 10000 else 1.08, "minute_shift": 41, "hour": 2, "channel": "mobile"},
        3: {"multiplier": 1.22 if amount >= 10000 else 1.12, "minute_shift": 67, "hour": 6, "channel": "online_banking"},
        4: {"multiplier": 1.36 if amount >= 10000 else 1.18, "minute_shift": 93, "hour": 23, "channel": "mobile"},
        5: {"multiplier": 1.00, "minute_shift": 0, "hour": 2, "channel": "online_banking"},
    }
    profile = profiles[variation]
    shifted = shifted + timedelta(minutes=profile["minute_shift"])
    if profile["hour"] is not None:
        shifted = shifted.replace(hour=profile["hour"], minute=(shifted.minute + (variation * 7)) % 60)

    if base["location"] in LOCATION_VARIANTS:
        location_idx = LOCATION_VARIANTS.index(base["location"])
    else:
        location_idx = 0

    if variation == 5:
        base["amount"] = 49980.0 if amount >= 10000 else max(round(amount * 1.35, 2), 9800.0)
    else:
        base["amount"] = round(amount * profile["multiplier"], 2)
    base["timestamp"] = shifted.isoformat().replace("+00:00", "Z")
    base["transaction_id"] = f"{base['transaction_id']}-V{variation}"
    base["location"] = LOCATION_VARIANTS[(location_idx + variation) % len(LOCATION_VARIANTS)]

    scenario_notes = {
        0: "baseline behavior",
        1: "timing shifted with mild amount drift",
        2: "executed outside regular operating hours",
        3: "new beneficiary introduced within 24h",
        4: "third transfer to related counterparty within 30 minutes",
        5: "amount adjusted just below reporting threshold",
    }
    base["description"] = f"{base['description']} ({scenario_notes[variation]})"

    sender_tags = {0: "BASE", 1: "SHIFT", 2: "NIGHT", 3: "PROFILE", 4: "VELO", 5: "EDGE"}
    receiver_tags = {0: "KNOWN", 1: "ALT1", 2: "ALT2", 3: "NEWBEN", 4: "CHAIN", 5: "THRESH"}
    base["sender_account"] = f"{base['sender_account']}-{sender_tags[variation]}"
    base["receiver_account"] = f"{base['receiver_account']}-{receiver_tags[variation]}"

    if profile["channel"]:
        base["channel"] = profile["channel"]
    elif variation >= 4 and base["channel"] == "branch":
        base["channel"] = "online_banking"

    return base


def _queue_selected_template() -> None:
    scenario = _build_template_variation(
        st.session_state.template_name,
        _normalize_variation(st.session_state.template_variation),
    )
    _queue_transaction_update(scenario)


def _form_transaction_payload() -> dict:
    time_value = st.session_state.tx_time
    if isinstance(time_value, dtime):
        parsed_time = time_value
    else:
        parsed_time = dtime(hour=14, minute=30)

    return {
        "transaction_id": st.session_state.tx_transaction_id,
        "amount": float(st.session_state.tx_amount),
        "sender_account": st.session_state.tx_sender_account,
        "receiver_account": st.session_state.tx_receiver_account,
        "timestamp": _iso_timestamp(st.session_state.tx_date, parsed_time),
        "description": st.session_state.tx_description,
        "channel": st.session_state.tx_channel,
        "location": st.session_state.tx_location,
    }


def _validate_transaction_payload(transaction: dict) -> dict:
    required = [
        "transaction_id",
        "amount",
        "sender_account",
        "receiver_account",
        "timestamp",
        "description",
        "channel",
        "location",
    ]
    missing = [field for field in required if field not in transaction]
    if missing:
        raise ValueError(f"Missing transaction fields: {', '.join(missing)}")

    validated = dict(transaction)
    validated["amount"] = float(validated["amount"])
    validated["transaction_id"] = str(validated["transaction_id"])
    validated["sender_account"] = str(validated["sender_account"])
    validated["receiver_account"] = str(validated["receiver_account"])
    validated["timestamp"] = str(validated["timestamp"])
    validated["description"] = str(validated["description"])
    validated["channel"] = str(validated["channel"])
    validated["location"] = str(validated["location"])
    return validated


def _build_payload() -> dict:
    if not st.session_state.advanced_json_mode:
        return {"transaction": _form_transaction_payload()}

    raw = str(st.session_state.tx_json_payload or "").strip()
    if not raw:
        raise ValueError("JSON payload cannot be empty while Advanced mode is enabled.")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON syntax at line {exc.lineno}, column {exc.colno}.") from exc

    if not isinstance(parsed, dict):
        raise ValueError("JSON payload must be an object with a `transaction` key.")
    transaction = parsed.get("transaction")
    if not isinstance(transaction, dict):
        raise ValueError("`transaction` must be a JSON object.")

    return {"transaction": _validate_transaction_payload(transaction)}


def _queue_payload_from_json() -> str | None:
    raw = str(st.session_state.tx_json_payload or "").strip()
    if not raw:
        return "JSON payload is empty."
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return f"Invalid JSON syntax at line {exc.lineno}, column {exc.colno}."
    if not isinstance(parsed, dict) or not isinstance(parsed.get("transaction"), dict):
        return "JSON payload must contain an object in `transaction`."

    try:
        validated = _validate_transaction_payload(parsed["transaction"])
    except (TypeError, ValueError) as exc:
        return str(exc)

    _queue_transaction_update(validated)
    return None


def _fallback_monitor_response(transaction: dict, reason: str) -> dict:
    amount = float(transaction.get("amount", 0.0))
    tx_id = str(transaction.get("transaction_id", "TXN-DEMO"))
    description = str(transaction.get("description", ""))

    if amount >= 49000:
        risk_level = "CRITICAL"
        score = 0.93
        patterns = [
            {
                "pattern_name": "Structuring (Smurfing)",
                "typology": "smurfing",
                "confidence": 0.99,
            },
            {
                "pattern_name": "Mule Account Funnel",
                "typology": "mule_account",
                "confidence": 0.91,
            },
        ]
        report = (
            "### Suspicious Activity Report (Sample)\n\n"
            f"- Transaction ID: `{tx_id}`\n"
            "- Risk Level: **CRITICAL**\n"
            "- Recommended Action: **BLOCK + FILE SAR**\n"
            "- Notes: high-value transfer near threshold and suspicious behavior pattern."
        )
        factors = [
            {"factor": "anomaly_score", "value": 0.96},
            {"factor": "max_pattern_confidence", "value": 0.99},
            {"factor": "velocity_score", "value": 0.88},
            {"factor": "amount_deviation_normalized", "value": 0.93},
        ]
    elif amount >= 10000:
        risk_level = "MEDIUM"
        score = 0.57
        patterns = [
            {
                "pattern_name": "Unusual Withdrawal Cadence",
                "typology": "behavioral_anomaly",
                "confidence": 0.72,
            }
        ]
        report = None
        factors = [
            {"factor": "anomaly_score", "value": 0.62},
            {"factor": "max_pattern_confidence", "value": 0.72},
            {"factor": "velocity_score", "value": 0.51},
            {"factor": "amount_deviation_normalized", "value": 0.58},
        ]
    else:
        risk_level = "LOW"
        score = 0.11
        patterns = []
        report = None
        factors = [
            {"factor": "anomaly_score", "value": 0.08},
            {"factor": "max_pattern_confidence", "value": 0.00},
            {"factor": "velocity_score", "value": 0.20},
            {"factor": "amount_deviation_normalized", "value": 0.30},
        ]

    recommended_action = {
        "CRITICAL": "BLOCK",
        "HIGH": "HOLD",
        "MEDIUM": "REVIEW",
        "LOW": "APPROVE",
    }.get(risk_level, "REVIEW")

    return {
        "transaction_id": tx_id,
        "analysis": {
            "features_extracted": {
                "amount": amount,
                "amount_percent_of_threshold": round(amount / 50000.0, 4),
            },
            "anomalies_detected": [],
            "velocity_score": factors[2]["value"],
            "amount_deviation": factors[3]["value"],
            "description": description,
        },
        "patterns": patterns,
        "risk": {
            "composite_score": score,
            "risk_level": risk_level,
            "risk_factors": factors,
            "recommended_action": recommended_action,
        },
        "report": report,
        "agent_trace": [
            {"agent": "transaction_analyzer", "duration_ms": 0.9, "status": "complete"},
            {"agent": "pattern_detector", "duration_ms": 0.6, "status": "complete"},
            {"agent": "risk_scorer", "duration_ms": 0.5, "status": "complete"},
            {"agent": "report_generator", "duration_ms": 0.4, "status": "complete"},
        ],
        "total_time_ms": 3.1,
        "langsmith_trace_url": None,
        "error": None,
        "demo_mode": True,
        "demo_reason": reason,
    }


def _render_pipeline_vertical(agent_trace: list[dict], total_time_ms: float) -> None:
    st.markdown("### Agent Timeline")
    if not agent_trace:
        st.info("No agent trace available.")
        return

    completed = sum(1 for trace in agent_trace if str(trace.get("status", "")).lower() == "complete")
    st.progress(completed / max(len(agent_trace), 1))

    for trace in agent_trace:
        status = str(trace.get("status", "unknown")).lower()
        if status == "complete":
            icon = "✅"
            label = "Complete"
        elif status == "running":
            icon = "⏳"
            label = "Running"
        else:
            icon = "❌"
            label = "Error"

        agent_name = str(trace.get("agent", "agent")).replace("_", " ").title()
        duration = float(trace.get("duration_ms", 0.0))
        st.markdown(
            f"<div class='timeline-node'><strong>{icon} {agent_name}</strong><br/>"
            f"<span style='color:#94A3B8'>{label} · {duration:.1f} ms</span></div>",
            unsafe_allow_html=True,
        )

    st.caption(f"Total pipeline time: {total_time_ms:.1f} ms")


def _render_execution_graph(agent_trace: list[dict], risk_level: str, report_present: bool) -> None:
    node_order = [
        ("input_node", "Input Node"),
        ("transaction_analyzer", "Transaction Analyzer"),
        ("pattern_detector", "Pattern Detector"),
        ("risk_scorer", "Risk Scorer"),
        ("report_generator", "Report Generator"),
    ]
    status_by_node = {name: "pending" for name, _ in node_order}
    status_by_node["input_node"] = "complete"
    for item in agent_trace:
        agent_name = str(item.get("agent", "")).strip().lower()
        if agent_name in status_by_node:
            status_by_node[agent_name] = str(item.get("status", "complete")).strip().lower()

    if not report_present and risk_level.upper() in {"LOW"} and status_by_node["report_generator"] == "pending":
        status_by_node["report_generator"] = "skipped"

    colors = {
        "complete": ("#0B3B2E", "#2A9D8F", "#DCFCE7"),
        "running": ("#1E3A8A", "#60A5FA", "#DBEAFE"),
        "error": ("#7F1D1D", "#EF4444", "#FEE2E2"),
        "pending": ("#1F2937", "#334155", "#CBD5E1"),
        "skipped": ("#3F3F46", "#71717A", "#E4E4E7"),
    }

    lines = [
        "digraph G {",
        "rankdir=LR;",
        'bgcolor="transparent";',
        'node [shape=box, style="rounded,filled", penwidth=1.4, fontname="Helvetica"];',
        'edge [color="#64748B", penwidth=1.2];',
    ]

    for node_name, label in node_order:
        status = status_by_node.get(node_name, "pending")
        fill, border, font = colors.get(status, colors["pending"])
        lines.append(
            f'{node_name} [label="{label}\\n{status.upper()}", fillcolor="{fill}", color="{border}", fontcolor="{font}"];'
        )

    for src, dst in zip(node_order, node_order[1:]):
        lines.append(f"{src[0]} -> {dst[0]};")
    lines.append("}")
    st.graphviz_chart("\n".join(lines), use_container_width=True)


def _render_risk_factors(risk_factors: list[dict]) -> None:
    if not risk_factors:
        st.info("No risk factors returned by the monitor service.")
        return

    factors_sorted = sorted(
        [(str(item.get("factor", "unknown")), float(item.get("value", 0.0))) for item in risk_factors],
        key=lambda item: item[1],
        reverse=True,
    )

    st.markdown("#### Risk Factors")
    for factor_name, value in factors_sorted:
        st.markdown(f"**{factor_name}**")
        st.progress(min(max(value, 0.0), 1.0))
        st.caption(f"{value:.2f}")

    with st.expander("Detailed factor chart", expanded=False):
        factor_df = pd.DataFrame(
            {
                "factor": [name for name, _ in factors_sorted],
                "value": [value for _, value in factors_sorted],
            }
        ).sort_values("value", ascending=True)
        st.bar_chart(factor_df.set_index("factor"))


_init_state()
_apply_pending_transaction_update()

st.markdown("<div class='main-header'>🕵️ Fraud Monitor — Multi-Agent Investigation System</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-header'>4 AI agents collaborate to analyze suspicious transactions.</div>",
    unsafe_allow_html=True,
)

recovery_cols = st.columns([4, 1])
with recovery_cols[0]:
    st.caption(
        "If the page appears stuck during load, click Reload App. "
        "If live API fails, retry analysis or review fallback output."
    )
with recovery_cols[1]:
    if st.button("Reload App", key="reload_monitor_app", use_container_width=True):
        st.rerun()

with st.expander("ℹ️ Project Guide", expanded=False):
    st.markdown(
        "Fraud Monitor orchestrates four agents: signal extraction, pattern detection, risk scoring, and report generation."
    )
    st.markdown(
        "Start with Template Library or Quick Scenario, then use Advanced Edits only when you need custom values."
    )

status_tab, guide_tab = st.sidebar.tabs(["📊 Status", "ℹ️ Guide"])

with status_tab:
    st.header("📊 Status")
    api_connected, health = show_api_status(API_URL, headers=HEADERS)
    if health:
        st.caption(f"Graph compiled: {health.get('graph_compiled', False)}")
        st.caption(f"LLM provider: {health.get('llm_provider', 'unknown')}")

    if st.button("Reset Result", key="reset_monitor_result", use_container_width=True):
        st.session_state.monitor_result = None
        st.session_state.last_monitor_error = ""
        _set_monitor_run_state("Idle", "Ready to analyze a transaction")
        st.rerun()

with guide_tab:
    st.markdown("### What This Project Is")
    st.markdown(
        "Fraud Monitor is a multi-agent investigation workflow. "
        "It orchestrates specialized agents to analyze a transaction and produce a risk decision."
    )
    st.markdown("### Agent Pipeline")
    st.markdown(
        "1. **Transaction Analyzer** extracts key behavioral signals.\n"
        "2. **Pattern Detector** checks known fraud typologies.\n"
        "3. **Risk Scorer** computes composite risk and action.\n"
        "4. **Report Generator** drafts SAR-ready summary when needed."
    )

st.markdown("### Start Here")
st.radio(
    "Primary path",
    options=["Template Library", "Quick Scenario"],
    horizontal=True,
    key="start_mode",
)

if st.session_state.start_mode == "Template Library":
    template_cols = st.columns([2, 1, 1])
    with template_cols[0]:
        st.selectbox("Template", options=list(TEMPLATE_LIBRARY.keys()), key="template_name")
    with template_cols[1]:
        st.selectbox(
            "Variation",
            options=list(VARIATION_LABELS.keys()),
            format_func=_format_variation_option,
            key="template_variation",
        )
    with template_cols[2]:
        st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
        st.button(
            "Load Template",
            key="apply_template_btn",
            use_container_width=True,
            on_click=_queue_selected_template,
        )

    template_preview = _build_template_variation(
        st.session_state.template_name,
        _normalize_variation(st.session_state.template_variation),
    )
    preview_cols = st.columns(3)
    with preview_cols[0]:
        st.caption(f"Preview Amount: ${float(template_preview['amount']):,.2f}")
    with preview_cols[1]:
        st.caption(f"Preview Channel: {template_preview['channel']}")
    with preview_cols[2]:
        st.caption(f"Preview Location: {template_preview['location']} · Receiver: {template_preview['receiver_account']}")
else:
    scenario_cols = st.columns(3)
    for idx, scenario_name in enumerate(TEST_SCENARIOS):
        with scenario_cols[idx]:
            st.button(
                scenario_name,
                key=f"monitor_scenario_{idx}",
                use_container_width=True,
                on_click=_queue_scenario,
                args=(scenario_name,),
            )

st.info("Use the form for analyst-friendly input, or switch to Advanced JSON mode for developer-level payload edits.")

st.markdown("### Transaction Input")
input_cols = st.columns(4)
with input_cols[0]:
    st.text_input("Sender Account", key="tx_sender_account")
with input_cols[1]:
    st.text_input("Receiver Account", key="tx_receiver_account")
with input_cols[2]:
    st.number_input("Amount", min_value=0.0, max_value=1000000.0, step=100.0, key="tx_amount")
with input_cols[3]:
    st.selectbox("Channel", options=CHANNELS, key="tx_channel")

more_cols = st.columns(4)
with more_cols[0]:
    st.text_input("Location", key="tx_location")
with more_cols[1]:
    st.text_input("Transaction ID", key="tx_transaction_id")
with more_cols[2]:
    st.date_input("Date", key="tx_date")
with more_cols[3]:
    st.time_input("Time (UTC)", key="tx_time")

st.text_area("Description", key="tx_description")

st.toggle(
    "Advanced: Edit JSON payload",
    key="advanced_json_mode",
    help="Enable this only when you need direct JSON control of the monitor request payload.",
)
if st.session_state.advanced_json_mode:
    st.text_area("Monitor Request JSON", key="tx_json_payload", height=240)
    json_cols = st.columns([1, 2])
    with json_cols[0]:
        if st.button("Load JSON Into Form", key="load_json_to_form_btn", use_container_width=True):
            error = _queue_payload_from_json()
            if error:
                st.error(error)
            else:
                st.success("JSON parsed and queued. Form values refreshed.")
                st.rerun()
    with json_cols[1]:
        st.caption("JSON must include `transaction` with required fields.")

st.markdown("### Run Analysis")
_render_monitor_state()
run_clicked = st.button("Analyze Transaction", use_container_width=True)
retry_clicked = False
if st.session_state.last_monitor_error:
    st.warning(f"Last live API call failed: {st.session_state.last_monitor_error}")
    retry_clicked = st.button("Retry Last Analysis", key="retry_last_monitor", use_container_width=False)

if run_clicked or retry_clicked:
    try:
        payload = _build_payload()
    except ValueError as exc:
        st.error(f"Payload validation failed: {exc}")
        payload = None

if (run_clicked or retry_clicked) and payload is not None:
    state_box = st.empty()

    _set_monitor_run_state("Queued", "Transaction queued")
    state_box.info("Run State: Queued - Transaction queued")

    _set_monitor_run_state("Processing", "Executing multi-agent monitor pipeline")
    state_box.info("Run State: Processing - Executing multi-agent monitor pipeline")

    response = api_call_with_retry(
        f"{API_URL}/monitor",
        method="POST",
        headers=HEADERS,
        json_payload=payload,
        timeout=120,
        max_retries=1,
    )

    if response.get("error"):
        detail = str(response.get("detail") or response["error"])
        st.session_state.last_monitor_error = detail
        _set_monitor_run_state("Error", f"Live API unavailable: {detail}")
        state_box.error(f"Run State: Error - Live API unavailable: {detail}")
        st.session_state.monitor_result = _fallback_monitor_response(payload["transaction"], detail)
    else:
        st.session_state.last_monitor_error = ""
        _set_monitor_run_state("Success", "Live monitor API response received")
        state_box.success("Run State: Success - Live monitor API response received")
        st.session_state.monitor_result = response

result = st.session_state.monitor_result
if result:
    st.markdown("### Results")
    if result.get("demo_mode"):
        st.error(
            "DEMO FALLBACK MODE ACTIVE: Results below are generated by local sample logic, not the live monitor API."
        )
        st.caption(f"Fallback reason: {result.get('demo_reason', 'API fallback')}")
    else:
        st.success("LIVE API MODE ACTIVE: Results below are generated by the deployed monitor service.")

    agent_trace = result.get("agent_trace") or []
    total_time_ms = float(result.get("total_time_ms", 0.0))
    risk = result.get("risk") or {}
    risk_level = str(risk.get("risk_level", "LOW"))

    graph_col, timeline_col = st.columns([1.4, 1.0])
    with graph_col:
        st.markdown("### Visual Execution Graph")
        _render_execution_graph(agent_trace, risk_level=risk_level, report_present=bool(result.get("report")))
    with timeline_col:
        _render_pipeline_vertical(agent_trace, total_time_ms)

    left, right = st.columns([1, 2])
    with left:
        composite = float(risk.get("composite_score", 0.0))
        action = str(risk.get("recommended_action", "REVIEW"))

        st.metric("Risk Score", f"{composite * 100:.1f}%")
        st.progress(min(max(composite, 0.0), 1.0))
        st.markdown(
            f"<span style='background:{risk_color(risk_level)}; color:white; font-weight:700; "
            f"padding:0.3rem 0.65rem; border-radius:999px;'>{risk_emoji(risk_level)} {risk_level}</span>",
            unsafe_allow_html=True,
        )
        st.metric("Recommended Action", action)

    with right:
        patterns = result.get("patterns") or []
        st.markdown("#### Patterns Detected")
        if patterns:
            for pattern in patterns:
                st.write(
                    f"• {pattern.get('pattern_name', 'pattern')} "
                    f"({pattern.get('typology', 'unknown')}) — {float(pattern.get('confidence', 0.0)) * 100:.1f}%"
                )
        else:
            st.write("• No high-confidence patterns detected")

        _render_risk_factors(risk.get("risk_factors") or [])

    report = result.get("report")
    st.markdown("### Suspicious Activity Report Preview")
    if report:
        st.caption("Print-ready preview (markdown).")
        st.text_area("SAR Preview", value=report, height=260, disabled=True)
        download_cols = st.columns(3)
        with download_cols[0]:
            st.download_button(
                "📥 Download .md",
                data=report,
                file_name=f"sar_{result.get('transaction_id', 'report')}.md",
                mime="text/markdown",
            )
        with download_cols[1]:
            st.download_button(
                "📥 Download .txt",
                data=report,
                file_name=f"sar_{result.get('transaction_id', 'report')}.txt",
                mime="text/plain",
            )
        with download_cols[2]:
            html_report = (
                "<html><head><meta charset='utf-8'><title>SAR</title></head>"
                "<body style='font-family:Arial,sans-serif;max-width:960px;margin:2rem auto;'>"
                f"<pre style='white-space:pre-wrap;'>{report}</pre></body></html>"
            )
            st.download_button(
                "📥 Download HTML",
                data=html_report,
                file_name=f"sar_{result.get('transaction_id', 'report')}.html",
                mime="text/html",
            )
    else:
        st.info("No SAR report generated for this risk level.")

    if result.get("langsmith_trace_url"):
        st.markdown(f"🔗 [View full agent trace in LangSmith]({result['langsmith_trace_url']})")

show_footer()
