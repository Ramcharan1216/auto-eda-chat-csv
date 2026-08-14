import streamlit as st

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1100px;
    }

    .brand-mark {
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: #1d1d1f;
        margin-bottom: 0.25rem;
    }

    .brand-subtitle {
        font-size: 0.875rem;
        color: #6e6e73;
        margin-bottom: 1.5rem;
    }

    .data-pulse {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8125rem;
        font-weight: 500;
        color: #0071e3;
        background: #f5f5f7;
        border: 1px solid #e5e5ea;
        border-radius: 999px;
        padding: 0.4rem 0.85rem;
        margin-bottom: 1.25rem;
    }

    .data-pulse::before {
        content: "";
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #34c759;
        box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.15);
    }

    .section-title {
        font-size: 0.9375rem;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 0.75rem;
        letter-spacing: -0.01em;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e5e5ea;
        border-radius: 14px;
        padding: 1rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }

    div[data-testid="stMetric"] label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #6e6e73;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1d1d1f;
    }

    div[data-testid="stTab"] {
        font-size: 0.875rem;
        font-weight: 500;
        color: #6e6e73;
        padding: 0.75rem 1rem;
    }

    div[data-testid="stTab"] p,
    div[data-testid="stTab"] span {
        color: #6e6e73 !important;
    }

    div[data-testid="stTab"][aria-selected="true"] p,
    div[data-testid="stTab"][aria-selected="true"] span {
        color: #0071e3 !important;
        font-weight: 600 !important;
    }

    .react-aria-SelectionIndicator {
        background: #0071e3 !important;
    }

    [data-testid="stSidebar"] {
        background: #fbfbfd;
        border-right: 1px solid #e5e5ea;
    }

    [data-testid="stSidebar"] .brand-mark {
        font-size: 1.25rem;
        padding: 1rem 1.25rem 0;
    }

    .stFileUploader > section,
    div[data-testid="stFileUploader"] > section {
        border: 2px dashed #d1d1d6;
        border-radius: 16px;
        background: #fbfbfd;
        padding: 2rem 1rem;
    }

    .stFileUploader > section:hover,
    div[data-testid="stFileUploader"] > section:hover {
        border-color: #0071e3;
        background: rgba(0, 113, 227, 0.03);
    }

    .stFileUploader button,
    div[data-testid="stFileUploader"] button {
        background: #0071e3 !important;
        color: #ffffff !important;
        border-radius: 10px;
        font-weight: 500;
        padding: 0.5rem 1rem;
    }

    .chat-message {
        padding: 0.9rem 1.1rem;
        border-radius: 14px;
        margin-bottom: 0.75rem;
        max-width: 90%;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    .chat-user {
        background: #0071e3;
        color: #ffffff;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }

    .chat-assistant {
        background: #f5f5f7;
        color: #1d1d1f;
        border: 1px solid #e5e5ea;
        border-bottom-left-radius: 4px;
    }

    .stAlert {
        border-radius: 12px;
        border: none;
        padding: 0.85rem 1rem;
        font-size: 0.9rem;
    }

    .stDataFrame {
        border: 1px solid #e5e5ea;
        border-radius: 14px;
        overflow: hidden;
    }

    button[kind="primary"] {
        background: #0071e3;
        border-radius: 10px;
        font-weight: 500;
        padding: 0.5rem 1.1rem;
    }

    button[kind="secondary"] {
        border: 1px solid #e5e5ea;
        color: #1d1d1f;
        border-radius: 10px;
        font-weight: 500;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
"""

def apply_theme():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
