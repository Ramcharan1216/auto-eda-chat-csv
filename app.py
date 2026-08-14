"""
app.py
------
Auto-EDA app: upload any CSV -> profiling report, auto-charts, and a
chat tab where an LLM writes+runs pandas code to answer questions.

Run locally with:
    pip install -r requirements.txt
    streamlit run app.py
"""

import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

import theme
from data_profiler import profile_dataset, NUMERIC, CATEGORICAL, DATETIME, BOOLEAN, TEXT, ID_LIKE
from chart_generator import generate_charts
from csv_loader import load_csv_robust
from suggested_questions import generate_suggested_questions
from llm_query_engine import answer_question

load_dotenv(encoding="utf-8-sig")

st.set_page_config(page_title="Auto-EDA: Analyze Any CSV", page_icon="📊", layout="wide")
st.markdown(theme.CUSTOM_CSS, unsafe_allow_html=True)

KIND_LABELS = {
    NUMERIC: "🔢 Numeric",
    CATEGORICAL: "🏷️ Categorical",
    DATETIME: "📅 Datetime",
    BOOLEAN: "✅ Boolean",
    TEXT: "📝 Text",
    ID_LIKE: "🔑 Identifier",
}


@st.cache_data(show_spinner=False)
def load_csv_cached(file_bytes: bytes, file_name: str):
    """Cache key is the raw bytes + name, not the UploadedFile object itself
    (which isn't hashable in a stable way across reruns)."""
    import types
    fake_file = types.SimpleNamespace(getvalue=lambda: file_bytes)
    return load_csv_robust(fake_file)


def render_overview(profile):
    with st.container(border=True):
        st.markdown("##### Dataset Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", f"{profile.n_rows:,}")
        c2.metric("Columns", profile.n_cols)
        c3.metric("Duplicate rows", profile.n_duplicate_rows)
        c4.metric("Memory", f"{profile.memory_mb} MB")

    st.write("")

    with st.container(border=True):
        st.markdown("##### Data Quality")
        if profile.dataset_warnings:
            for w in profile.dataset_warnings:
                st.warning(w)
        else:
            st.success("No major data quality issues detected.")


def render_column_table(profile):
    with st.container(border=True):
        st.markdown("##### Column Breakdown")
        rows = []
        for name, cp in profile.column_profiles.items():
            rows.append({
                "Column": name,
                "Type": KIND_LABELS.get(cp.kind, cp.kind),
                "Missing %": cp.missing_pct,
                "Unique values": cp.n_unique,
                "Flags": "; ".join(cp.warnings) if cp.warnings else "—",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_charts(df, profile):
    charts = generate_charts(df, profile)
    if not charts:
        st.info("Not enough structure in this dataset to auto-generate charts.")
        return

    cols = st.columns(2)
    for i, (chart_id, fig) in enumerate(charts):
        with cols[i % 2]:
            with st.container(border=True):
                st.plotly_chart(fig, use_container_width=True, key=chart_id)


def _render_answer_result(result):
    """Decide how to display whatever `result` the generated code produced."""
    if isinstance(result, pd.Series):
        st.dataframe(result.rename("value"), use_container_width=True)
        if 2 <= len(result) <= 30 and pd.api.types.is_numeric_dtype(result):
            chart_df = result.reset_index()
            chart_df.columns = ["category", "value"]
            fig = px.bar(chart_df, x="category", y="value")
            st.plotly_chart(fig, use_container_width=True)
    elif isinstance(result, pd.DataFrame):
        st.dataframe(result, use_container_width=True)
    elif isinstance(result, float):
        st.metric("Answer", f"{result:,.4f}")
    elif isinstance(result, int):
        st.metric("Answer", f"{result:,}")
    else:
        st.write(result)


def _ask_and_store(api_key, df, profile, question):
    """Shared by both the free-text chat input and the suggested-question
    buttons, so asking a suggested question behaves identically to typing
    it. Prior (successful) turns are passed as context for follow-ups."""
    with st.spinner("Writing and running pandas code..."):
        outcome = answer_question(api_key, df, profile, question, history=st.session_state.chat_history)
    st.session_state.chat_history.insert(0, {"question": question, **outcome})


def render_chat(df, profile, dataset_key):
    st.caption(
        "Ask a question in plain English. The LLM writes pandas code to answer it, "
        "which runs in a sandboxed environment against your actual data."
    )

    api_key = st.session_state.get("gemini_api_key", "")
    if not api_key:
        st.info("Enter your Gemini API key in the sidebar to use the chat feature.")
        return

    if st.session_state.get("chat_dataset_key") != dataset_key:
        st.session_state.chat_history = []
        st.session_state.chat_dataset_key = dataset_key

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if not st.session_state.chat_history:
        suggestions = generate_suggested_questions(profile)
        if suggestions:
            st.caption("Try asking:")
            cols = st.columns(len(suggestions))
            for col, suggestion in zip(cols, suggestions):
                if col.button(suggestion, key=f"suggestion_{suggestion}", use_container_width=True):
                    _ask_and_store(api_key, df, profile, suggestion)
                    st.rerun()

    question = st.chat_input("e.g. What's the average value by category?")
    if question:
        _ask_and_store(api_key, df, profile, question)

    for entry in st.session_state.chat_history:
        with st.chat_message("user", avatar="🧑"):
            st.write(entry["question"])
        with st.chat_message("assistant", avatar="📊"):
            if entry["success"]:
                _render_answer_result(entry["result"])
                with st.expander("Show generated code"):
                    st.code(entry["code"], language="python")
            else:
                st.error(f"Couldn't answer that: {entry['error']}")
                if entry.get("code"):
                    with st.expander("Show attempted code"):
                        st.code(entry["code"], language="python")


def main():
    st.title("📊 Auto-EDA: Analyze Any CSV")
    st.caption("Upload a raw CSV (e.g. from Kaggle) and get an instant, dataset-agnostic exploratory analysis.")
    st.markdown('<div class="hero-divider"></div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="brand-mark">AUTO · EDA</div>', unsafe_allow_html=True)
        st.subheader("⚙️ Settings")
        env_key = os.environ.get("GEMINI_API_KEY", "")
        api_key_input = st.text_input(
            "Gemini API key", type="password", value=env_key,
            help="Loaded automatically from .env if present. Get one at aistudio.google.com/apikey",
        )
        if api_key_input:
            st.session_state["gemini_api_key"] = api_key_input

    uploaded_file = st.file_uploader("Upload your CSV", type=["csv"])

    if uploaded_file is None:
        st.info("👆 Upload a CSV to get started. Try any Kaggle dataset — Titanic, house prices, customer churn, etc.")
        return

    with st.spinner("Reading and profiling your data..."):
        load_result = load_csv_cached(uploaded_file.getvalue(), uploaded_file.name)

    if load_result.error:
        st.error(f"Couldn't load this file: {load_result.error}")
        st.caption("Try re-saving the file as UTF-8 CSV, or double-check it's a valid CSV export.")
        return

    df = load_result.df

    try:
        profile = profile_dataset(df)
    except Exception as e:
        st.error(f"Something went wrong while analyzing this file: {e}")
        st.caption("If this keeps happening on a specific file, it may have an unusual structure worth checking manually.")
        return

    if load_result.is_large:
        st.info(f"This is a large dataset ({load_result.encoding_used} encoding, {len(df):,} rows) -- analysis may take a bit longer than usual.")

    dataset_key = f"{uploaded_file.name}-{uploaded_file.size}"

    st.markdown(
        f'<div class="data-pulse">{profile.n_rows:,} rows &middot; {profile.n_cols} columns &middot; {uploaded_file.name}</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Overview", "📊 Auto-Generated Charts", "🔍 Raw Data", "💬 Chat with your Data"]
    )

    with tab1:
        render_overview(profile)
        st.write("")
        render_column_table(profile)

    with tab2:
        render_charts(df, profile)

    with tab3:
        with st.container(border=True):
            st.dataframe(df.head(200), use_container_width=True)

    with tab4:
        render_chat(df, profile, dataset_key)


if __name__ == "__main__":
    main()
