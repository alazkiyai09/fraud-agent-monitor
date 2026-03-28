import streamlit as st


def render_risk_dashboard(risk: dict | None) -> None:
    st.subheader("Risk Dashboard")
    if not risk:
        st.info("No risk assessment available")
        return

    st.metric("Risk Level", risk.get("risk_level", "N/A"))
    st.metric("Composite Score", risk.get("composite_score", 0.0))

    factors = risk.get("risk_factors", [])
    if factors:
        st.markdown("**Risk Factors**")
        for factor in factors:
            st.write(f"- {factor.get('factor')}: {factor.get('value')} (w={factor.get('weight')})")
