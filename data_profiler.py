"""
data_profiler.py
-----------------
Core engine for Week 1 of the Auto-EDA project.

Given ANY raw CSV loaded into a pandas DataFrame, this module:
  1. Detects the semantic type of every column (numeric, categorical,
     datetime, text/high-cardinality, boolean, id-like).
  2. Computes summary statistics appropriate to each type.
  3. Flags data quality issues (missing values, duplicates, outliers,
     constant columns, high-cardinality columns).

This is deliberately dataset-agnostic -- it should work the same way
on a Titanic CSV, a sales CSV, or a churn CSV without any manual
configuration. That generality is the whole point of the project.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Column type detection
# ---------------------------------------------------------------------------

NUMERIC = "numeric"
CATEGORICAL = "categorical"
DATETIME = "datetime"
BOOLEAN = "boolean"
TEXT = "text"
ID_LIKE = "id_like"


def _looks_like_id(series: pd.Series, col_name: str) -> bool:
    name_hint = any(tok in col_name.lower() for tok in ["id", "uuid", "key", "index", "_no", "number"])
    uniqueness = series.nunique(dropna=True) / max(len(series), 1)
    return uniqueness > 0.95 and (name_hint or series.dtype == object)


def _try_parse_datetime(series: pd.Series) -> Optional[pd.Series]:
    if series.dtype == object or pd.api.types.is_string_dtype(series):
        sample = series.dropna().astype(str).head(50)
        if sample.empty:
            return None
        try:
            parsed_sample = pd.to_datetime(sample, errors="coerce", format="mixed")
        except Exception:
            return None
        if parsed_sample.notna().mean() < 0.8:
            return None
        parsed_full = pd.to_datetime(series, errors="coerce", format="mixed")
        return parsed_full
    return None


def detect_column_type(series: pd.Series, col_name: str) -> str:
    n = len(series)
    if n == 0:
        return TEXT

    if pd.api.types.is_bool_dtype(series):
        return BOOLEAN

    if pd.api.types.is_datetime64_any_dtype(series):
        return DATETIME

    if pd.api.types.is_numeric_dtype(series):
        nunique = series.nunique(dropna=True)
        if nunique <= 10 and series.dropna().apply(lambda x: float(x).is_integer()).all():
            return CATEGORICAL
        if _looks_like_id(series, col_name):
            return ID_LIKE
        return NUMERIC

    parsed = _try_parse_datetime(series)
    if parsed is not None:
        return DATETIME

    if _looks_like_id(series, col_name):
        return ID_LIKE

    nunique = series.nunique(dropna=True)
    uniqueness_ratio = nunique / max(n, 1)

    if nunique <= 50 or uniqueness_ratio < 0.05:
        return CATEGORICAL
    return TEXT


# ---------------------------------------------------------------------------
# Per-column profile
# ---------------------------------------------------------------------------

@dataclass
class ColumnProfile:
    name: str
    kind: str
    dtype: str
    missing_count: int
    missing_pct: float
    n_unique: int
    stats: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)


def _iqr_outlier_count(series: pd.Series) -> int:
    clean = series.dropna()
    if len(clean) < 4:
        return 0
    q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return int(((clean < lower) | (clean > upper)).sum())


def profile_column(df: pd.DataFrame, col_name: str) -> ColumnProfile:
    series = df[col_name]
    n = len(series)
    missing = int(series.isna().sum())
    kind = detect_column_type(series, col_name)

    profile = ColumnProfile(
        name=col_name,
        kind=kind,
        dtype=str(series.dtype),
        missing_count=missing,
        missing_pct=round(100 * missing / max(n, 1), 2),
        n_unique=int(series.nunique(dropna=True)),
    )

    if kind == NUMERIC:
        clean = pd.to_numeric(series, errors="coerce").dropna()
        if not clean.empty:
            profile.stats = {
                "mean": round(float(clean.mean()), 4),
                "median": round(float(clean.median()), 4),
                "std": round(float(clean.std()), 4) if len(clean) > 1 else 0.0,
                "min": float(clean.min()),
                "max": float(clean.max()),
                "skew": round(float(clean.skew()), 4) if len(clean) > 2 else 0.0,
                "outlier_count": _iqr_outlier_count(clean),
            }
            if profile.stats["outlier_count"] > 0:
                profile.warnings.append(
                    f"{profile.stats['outlier_count']} potential outliers (IQR method)"
                )
            if abs(profile.stats["skew"]) > 1:
                profile.warnings.append(f"highly skewed (skew={profile.stats['skew']})")

    elif kind == CATEGORICAL or kind == BOOLEAN:
        vc = series.value_counts(dropna=True).head(20)
        profile.stats = {"top_values": vc.to_dict()}
        if profile.n_unique == 1:
            profile.warnings.append("constant column (only 1 unique value) -- likely useless")

    elif kind == DATETIME:
        parsed = series if pd.api.types.is_datetime64_any_dtype(series) else _try_parse_datetime(series)
        clean = parsed.dropna() if parsed is not None else pd.Series([], dtype="datetime64[ns]")
        if not clean.empty:
            profile.stats = {
                "min_date": str(clean.min()),
                "max_date": str(clean.max()),
                "span_days": int((clean.max() - clean.min()).days),
            }

    elif kind == TEXT:
        lengths = series.dropna().astype(str).str.len()
        profile.stats = {
            "avg_length": round(float(lengths.mean()), 1) if not lengths.empty else 0,
            "n_unique": profile.n_unique,
        }

    if profile.missing_pct > 30:
        profile.warnings.append(f"{profile.missing_pct}% missing -- consider imputation or dropping")

    return profile


# ---------------------------------------------------------------------------
# Whole-dataframe profile
# ---------------------------------------------------------------------------

@dataclass
class DatasetProfile:
    n_rows: int
    n_cols: int
    n_duplicate_rows: int
    memory_mb: float
    column_profiles: dict
    kind_groups: dict
    dataset_warnings: list = field(default_factory=list)


def profile_dataset(df: pd.DataFrame) -> DatasetProfile:
    column_profiles = {col: profile_column(df, col) for col in df.columns}

    kind_groups: dict = {}
    for name, cp in column_profiles.items():
        kind_groups.setdefault(cp.kind, []).append(name)

    dataset_warnings = []
    n_dupes = int(df.duplicated().sum())
    if n_dupes > 0:
        dataset_warnings.append(f"{n_dupes} duplicate rows found")

    high_missing_cols = [c for c, cp in column_profiles.items() if cp.missing_pct > 50]
    if high_missing_cols:
        dataset_warnings.append(f"columns >50% missing: {', '.join(high_missing_cols)}")

    constant_cols = [c for c, cp in column_profiles.items() if cp.n_unique <= 1]
    if constant_cols:
        dataset_warnings.append(f"constant/near-constant columns: {', '.join(constant_cols)}")

    return DatasetProfile(
        n_rows=len(df),
        n_cols=len(df.columns),
        n_duplicate_rows=n_dupes,
        memory_mb=round(df.memory_usage(deep=True).sum() / (1024 ** 2), 3),
        column_profiles=column_profiles,
        kind_groups=kind_groups,
        dataset_warnings=dataset_warnings,
    )


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    n = 500
    df = pd.DataFrame({
        "customer_id": [f"CUST{i:05d}" for i in range(n)],
        "age": rng.integers(18, 90, n).astype(float),
        "signup_date": pd.date_range("2021-01-01", periods=n, freq="D").astype(str),
        "plan_type": rng.choice(["Basic", "Pro", "Enterprise"], n),
        "monthly_spend": np.concatenate([rng.normal(50, 15, n - 5), [500, 520, -10, 0, 600]]),
        "is_active": rng.choice([True, False], n),
        "notes": rng.choice(["", "called about billing issue last week", "n/a"], n),
        "country": rng.choice(["US"] * 490 + ["CA", "UK", "IN", "AU", "DE"] * 2, n),
        "constant_col": ["same_value"] * n,
    })
    df.loc[rng.choice(n, 60, replace=False), "monthly_spend"] = np.nan
    df.loc[rng.choice(n, 200, replace=False), "notes"] = np.nan

    result = profile_dataset(df)
    print(f"Rows: {result.n_rows}, Cols: {result.n_cols}, Duplicates: {result.n_duplicate_rows}")
    print(f"Dataset warnings: {result.dataset_warnings}")
    print(f"Column kinds: { {k: v for k, v in result.kind_groups.items()} }")
    print()
    for name, cp in result.column_profiles.items():
        print(f"- {name}: kind={cp.kind}, missing={cp.missing_pct}%, unique={cp.n_unique}, warnings={cp.warnings}")
