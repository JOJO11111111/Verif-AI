"""VerifAI - Streamlit GUI for AI-powered financial fact-checking."""

import streamlit as st
from pipeline import run_pipeline

st.set_page_config(
    page_title="VerifAI - Financial Fact Checker",
    page_icon="🔍",
    layout="wide",
)

# --- Header ---
st.title("🔍 VerifAI")
st.markdown(
    "**AI-powered fact-checking for financial claims.** "
    "Built for financial advisors and individual investors to verify suspicious investment claims and protect against fraud."
)

st.markdown("---")

# --- Sidebar: how it works ---
with st.sidebar:
    st.header("How it works")
    st.markdown(
        """
        VerifAI uses a three-stage AI pipeline:

        **1. Decomposition** — Claude breaks your claim into atomic, verifiable sub-assertions.

        **2. Evidence Retrieval** — GPT-4o-mini + Tavily search gather evidence from authoritative sources (SEC, FINRA, registries).

        **3. Synthesis** — Claude weighs the evidence and produces a final verdict with confidence scores and citations.

        ---

        **Why orchestrate two models?**
        We route reasoning tasks to Claude and retrieval tasks to GPT — giving you the strongest reasoning where it matters and faster, cheaper retrieval where it doesn't.
        """
    )
    st.markdown("---")
    st.caption("CMU 14-789 · AI in Business Modeling")

# --- Input ---
st.subheader("Submit a claim to verify")

example_claims = {
    "— Choose an example —": "",
    "Crypto fraud (senior persona)": "My neighbor told me about a crypto fund called Doc Rock Company that pays 15% monthly dividends, guaranteed. Is this legit?",
    "Facebook investment ad": "I saw on Facebook that SafeHaven Capital guarantees 20% annual returns with zero risk.",
    "Cold call (advisor persona)": "My client got a call from someone at 'Morgan Stanley Senior Advisors' offering a special bond program for retirees with 9% guaranteed returns. Is this real?",
}

example_choice = st.selectbox("Or pick an example:", list(example_claims.keys()))
default_text = example_claims[example_choice]

claim = st.text_area(
    "Paste the claim here:",
    value=default_text,
    height=100,
    placeholder="e.g., 'My neighbor told me about a crypto fund that pays 15% monthly dividends, guaranteed...'",
)

verify_button = st.button("🔎 Verify Claim", type="primary", use_container_width=True)

# --- Run pipeline ---
if verify_button:
    if not claim.strip():
        st.warning("Please enter a claim to verify.")
    else:
        st.markdown("---")

        # Progress placeholders
        status = st.status("Running VerifAI pipeline...", expanded=True)
        stage_messages = []

        def progress(stage, message):
            stage_messages.append((stage, message))
            with status:
                st.write(f"**{message}**")

        try:
            with status:
                result = run_pipeline(claim, progress_callback=progress)
            status.update(label="✅ Verification complete", state="complete", expanded=False)

            # --- Display results ---
            st.markdown("## 📋 Verdict Report")

            # Show sub-claims that were checked
            with st.expander("🔬 Sub-claims that were checked", expanded=False):
                for i, sc in enumerate(result["sub_claims"], 1):
                    st.markdown(f"{i}. {sc}")

            # Show raw evidence (for transparency)
            with st.expander("📚 Raw evidence gathered (transparency log)", expanded=False):
                for item in result["evidence"]:
                    st.markdown(f"**Sub-claim:** {item['sub_claim']}")
                    st.markdown(item["evidence"])
                    st.markdown("---")

            # Main verdict
            st.markdown("### Final Verdict")
            st.markdown(result["verdict"])

        except Exception as e:
            status.update(label="❌ Pipeline failed", state="error")
            st.error(f"Something went wrong: {e}")
            st.exception(e)