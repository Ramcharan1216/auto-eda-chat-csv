"""
suggested_questions.py
-----------------------
Generates a handful of example questions tailored to the actual columns
in the uploaded dataset, so the chat tab isn't just a blank input box
with no hint of what's possible.

Deliberately rule-based, not LLM-based: it needs to be instant, free, and
available even before the user has entered an API key (since it only
reads the already-computed DatasetProfile from data_profiler.py).
"""

from data_profiler import NUMERIC, CATEGORICAL, DATETIME, BOOLEAN


def generate_suggested_questions(profile, max_questions: int = 4) -> list:
    numeric = profile.kind_groups.get(NUMERIC, [])
    categorical = profile.kind_groups.get(CATEGORICAL, [])
    datetime_cols = profile.kind_groups.get(DATETIME, [])

    candidates = []

    if numeric:
        candidates.append(f"What is the average {numeric[0]}?")
    if numeric and categorical:
        candidates.append(f"What is the average {numeric[0]} by {categorical[0]}?")
    if categorical:
        candidates.append(f"What are the top 5 most common values in {categorical[0]}?")
    if len(numeric) >= 2:
        candidates.append(f"Is there a correlation between {numeric[0]} and {numeric[1]}?")
    if datetime_cols:
        candidates.append(f"How does the row count change over time based on {datetime_cols[0]}?")
    if numeric:
        candidates.append(f"What are the 5 highest values of {numeric[-1]}?")

    if not candidates:
        candidates.append("How many rows and columns does this dataset have?")

    return candidates[:max_questions]


if __name__ == "__main__":
    import pandas as pd
    import numpy as np
    from data_profiler import profile_dataset

    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "price": rng.normal(50, 10, 200),
        "rating": rng.normal(4.2, 0.5, 200),
        "city": rng.choice(["Bandung", "Jakarta", "Surabaya"], 200),
        "listed_on": pd.date_range("2023-01-01", periods=200, freq="3D").astype(str),
    })
    profile = profile_dataset(df)
    for q in generate_suggested_questions(profile):
        print(f"- {q}")
