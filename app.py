import os
from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from researcher import collect_research
from synthesizer import generate_full_report
from report_builder import create_company_report


# ─────────────────────────────────────────────────────────────
# API KEY VALIDATION
# ─────────────────────────────────────────────────────────────

if not os.getenv("GROQ_API_KEY"):
    st.error(
        "GROQ_API_KEY is not configured. "
        "Please add it to your .env file or Streamlit secrets."
    )
    st.stop()


# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ResearchMind",
    page_icon="📊",
    layout="wide"
)

st.title("📊 ResearchMind")
st.subheader("AI-Powered Company Intelligence Report Generator")


# ─────────────────────────────────────────────────────────────
# INPUT
# ─────────────────────────────────────────────────────────────

company = st.text_input(
    "Enter Company Name"
)


# ─────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────

if st.button("Generate Report"):

    if not company.strip():
        st.warning("Please enter a company name.")
        st.stop()

    if len(company.strip()) > 100:
        st.warning("Please enter a valid company name (under 100 characters).")
        st.stop()

    try:

        progress_bar = st.progress(0)
        status_text = st.empty()

        # STEP 1
        status_text.text(
            "🔎 Generating research queries and searching the web..."
        )

        progress_bar.progress(10)

        research_data = collect_research(company)

        # Empty Research Protection
        if (
            not research_data
            or all(len(v) == 0 for v in research_data.values())
        ):
            progress_bar.empty()
            status_text.empty()

            st.error(
                f"Could not find sufficient public data for '{company}'. "
                "Please try a more well-known company."
            )

            st.stop()

        progress_bar.progress(40)

        # STEP 2
        status_text.text(
            "🤖 Synthesizing intelligence report..."
        )

        progress_bar.progress(50)

        report = generate_full_report(research_data)

        progress_bar.progress(75)

        # STEP 3
        status_text.text(
            "📄 Building PDF report..."
        )

        progress_bar.progress(85)

        pdf_path = create_company_report(
            company,
            report,
            research_data
        )

        progress_bar.progress(100)

        status_text.text("✅ Report ready!")

        st.success("Report Generated Successfully!")

        st.markdown(report)

        with open(pdf_path, "rb") as file:

            st.download_button(
                label="⬇️ Download PDF Report",
                data=file,
                file_name=f"{company}_Intelligence_Report.pdf",
                mime="application/pdf"
            )

    except Exception as e:

        st.error(
            f"Unexpected error occurred:\n\n{str(e)}"
        )