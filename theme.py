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
        background-color: #f5f5f7 !important;
    }

   h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
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
        color: #000000;
        margin-bottom: 0.25rem;
    }

    .brand-subtitle {
        font-size: 0.875rem;
        color: #000000;
        margin-bottom: 1.5rem;
    }

    .data-pulse {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8125rem;
        font-weight: 500;
        color: #000000;
        background: #f5f5f7;
        border: 1px solid #000000;
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

    .hero-divider {
        height: 3px;
        background: linear-gradient(90deg, #000000, transparent);
        border-radius: 2px;
        margin: 4px 0 20px 0;
    }

    .section-title {
        font-size: 0.9375rem;
        font-weight: 600;
        color: #000000;
        margin-bottom: 0.75rem;
        letter-spacing: -0.01em;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #000000;
        border-radius: 14px;
        padding: 1rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }

    div[data-testid="stMetric"] label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #000000;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 700;
        color: #000000;
    }

    div[data-testid="stTab"] {
        font-size: 0.875rem;
        font-weight: 500;
        color: #000000;
        padding: 0.75rem 1rem;
    }

    div[data-testid="stTab"] p,
    div[data-testid="stTab"] span {
        color: #000000 !important;
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
        border-right: 1px solid #000000;
    }

    [data-testid="stSidebar"] .brand-mark {
        font-size: 1.25rem;
        padding: 1rem 1.25rem 0;
    }

    .stFileUploader > section,
    div[data-testid="stFileUploader"] > section {
        border: 2px dashed #000000;
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
        color: #000000;
        border: 1px solid #000000;
        border-bottom-left-radius: 4px;
    }

    [data-testid="stChatMessage"] {
        border-radius: 14px;
        border: 1px solid #000000;
        background: #ffffff;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * {
        color: #000000 !important;
    }

    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary * {
        color: #000000 !important;
    }

    [data-testid="stExpander"] {
        border: 1px solid #000000 !important;
    }

    .stAlert {
        border-radius: 12px;
        border: 1px solid #000000;
        padding: 0.85rem 1rem;
        font-size: 0.9rem;
    }

    .stDataFrame {
        border: 1px solid #000000;
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
        background: #ffffff !important;
        border: 1px solid #000000;
        color: #000000 !important;
        border-radius: 10px;
        font-weight: 500;
    }

    [data-testid="stChatInput"] {
        background: #ffffff !important;
        border: 1px solid #000000 !important;
        border-radius: 12px;
    }
    [data-testid="stChatInput"] textarea {
        color: #000000 !important;
        background: transparent !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #6e6e73 !important;
    }

    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {
        color: #000000 !important;
    }
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] * {
        color: #000000 !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"],
    [data-testid="stFileUploaderDropzoneInstructions"] * {
        color: #000000 !important;
    }

    [data-testid="stChatInputSubmitButton"] {
        color: #000000 !important;
        background: transparent !important;
    }
    [data-testid="stChatInputSubmitButton"] svg {
        fill: #000000 !important;
        color: #000000 !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
"""


def apply_theme():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


_template = go.layout.Template()
_template.layout = go.Layout(
    colorway=["#0071e3", "#34c759", "#ff9500", "#af52de", "#ff3b30", "#5ac8fa"],
    font=dict(family="Inter, sans-serif", color="#000000", size=13),
    title=dict(font=dict(family="Inter, sans-serif", size=16, color="#000000")),
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    xaxis=dict(gridcolor="#e5e5ea", zerolinecolor="#000000", linecolor="#000000"),
    yaxis=dict(gridcolor="#e5e5ea", zerolinecolor="#000000", linecolor="#000000"),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    margin=dict(t=50, l=10, r=10, b=10),
)
pio.templates["auto_eda"] = _template
pio.templates.default = "auto_eda"
