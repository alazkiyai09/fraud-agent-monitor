import json
import os

import requests
import streamlit as st

from components.agent_trace_viewer import render_agent_trace
from components.report_viewer import render_report
from components.risk_dashboard import render_risk_dashboard

API_URL = os.getenv("API_URL", "http://localhost:8001")

st.set_page_config(page_title="Fraud Monitor Dashboard", page_icon="FM", layout="wide")
st.title("Multi-Agent Fraud Monitor Dashboard")
st.caption("Submit transactions, inspect agent traces, risk scores, and generated SAR reports.")

sample_payload = {
    "transaction": {
        "transaction_id": "TXN-2026-0042",
        "amount": 49999.0,
        "sender_account": "ACC-001-SENDER",
        "receiver_account": "ACC-999-RECEIVER",
        "timestamp": "2026-03-28T14:30:00Z",
        "description": "Wire transfer - business payment",
        "channel": "online_banking",
        "location": "Jakarta",
    }
}

payload_text = st.text_area("Monitor Request JSON", value=json.dumps(sample_payload, indent=2), height=260)

if st.button("Run Monitor"):
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        st.error(f"Invalid JSON: {exc.msg}")
        st.stop()

    try:
        response = requests.post(f"{API_URL}/monitor", json=payload, timeout=120)
    except requests.RequestException as exc:
        st.error(f"API error: {exc}")
        st.stop()

    if not response.ok:
        st.error(f"Request failed: {response.status_code}")
        st.json(response.json())
        st.stop()

    result = response.json()

    col1, col2 = st.columns(2)
    with col1:
        render_risk_dashboard(result.get("risk"))
    with col2:
        st.subheader("Matched Patterns")
        patterns = result.get("patterns") or []
        if patterns:
            st.json(patterns)
        else:
            st.info("No patterns matched")

    render_agent_trace(result.get("agent_trace") or [])
    render_report(result.get("report"))

    if result.get("langsmith_trace_url"):
        st.markdown(f"[Open LangSmith Trace]({result['langsmith_trace_url']})")
