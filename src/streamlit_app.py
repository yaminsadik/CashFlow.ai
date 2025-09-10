# streamlit_app.py
import streamlit as st
import pandas as pd
import asyncio
import json
import hashlib
from langchain_core.messages import HumanMessage

from agents.cashflow_agent import cashflow_agent
from agents.data_normalizer_agent import infer_spec   # returns a Pydantic NormalizationSpec
from core.spec_apply import apply_spec                 # applies spec → normalized_df, issues

st.set_page_config(page_title="Cash Flow Generator - MVP", page_icon="💰", layout="wide")
st.title("💰 Cash Flow Generator - MVP")
st.caption("Small Business Mode (Direct Method): LLM infers normalization rules → deterministic transform → cash flow.")

# --- Session state (cache spec & normalized df per file signature) ---
if "spec_cache" not in st.session_state:
    st.session_state.spec_cache = {}
if "normalized_cache" not in st.session_state:
    st.session_state.normalized_cache = {}

# --- Helpers ---
def _file_sig(df: pd.DataFrame) -> str:
    """Stable signature by headers only (fast, good for re-uploads from same source)."""
    header_str = "|".join(list(df.columns))
    return hashlib.sha256(header_str.encode("utf-8")).hexdigest()

def _to_dict(obj):
    if hasattr(obj, "model_dump"):      # pydantic v2
        return obj.model_dump()
    if hasattr(obj, "dict"):            # pydantic v1
        return obj.dict()
    return obj

# --- Upload ---
st.subheader("📊 Upload Excel or CSV File")
uploaded_file = st.file_uploader("Choose file", type=["xlsx", "xls", "csv"])

if uploaded_file:
    # Read the file
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file, low_memory=False)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.stop()

    # Preview data
    st.subheader("📋 Data Preview")
    st.dataframe(df.head(50), use_container_width=True)
    sig = _file_sig(df)

    col_a, col_b, col_c = st.columns([1, 1, 1])

    # Infer + Apply in one go
    with col_a:
        infer_and_apply = st.button("🔎 Infer Rules & Normalize")

    with col_b:
        reset_spec = st.button("♻️ Reset Rules (re-infer)")

    with col_c:
        show_spec = st.checkbox("Show inferred rules (debug)", value=False)

    if reset_spec:
        st.session_state.spec_cache.pop(sig, None)
        st.session_state.normalized_cache.pop(sig, None)
        st.info("Spec & normalized cache cleared for this header signature. Click **Infer Rules & Normalize** again.")

    # Auto-load from cache if exists
    spec = st.session_state.spec_cache.get(sig)
    norm_pack = st.session_state.normalized_cache.get(sig)  # tuple: (normalized_df, issues)

    # Run inference + normalization if asked or cache empty
    if infer_and_apply or (spec is None and norm_pack is None):
        with st.spinner("Inferring normalization rules with LLM…"):
            try:
                # LLM returns a NormalizationSpec (structured output)
                spec = asyncio.run(infer_spec(df))
                st.session_state.spec_cache[sig] = spec
            except Exception as e:
                st.error(f"❌ Spec inference failed: {e}")
                st.stop()

        with st.spinner("Applying rules deterministically to full dataset…"):
            try:
                normalized_df, issues = apply_spec(df.copy(), spec)
                st.session_state.normalized_cache[sig] = (normalized_df, issues)
                norm_pack = (normalized_df, issues)
            except Exception as e:
                st.error(f"❌ Transform failed while applying spec: {e}")
                st.stop()

    # If we have a normalized result, show it
    if norm_pack:
        normalized_df, issues = norm_pack

        st.subheader("✅ Normalized Data (Canonical Schema)")
        st.dataframe(normalized_df.head(100), use_container_width=True)

        # Summary
        with st.expander("Summary & Quality Checks", expanded=True):
            total = int(len(normalized_df))
            date_range = "n/a"
            if total > 0 and "date" in normalized_df.columns:
                try:
                    date_range = f"{normalized_df['date'].min()} to {normalized_df['date'].max()}"
                except Exception:
                    pass

            st.markdown(f"- **Rows**: {total}\n- **Date range**: {date_range}")
            if issues:
                st.warning("**Issues detected:**\n- " + "\n- ".join(issues))
            else:
                st.success("No major issues detected by the transformer.")

        # Show spec (debug)
        if show_spec and spec is not None:
            with st.expander("🔧 Inferred NormalizationSpec (LLM output JSON)"):
                st.code(json.dumps(_to_dict(spec), indent=2))

        # Export button
        st.download_button(
            "⬇️ Export Normalized CSV",
            data=normalized_df.to_csv(index=False).encode("utf-8"),
            file_name="normalized_transactions.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # ---- Cash Flow Generation ----
        st.subheader("📈 Generate Direct-Method Cash Flow (Agent 1)")
        gen_btn = st.button("📊 Generate Cash Flow")

        if gen_btn:
            with st.spinner("Asking Agent 1 (Generator) to produce the cash flow…"):
                try:
                    # Send *normalized* CSV to the agent (smaller, consistent)
                    normalized_csv = normalized_df.to_csv(index=False)

                    # Give agent minimal, firm rules (keeps output consistent)
                    issues_text = "\n".join(issues) if issues else "None"
                    prompt = f"""
You are Agent 1 (Generator). Build a **Direct Method** cash flow statement from **normalized transactions** below (CSV).
Columns: date, description, amount, direction, category, balance, source.
Rules:
1) amount > 0 = cash inflow, amount < 0 = cash outflow.
2) Group and subtotal by simple categories if helpful; otherwise show aggregated inflows vs outflows.
3) Compute: Total Inflows, Total Outflows, **Net Change in Cash**.
4) If a 'balance' column exists with beginning and ending values, reconcile: Ending Cash - Beginning Cash == Net Change in Cash and report any variance.
5) Output in clean Markdown with a summary at the end (2-3 lines). Use two decimal places.

Known data quality issues (from the transformer):
{issues_text}

Normalized transactions (CSV):"""

                    config = {"configurable": {}}
                    result = asyncio.run(
                        cashflow_agent({"messages": [HumanMessage(content=prompt)]}, config=config)
                    )

                    st.success("✅ Cash Flow Generated!")
                    st.markdown(result["messages"][-1].content)

                except Exception as e:
                    st.error(f"❌ Error generating cash flow: {e}")
else:
    st.info("Upload a CSV/XLSX to begin.")

