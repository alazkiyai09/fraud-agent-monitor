import streamlit as st


def render_agent_trace(agent_trace: list[dict]) -> None:
    st.subheader("Agent Trace")
    if not agent_trace:
        st.info("No agent trace available")
        return

    for index, row in enumerate(agent_trace, start=1):
        st.markdown(
            f"**{index}. {row.get('agent')}** | duration: {row.get('duration_ms')} ms | status: {row.get('status')}"
        )
        st.json(row)
