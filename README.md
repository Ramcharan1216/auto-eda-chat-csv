# 📊 Auto-EDA — Analyze Any CSV, Then Chat With It

An app that takes any raw CSV (Kaggle datasets, exports, whatever) and automatically produces a full exploratory data analysis — dataset-agnostic column profiling, auto-selected charts, and a natural-language chat interface that writes and safely executes pandas code to answer questions about your actual data.

**[Live demo →](#)** *(add your Streamlit Cloud URL here after deploying)*

---

## What it does

Upload a CSV and the app immediately:

- **Profiles every column** — infers whether each is numeric, categorical, datetime, boolean, an identifier, or free text, using a chain of heuristics (no manual configuration per dataset), and flags data quality issues: missing values, outliers, skew, duplicate rows, constant columns.
- **Auto-generates the right chart per column** — histograms for numerics, bar charts for categoricals, a correlation heatmap when there are multiple numeric columns, time-series trends when a date column exists.
- **Answers questions about the data in plain English** — "what's the average price by city?" gets turned into real pandas code by an LLM, executed safely against your dataframe, and returned with both the answer and the code that produced it. Follow-up questions ("now break that down by year") use conversation context to build on prior answers.

## Why this is more than a wrapper around an LLM

The interesting engineering problem here isn't "call an LLM" — it's **running LLM-generated code safely**. An AI-written pandas snippet is untrusted code executing against real data, so naive `exec()` is not an option. This app defends in two layers:

1. **Static analysis** — every generated snippet is parsed into an AST before it runs. Imports, dunder-attribute access (blocks the classic `().__class__.__bases__` sandbox-escape trick), and dangerous builtins (`open`, `eval`, `exec`, `__import__`, etc.) are rejected outright.
2. **Restricted runtime execution** — code that passes the static check still runs in a namespace that only exposes `pandas`, `numpy`, and a small builtin allowlist, with a timeout so a hung computation can't block the app.

This isn't bulletproof (arbitrary Python was never designed to be sandboxed in-process — true isolation would mean a separate process or container), but it's a well-reasoned, tested defense-in-depth approach, and that honesty is itself part of the design.

## Tech stack

| Layer | Choice |
|---|---|
| UI | Streamlit |
| Data profiling & charts | pandas, NumPy, Plotly |
| Natural language → code | Google Gemini (`google-genai` SDK) |
| Code safety | Custom AST validator + restricted `exec` sandbox |
| Config | `python-dotenv`, Streamlit theme config |

## Project structure
## Running it locally

```bash
git clone <your-repo-url>
cd auto_eda_app
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

python -m pip install -r requirements.txt
```

Create a `.env` file (copy `.env.example`) with your own [GEMINI_API_KEY = your-key-here](https://aistudio.google.com/apikey):
Then run:

```bash
streamlit run app.py
```

## Known limitations

- Sandboxing is defense-in-depth, not a formal security boundary — see the safety section above.
- Very large CSVs (300K+ rows) are flagged but not sampled, since silently truncating data would give incorrect answers to aggregate questions.
- The chat feature requires a Gemini API key (free tier available).

---

*Built as a portfolio project exploring LLM-powered data tooling, prompt engineering, and safe code execution.*
