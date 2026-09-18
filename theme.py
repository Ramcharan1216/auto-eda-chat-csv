import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background-color: #f7f7fb !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #1a1a2e !important;
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
        color: #1a1a2e;
        margin-bottom: 0.25rem;
    }

    .brand-subtitle {
        font-size: 0.875rem;
        color: #1a1a2e;
        margin-bottom: 1.5rem;
    }

    .data-pulse {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8125rem;
        font-weight: 500;
        color: #1a1a2e;
        background: #ffffff;
        border: 1px solid #e0e0eb;
        border-radius: 999px;
        padding: 0.4rem 0.85rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 2px rgba(99, 102, 241, 0.06);
    }

    .data-pulse::before {
        content: "";
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #34c759;
        box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.15);
    }

    .hero-divider {
        height: 3px;
        background: linear-gradient(90deg, #6366f1, transparent);
        border-radius: 2px;
        margin: 4px 0 20px 0;
    }

    .section-title {
        font-size: 0.9375rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.75rem;
        letter-spacing: -0.01em;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        animation: fadeIn 0.35s ease-out;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e0e0eb;
        border-radius: 14px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(99, 102, 241, 0.06);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }

    div[data-testid="stMetric"]:hover {
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.12);
        transform: translateY(-1px);
    }

    div[data-testid="stMetric"] label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #6b6b80;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1a1a2e;
    }

    div[data-testid="stTab"] {
        font-size: 0.875rem;
        font-weight: 500;
        color: #1a1a2e;
        padding: 0.75rem 1rem;
        transition: color 0.15s ease;
    }

    div[data-testid="stTab"] p,
    div[data-testid="stTab"] span {
        color: #1a1a2e !important;
    }

    div[data-testid="stTab"][aria-selected="true"] p,
    div[data-testid="stTab"][aria-selected="true"] span {
        color: #6366f1 !important;
        font-weight: 600 !important;
    }

    .react-aria-SelectionIndicator {
        background: #6366f1 !important;
    }

    [data-testid="stSidebar"] {
        background: #fbfbfd;
        border-right: 1px solid #e0e0eb;
    }

    [data-testid="stSidebar"] .brand-mark {
        font-size: 1.25rem;
        padding: 1rem 1.25rem 0;
    }

    .stFileUploader > section,
    div[data-testid="stFileUploader"] > section {
        border: 2px dashed #c7c7e0;
        border-radius: 16px;
        background: #fbfbfd;
        padding: 2rem 1rem;
        transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
    }

    .stFileUploader > section:hover,
    div[data-testid="stFileUploader"] > section:hover {
        border-color: #6366f1;
        background: rgba(99, 102, 241, 0.04);
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.06);
    }

    .stFileUploader button,
    div[data-testid="stFileUploader"] button {
        background: #6366f1 !important;
        color: #ffffff !important;
        border-radius: 10px;
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: background 0.15s ease;
    }

    .stFileUploader button:hover,
    div[data-testid="stFileUploader"] button:hover {
        background: #4f46e5 !important;
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
        background: #6366f1;
        color: #ffffff;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }

    .chat-assistant {
        background: #f7f7fb;
        color: #1a1a2e;
        border: 1px solid #e0e0eb;
        border-bottom-left-radius: 4px;
    }

    [data-testid="stChatMessage"] {
        border-radius: 14px;
        border: 1px solid #e0e0eb;
        background: #ffffff;
        animation: fadeIn 0.3s ease-out;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * {
        color: #1a1a2e !important;
    }

    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary * {
        color: #1a1a2e !important;
    }

    [data-testid="stExpander"] {
        border: 1px solid #e0e0eb !important;
    }

    .stAlert {
        border-radius: 12px;
        border: 1px solid #e0e0eb;
        padding: 0.85rem 1rem;
        font-size: 0.9rem;
    }

    .stDataFrame {
        border: 1px solid #e0e0eb;
        border-radius: 14px;
        overflow: hidden;
    }

    button[kind="primary"] {
        background: #6366f1;
        border-radius: 10px;
        font-weight: 500;
        padding: 0.5rem 1.1rem;
        transition: background 0.15s ease, transform 0.1s ease;
    }
    button[kind="primary"]:hover {
        background: #4f46e5;
        transform: translateY(-1px);
    }

    button[kind="secondary"] {
        background: #ffffff !important;
        border: 1px solid #e0e0eb;
        color: #1a1a2e !important;
        border-radius: 10px;
        font-weight: 500;
        transition: border-color 0.15s ease, transform 0.1s ease;
    }
    button[kind="secondary"]:hover {
        border-color: #6366f1;
        transform: translateY(-1px);
    }

    [data-testid="stChatInput"] {
        background: #ffffff !important;
        border: 1px solid #e0e0eb !important;
        border-radius: 12px;
    }
    [data-testid="stChatInput"] textarea {
        color: #1a1a2e !important;
        background: transparent !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #9494a8 !important;
    }

    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {
        color: #1a1a2e !important;
    }
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] * {
        color: #6b6b80 !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"],
    [data-testid="stFileUploaderDropzoneInstructions"] * {
        color: #1a1a2e !important;
    }

    [data-testid="stChatInputSubmitButton"] {
        color: #6366f1 !important;
        background: transparent !important;
    }
    [data-testid="stChatInputSubmitButton"] svg {
        fill: #6366f1 !important;
        color: #6366f1 !important;
    }

    [data-testid="stToolbarActions"] {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""


def apply_theme():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


_template = go.layout.Template()
_template.layout = go.Layout(
    colorway=["#6366f1", "#34c759", "#ff9500", "#af52de", "#ff3b30", "#22c3dd"],
    font=dict(family="Inter, sans-serif", color="#1a1a2e", size=13),
    title=dict(font=dict(family="Inter, sans-serif", size=16, color="#1a1a2e")),
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    xaxis=dict(gridcolor="#eeeef5", zerolinecolor="#c7c7e0", linecolor="#c7c7e0"),
    yaxis=dict(gridcolor="#eeeef5", zerolinecolor="#c7c7e0", linecolor="#c7c7e0"),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    margin=dict(t=50, l=10, r=10, b=10),
)
pio.templates["auto_eda"] = _template
pio.templates.default = "auto_eda"
