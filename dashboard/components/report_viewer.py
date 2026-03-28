import streamlit as st


def render_report(report: str | None) -> None:
    st.subheader("SAR Report")
    if not report:
        st.info("No report generated for this transaction")
        return

    st.markdown(report)
    st.download_button(
        "Download SAR",
        data=report,
        file_name="sar_report.md",
        mime="text/markdown",
    )
