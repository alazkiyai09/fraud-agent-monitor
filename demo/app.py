from __future__ import annotations

from datetime import datetime, time as dtime, timezone

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

CHANNELS = ["online_banking", "mobile", "branch", "atm"]


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
      .agent-card {{
        text-align: center;
        padding: 0.8rem;
        border-radius: 10px;
        min-height: 120px;
      }}
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
        "auto_run_monitor": False,
        "monitor_result": None,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


_init_state()


def _apply_scenario(name: str) -> None:
    scenario = TEST_SCENARIOS[name]
    parsed = _parse_timestamp(scenario["timestamp"])

    st.session_state.tx_transaction_id = scenario["transaction_id"]
    st.session_state.tx_amount = float(scenario["amount"])
    st.session_state.tx_sender_account = scenario["sender_account"]
    st.session_state.tx_receiver_account = scenario["receiver_account"]
    st.session_state.tx_date = parsed.date()
    st.session_state.tx_time = parsed.time().replace(tzinfo=None)
    st.session_state.tx_description = scenario["description"]
    st.session_state.tx_channel = scenario["channel"]
    st.session_state.tx_location = scenario["location"]
    st.session_state.auto_run_monitor = True


def _build_payload() -> dict:
    time_value = st.session_state.tx_time
    if isinstance(time_value, dtime):
        parsed_time = time_value
    else:
        parsed_time = dtime(hour=14, minute=30)

    return {
        "transaction": {
            "transaction_id": st.session_state.tx_transaction_id,
            "amount": float(st.session_state.tx_amount),
            "sender_account": st.session_state.tx_sender_account,
            "receiver_account": st.session_state.tx_receiver_account,
            "timestamp": _iso_timestamp(st.session_state.tx_date, parsed_time),
            "description": st.session_state.tx_description,
            "channel": st.session_state.tx_channel,
            "location": st.session_state.tx_location,
        }
    }


def _render_pipeline(agent_trace: list[dict], total_time_ms: float) -> None:
    st.markdown("### Agent Pipeline")
    if not agent_trace:
        st.info("No agent trace available.")
        return

    progress = st.progress(0)
    slot_count = (len(agent_trace) * 2) - 1
    slots = st.columns(slot_count)

    for idx, trace in enumerate(agent_trace):
        progress.progress((idx + 1) / len(agent_trace))
        status = str(trace.get("status", "unknown"))

        if status == "complete":
            icon = "✅"
            border = "#2A9D8F"
        elif status == "running":
            icon = "⏳"
            border = "#F4A261"
        else:
            icon = "❌"
            border = "#E63946"

        agent_name = str(trace.get("agent", "agent")).replace("_", " ").title()
        duration = float(trace.get("duration_ms", 0.0))

        with slots[idx * 2]:
            st.markdown(
                f"""
                <div class='agent-card' style='border:2px solid {border}; background:#1E293B;'>
                    <div style='font-size:1.4rem'>{icon}</div>
                    <div style='font-weight:700'>{agent_name}</div>
                    <div style='color:#94A3B8'>{duration:.1f} ms</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if idx < len(agent_trace) - 1:
            with slots[(idx * 2) + 1]:
                st.markdown("<div style='text-align:center; font-size:1.6rem; padding-top:2.7rem;'>→</div>", unsafe_allow_html=True)

    st.caption(f"Total pipeline time: {total_time_ms:.1f} ms")


st.markdown("<div class='main-header'>🕵️ Fraud Monitor — Multi-Agent Investigation System</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-header'>4 AI agents collaborate to analyze suspicious transactions.</div>",
    unsafe_allow_html=True,
)

st.sidebar.header("📊 Status")
api_connected, health = show_api_status(API_URL, headers=HEADERS)
if health:
    st.sidebar.caption(f"Graph compiled: {health.get('graph_compiled', False)}")
    st.sidebar.caption(f"LLM provider: {health.get('llm_provider', 'unknown')}")

if st.sidebar.button("Reset Result", use_container_width=True):
    st.session_state.monitor_result = None
    st.rerun()

st.markdown("### Transaction Input")
input_cols = st.columns(4)
with input_cols[0]:
    st.number_input("Amount", min_value=0.0, max_value=1000000.0, step=100.0, key="tx_amount")
with input_cols[1]:
    st.selectbox("Channel", options=CHANNELS, key="tx_channel")
with input_cols[2]:
    st.text_input("Location", key="tx_location")
with input_cols[3]:
    st.text_input("Transaction ID", key="tx_transaction_id")

st.text_area("Description", key="tx_description")
more_cols = st.columns(4)
with more_cols[0]:
    st.text_input("Sender Account", key="tx_sender_account")
with more_cols[1]:
    st.text_input("Receiver Account", key="tx_receiver_account")
with more_cols[2]:
    st.date_input("Date", key="tx_date")
with more_cols[3]:
    st.time_input("Time (UTC)", key="tx_time")

scenario_cols = st.columns(3)
for idx, scenario_name in enumerate(TEST_SCENARIOS):
    with scenario_cols[idx]:
        if st.button(scenario_name, key=f"monitor_scenario_{idx}", use_container_width=True):
            _apply_scenario(scenario_name)
            st.rerun()

run_clicked = st.button("🔍 Analyze Transaction", use_container_width=True)
auto_run = bool(st.session_state.auto_run_monitor)
st.session_state.auto_run_monitor = False

if run_clicked or auto_run:
    payload = _build_payload()
    with st.spinner("Running 4-agent pipeline..."):
        response = api_call_with_retry(
            f"{API_URL}/monitor",
            method="POST",
            headers=HEADERS,
            json_payload=payload,
            timeout=120,
            max_retries=1,
        )

    if "error" in response:
        st.error(response.get("detail", response["error"]))
        st.session_state.monitor_result = None
    else:
        st.session_state.monitor_result = response

result = st.session_state.monitor_result
if result:
    agent_trace = result.get("agent_trace") or []
    total_time_ms = float(result.get("total_time_ms", 0.0))
    _render_pipeline(agent_trace, total_time_ms)

    st.markdown("### Results")
    left, right = st.columns([1, 2])

    risk = result.get("risk") or {}
    with left:
        composite = float(risk.get("composite_score", 0.0))
        risk_level = str(risk.get("risk_level", "LOW"))
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

        risk_factors = risk.get("risk_factors") or []
        if risk_factors:
            factor_df = pd.DataFrame(
                {
                    "factor": [item.get("factor", "unknown") for item in risk_factors],
                    "value": [float(item.get("value", 0.0)) for item in risk_factors],
                }
            ).sort_values("value", ascending=True)
            st.markdown("#### Risk Factors")
            st.bar_chart(factor_df.set_index("factor"))

    report = result.get("report")
    st.markdown("### Generated SAR Report")
    if report:
        st.markdown(report)
        st.code(report, language="markdown")
        st.download_button(
            "📥 Download Report",
            data=report,
            file_name=f"sar_{result.get('transaction_id', 'report')}.md",
            mime="text/markdown",
        )
    else:
        st.info("No SAR report generated for this risk level.")

    if result.get("langsmith_trace_url"):
        st.markdown(f"🔗 [View full agent trace in LangSmith]({result['langsmith_trace_url']})")

show_footer()
