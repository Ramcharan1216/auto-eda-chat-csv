"""
llm_query_engine.py
--------------------
Turns a natural-language question into pandas code (via Gemini), then runs
that code through sandbox_executor.py and returns a structured answer.

Flow for one question:
  1. build_schema_context(df, profile) -> a compact text description of
     the dataframe (column names, kinds, sample rows) so the LLM knows
     what it's working with without us dumping the whole CSV into the prompt.
  2. build_conversation_context(...) -> recent successful Q&A, for follow-ups.
  3. generate_pandas_code(...) -> call Gemini, get back Python code.
  4. sandbox_executor.execute_safely(...) -> run it safely.
  5. If it fails, retry ONCE, feeding the error back to the LLM so it can
     self-correct.

Uses the `google-genai` package (the current unified Google GenAI SDK):
    pip install google-genai
"""

import re
import pandas as pd
from google import genai
from google.genai import types

from sandbox_executor import execute_safely, UnsafeCodeError, ExecutionError

MODEL_NAME = "gemini-3.5-flash"

SYSTEM_INSTRUCTION = """You are a data analysis assistant. You will be given the schema of a \
pandas DataFrame called `df` and a question about it. Write Python code that computes the answer.

Rules (follow all of them exactly):
1. Assign your final answer to a variable named `result`.
2. Only use `df`, `pd` (pandas), and `np` (numpy) -- these already exist. Do not import anything.
3. Do not read or write files, do not access the network, do not use exec/eval/open.
4. Output ONLY the Python code. No explanation, no markdown code fences, no comments before or after.
5. If the question implies a breakdown/comparison across groups (e.g. "by region", \
"for each category", "average X per Y"), make `result` a pandas Series or DataFrame, \
not a single scalar, so it can be charted.
6. If the question just asks for a single number, count, or fact, make `result` a plain \
Python scalar (int, float, or str).
7. Keep the code short -- usually 1-3 lines is enough."""


def build_schema_context(df: pd.DataFrame, profile) -> str:
    """Compact schema description fed to the LLM. Uses the DatasetProfile
    from data_profiler.py so we reuse type-detection work already done."""
    lines = [f"DataFrame `df` has {profile.n_rows} rows and {profile.n_cols} columns:"]
    for name, cp in profile.column_profiles.items():
        detail = f"  - {name} ({cp.kind}, dtype={cp.dtype})"
        if cp.kind in ("categorical", "boolean") and cp.stats.get("top_values"):
            sample_vals = list(cp.stats["top_values"].keys())[:5]
            detail += f", example values: {sample_vals}"
        lines.append(detail)
    lines.append("\nFirst 3 rows:")
    lines.append(df.head(3).to_string())
    return "\n".join(lines)


def build_conversation_context(history: list, max_turns: int = 3) -> str:
    """
    Turns recent chat history into a short block of context so follow-up
    questions like "now break that down by region" resolve correctly.

    `history` is expected newest-first (matches how app.py stores it, since
    new questions are inserted at index 0). Only successful exchanges are
    included -- feeding the model its own past failures as "context" tends
    to confuse it rather than help.
    """
    successful = [h for h in history if h.get("success")][:max_turns]
    if not successful:
        return ""

    chronological = list(reversed(successful))
    lines = ["Earlier in this conversation:"]
    for h in chronological:
        lines.append(f'- Question: "{h["question"]}"')
        lines.append(f"  Code used: {h['code']}")
    lines.append(
        "\nIf the new question below refers back to this (e.g. \"now show it by X\", "
        "\"what about last year\", \"and the minimum?\"), build on the same approach."
    )
    return "\n".join(lines)


def _extract_code(raw_text: str) -> str:
    """Strip markdown code fences if the model added them despite instructions."""
    text = raw_text.strip()
    match = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def generate_pandas_code(
    client, question: str, schema_context: str,
    conversation_context: str = "", error_feedback: str = None,
) -> str:
    prompt_parts = [schema_context]
    if conversation_context:
        prompt_parts.append(conversation_context)
    prompt_parts.append(f"Question: {question}")
    prompt = "\n\n".join(prompt_parts)

    if error_feedback:
        prompt += (
            f"\n\nYour previous attempt raised this error:\n{error_feedback}\n"
            "Fix the code and try again."
        )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.1,
        ),
    )
    return _extract_code(response.text)


def answer_question(
    api_key: str, df: pd.DataFrame, profile, question: str,
    history: list = None, max_retries: int = 1,
) -> dict:
    """
    Main entry point. Returns a dict:
      {
        "success": bool,
        "code": str | None,
        "result": Any | None,
        "error": str | None,
      }

    `history` (optional): prior chat_history entries (newest-first), used
    to give follow-up questions context. Pass the list as stored in
    st.session_state.chat_history -- entries for the CURRENT question
    should not be included yet.
    """
    client = genai.Client(api_key=api_key)
    schema_context = build_schema_context(df, profile)
    conversation_context = build_conversation_context(history or [])

    error_feedback = None
    last_code = None

    for attempt in range(max_retries + 1):
        try:
            code = generate_pandas_code(
                client, question, schema_context, conversation_context, error_feedback
            )
            last_code = code
            result = execute_safely(code, df)
            return {"success": True, "code": code, "result": result, "error": None}
        except UnsafeCodeError as e:
            return {"success": False, "code": last_code, "result": None, "error": str(e)}
        except ExecutionError as e:
            error_feedback = str(e)
            if attempt == max_retries:
                return {"success": False, "code": last_code, "result": None, "error": str(e)}

    return {"success": False, "code": last_code, "result": None, "error": "Unknown failure."}
