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

# Dark-mode override, targeting the same selectors theme.py styles for
# light mode (most of which hardcode black text/borders with !important,
# so we mirror each one with a dark equivalent rather than trying to
# blanket-override everything).
DARK_MODE_CSS = """
<style>
    .stApp {
        background-color: #0e1117 !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #f0f0f2 !important;
    }

    .brand-mark, .brand-subtitle, .section-title {
        color: #f0f0f2 !important;
    }

    .data-pulse {
        color: #f0f0f2 !important;
        background: #171a23 !important;
        border: 1px solid #3a3f4b !important;
    }

    .hero-divider {
        background: linear-gradient(90deg, #f0f0f2, transparent) !important;
    }

    div[data-testid="stMetric"] {
        background: #171a23 !important;
        border: 1px solid #3a3f4b !important;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #f0f0f2 !important;
    }

    div[data-testid="stTab"],
    div[data-testid="stTab"] p,
    div[data-testid="stTab"] span {
        color: #d0d0d5 !important;
    }
    div[data-testid="stTab"][aria-selected="true"] p,
    div[data-testid="stTab"][aria-selected="true"] span {
        color: #4da3ff !important;
    }

    [data-testid="stSidebar"] {
        background: #12141c !important;
        border-right: 1px solid #3a3f4b !important;
    }

    .stFileUploader > section,
    div[data-testid="stFileUploader"] > section {
        border: 2px dashed #3a3f4b !important;
        background: #171a23 !important;
    }
    .stFileUploader > section:hover,
    div[data-testid="stFileUploader"] > section:hover {
        border-color: #4da3ff !important;
        background: rgba(77, 163, 255, 0.06) !important;
    }

    [data-testid="stChatMessage"] {
        border: 1px solid #3a3f4b !important;
        background: #171a23 !important;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * {
        color: #f0f0f2 !important;
    }

    [data-testid="stExpander"] {
        border: 1px solid #3a3f4b !important;
    }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary * {
        color: #f0f0f2 !important;
    }

    .stAlert {
        border: 1px solid #3a3f4b !important;
    }

    .stDataFrame {
        border: 1px solid #3a3f4b !important;
    }

    button[kind="secondary"] {
        background: #171a23 !important;
        border: 1px solid #3a3f4b !important;
        color: #f0f0f2 !important;
    }

    [data-testid="stChatInput"] {
        background: #171a23 !important;
        border: 1px solid #3a3f4b !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #f0f0f2 !important;
    }

    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p,
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] *,
    [data-testid="stFileUploaderDropzoneInstructions"],
    [data-testid="stFileUploaderDropzoneInstructions"] * {
        color: #d0d0d5 !important;
    }

    [data-testid="stChatInputSubmitButton"] {
        color: #f0f0f2 !important;
    }
    [data-testid="stChatInputSubmitButton"] svg {
        fill: #f0f0f2 !important;
        color: #f0f0f2 !important;
    }
</style>
"""

KIND_LABELS = {
    NUMERIC: "🔢 Numeric",
    CATEGORICAL: "🏷️ Categorical",
    DATETIME: "📅 Datetime",
    BOOLEAN: "✅ Boolean",
    TEXT: "📝 Text",
    ID_LIKE: "🔑 Identifier",
}


def _init_state():
    """Everything the sidebar history + theme toggle needs, set up once."""
    st.session_state.setdefault("dark_mode", False)
    st.session_state.setdefault("upload_order", [])   # list of dataset_keys, most recent first
    st.session_state.setdefault("uploads", {})         # dataset_key -> {"name": str, "bytes": bytes}
    st.session_state.setdefault("chat_histories", {})   # dataset_key -> list of chat entries
    st.session_state.setdefault("active_dataset_key", None)


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


def _ask_and_store(api_key, df, profile, question, dataset_key):
    """Shared by both the free-text chat input and the suggested-question
    buttons, so asking a suggested question behaves identically to typing
    it. Prior (successful) turns are passed as context for follow-ups."""
    history = st.session_state.chat_histories.setdefault(dataset_key, [])
    with st.spinner("Writing and running pandas code..."):
        outcome = answer_question(api_key, df, profile, question, history=history)
    history.insert(0, {"question": question, **outcome})


def render_chat(df, profile, dataset_key):
    st.caption(
        "Ask a question in plain English. The LLM writes pandas code to answer it, "
        "which runs in a sandboxed environment against your actual data."
    )

    api_key = st.session_state.get("gemini_api_key", "")
    if not api_key:
        st.info("Enter your Gemini API key in the sidebar to use the chat feature.")
        return

    history = st.session_state.chat_histories.setdefault(dataset_key, [])

    if not history:
        suggestions = generate_suggested_questions(profile)
        if suggestions:
            st.caption("Try asking:")
            cols = st.columns(len(suggestions))
            for col, suggestion in zip(cols, suggestions):
                if col.button(suggestion, key=f"suggestion_{suggestion}", use_container_width=True):
                    _ask_and_store(api_key, df, profile, suggestion, dataset_key)
                    st.rerun()

    question = st.chat_input("e.g. What's the average value by category?")
    if question:
        _ask_and_store(api_key, df, profile, question, dataset_key)

    for entry in history:
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


def render_sidebar():
    """Hamburger-style side menu: brand, theme toggle, API key (silent
    when available), and a History section covering both past uploads
    and each upload's chat log."""
    with st.sidebar:
        top_l, top_r = st.columns([3, 1])
        with top_l:
            st.markdown('<div class="brand-mark">AUTO · EDA</div>', unsafe_allow_html=True)
        with top_r:
            dark = st.toggle("🌙", value=st.session_state.dark_mode, help="Dark mode", label_visibility="collapsed")
            if dark != st.session_state.dark_mode:
                st.session_state.dark_mode = dark
                st.rerun()

        # API key: loaded silently from .env / Streamlit secrets when present.
        # Only shown as an input if no key is configured anywhere.
        env_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
        if env_key:
            st.session_state["gemini_api_key"] = env_key
        else:
            api_key_input = st.text_input(
                "Gemini API key", type="password",
                help="Get one free at aistudio.google.com/apikey",
            )
            if api_key_input:
                st.session_state["gemini_api_key"] = api_key_input

        st.divider()

        with st.expander("🕘 History", expanded=bool(st.session_state.upload_order)):
            if not st.session_state.upload_order:
                st.caption("Nothing uploaded yet this session.")
            else:
                for key in st.session_state.upload_order:
                    record = st.session_state.uploads.get(key)
                    if not record:
                        continue
                    n_questions = len(st.session_state.chat_histories.get(key, []))
                    is_active = key == st.session_state.active_dataset_key
                    label = f"{'📌 ' if is_active else '📄 '}{record['name']}"
                    if st.button(label, key=f"history_{key}", use_container_width=True):
                        st.session_state.active_dataset_key = key
                        st.rerun()
                    caption = f"{n_questions} question{'s' if n_questions != 1 else ''} asked" if n_questions else "No questions asked yet"
                    st.caption(caption)

                st.write("")
                if st.button("🗑️ Clear history", use_container_width=True):
                    st.session_state.upload_order = []
                    st.session_state.uploads = {}
                    st.session_state.chat_histories = {}
                    st.session_state.active_dataset_key = None
                    st.rerun()


def main():
    _init_state()
    if st.session_state.dark_mode:
        st.markdown(DARK_MODE_CSS, unsafe_allow_html=True)

    st.title("📊 Auto-EDA: Analyze Any CSV")
    st.caption("Upload a raw CSV (e.g. from Kaggle) and get an instant, dataset-agnostic exploratory analysis.")
    st.markdown('<div class="hero-divider"></div>', unsafe_allow_html=True)

    render_sidebar()

    uploaded_file = st.file_uploader("Upload your CSV", type=["csv"])

    # A fresh upload takes priority and becomes the active dataset.
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        dataset_key = f"{uploaded_file.name}-{uploaded_file.size}"
        if dataset_key not in st.session_state.uploads:
            st.session_state.uploads[dataset_key] = {"name": uploaded_file.name, "bytes": file_bytes}
            st.session_state.upload_order.insert(0, dataset_key)
        st.session_state.active_dataset_key = dataset_key

    active_key = st.session_state.active_dataset_key

    if active_key is None or active_key not in st.session_state.uploads:
        st.info("👆 Upload a CSV to get started. Try any Kaggle dataset — Titanic, house prices, customer churn, etc.")
        return

    record = st.session_state.uploads[active_key]

    with st.spinner("Reading and profiling your data..."):
        load_result = load_csv_cached(record["bytes"], record["name"])

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

    st.markdown(
        f'<div class="data-pulse">{profile.n_rows:,} rows &middot; {profile.n_cols} columns &middot; {record["name"]}</div>',
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
        render_chat(df, profile, active_key)


if __name__ == "__main__":
    main()
