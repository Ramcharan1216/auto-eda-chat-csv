"""
chart_generator.py
-------------------
Takes a DataFrame + the DatasetProfile from data_profiler.py and decides,
per column (and per useful column pair), which chart type best explains it.

Design principle: this is a RULE-BASED chart picker, not ML. The rules are
simple on purpose -- they're the "domain knowledge" that makes the app look
smart without needing a model:

  numeric column          -> histogram + boxplot (distribution + outliers)
  categorical column      -> bar chart of value counts (top 15)
  boolean column          -> pie chart
  datetime column present -> time series line chart of row counts over time
  2+ numeric columns      -> correlation heatmap
  numeric + categorical   -> boxplot of numeric grouped by category (top pair only)
"""

from itertools import combinations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import theme  # noqa: F401 -- side effect: registers the "auto_eda" Plotly template
from data_profiler import DatasetProfile, NUMERIC, CATEGORICAL, DATETIME, BOOLEAN

def _numeric_distribution_charts(df: pd.DataFrame, numeric_cols: list) -> list:
    charts = []
    for col in numeric_cols:
        fig = px.histogram(df, x=col, marginal="box", nbins=40, title=f"Distribution of {col}")
        fig.update_layout(bargap=0.05)
        charts.append((f"dist_{col}", fig))
    return charts


def _categorical_bar_charts(df: pd.DataFrame, categorical_cols: list) -> list:
    charts = []
    for col in categorical_cols:
        vc = df[col].value_counts(dropna=True).head(15).reset_index()
        vc.columns = [col, "count"]
        fig = px.bar(vc, x=col, y="count", title=f"Top values in {col}")
        fig.update_layout(xaxis_tickangle=-30)
        charts.append((f"bar_{col}", fig))
    return charts


def _boolean_pie_charts(df: pd.DataFrame, boolean_cols: list) -> list:
    charts = []
    for col in boolean_cols:
        vc = df[col].value_counts(dropna=True).reset_index()
        vc.columns = [col, "count"]
        fig = px.pie(vc, names=col, values="count", title=f"Split of {col}")
        charts.append((f"pie_{col}", fig))
    return charts


def _correlation_heatmap(df: pd.DataFrame, numeric_cols: list):
    if len(numeric_cols) < 2:
        return None
    corr = df[numeric_cols].corr(numeric_only=True)
    fig = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        title="Correlation heatmap (numeric columns)"
    )
    return ("correlation_heatmap", fig)


def _time_series_chart(df: pd.DataFrame, datetime_col: str):
    parsed = pd.to_datetime(df[datetime_col], errors="coerce", format="mixed")
    ts = parsed.dropna().dt.to_period("M").value_counts().sort_index()
    if ts.empty:
        return None
    ts_df = ts.rename_axis("period").reset_index(name="count")
    ts_df["period"] = ts_df["period"].astype(str)
    fig = px.line(ts_df, x="period", y="count", markers=True,
                   title=f"Row count over time (by {datetime_col}, monthly)")
    return (f"timeseries_{datetime_col}", fig)


def _top_numeric_by_category(df: pd.DataFrame, numeric_col: str, categorical_col: str):
    n_categories = df[categorical_col].nunique(dropna=True)
    if n_categories > 12:
        return None
    fig = px.box(df, x=categorical_col, y=numeric_col,
                 title=f"{numeric_col} by {categorical_col}")
    return (f"box_{numeric_col}_by_{categorical_col}", fig)


def generate_charts(df: pd.DataFrame, profile: DatasetProfile, max_relationship_charts: int = 3) -> list:
    """
    Returns a list of (chart_id, plotly_figure) tuples ready to render,
    e.g. with st.plotly_chart(fig) in Streamlit.
    """
    numeric_cols = profile.kind_groups.get(NUMERIC, [])
    categorical_cols = profile.kind_groups.get(CATEGORICAL, [])
    boolean_cols = profile.kind_groups.get(BOOLEAN, [])
    datetime_cols = profile.kind_groups.get(DATETIME, [])

    charts = []
    charts += _numeric_distribution_charts(df, numeric_cols)
    charts += _categorical_bar_charts(df, categorical_cols)
    charts += _boolean_pie_charts(df, boolean_cols)

    heatmap = _correlation_heatmap(df, numeric_cols)
    if heatmap:
        charts.append(heatmap)

    for dt_col in datetime_cols:
        ts_chart = _time_series_chart(df, dt_col)
        if ts_chart:
            charts.append(ts_chart)

    relationship_count = 0
    for num_col in numeric_cols:
        if relationship_count >= max_relationship_charts:
            break
        for cat_col in categorical_cols:
            if relationship_count >= max_relationship_charts:
                break
            rel_chart = _top_numeric_by_category(df, num_col, cat_col)
            if rel_chart:
                charts.append(rel_chart)
                relationship_count += 1

    return charts


if __name__ == "__main__":
    import numpy as np
    from data_profiler import profile_dataset

    rng = np.random.default_rng(0)
    n = 300
    df = pd.DataFrame({
        "age": rng.integers(18, 80, n),
        "spend": rng.normal(100, 30, n),
        "plan": rng.choice(["Basic", "Pro", "Enterprise"], n),
        "active": rng.choice([True, False], n),
        "joined": pd.date_range("2022-01-01", periods=n, freq="3D").astype(str),
    })
    profile = profile_dataset(df)
    charts = generate_charts(df, profile)
    print(f"Generated {len(charts)} charts:")
    for cid, fig in charts:
        print(f"  - {cid} ({fig.layout.title.text})")
