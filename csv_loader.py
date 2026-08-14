"""
csv_loader.py
-------------
Kaggle CSVs (and real-world CSVs in general) are not always clean UTF-8 --
Excel exports in particular are often saved as Windows-1252/Latin-1, and a
plain pd.read_csv(file) will raise a raw UnicodeDecodeError traceback that
means nothing to a non-technical user.

This module tries a small sequence of encodings and returns a structured
result instead of raising, so app.py can show a friendly message rather
than a stack trace.
"""

import io
from dataclasses import dataclass
from typing import Optional

import pandas as pd

ENCODINGS_TO_TRY = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]

LARGE_DATASET_ROW_THRESHOLD = 300_000


@dataclass
class LoadResult:
    df: Optional[pd.DataFrame]
    encoding_used: Optional[str]
    error: Optional[str]
    is_large: bool = False


def load_csv_robust(uploaded_file) -> LoadResult:
    """
    Reads a Streamlit UploadedFile into a DataFrame, trying multiple
    encodings before giving up. Never raises -- check `.error` on the
    result instead.
    """
    raw_bytes = uploaded_file.getvalue()

    if not raw_bytes.strip():
        return LoadResult(df=None, encoding_used=None, error="The uploaded file is empty.")

    last_error = None
    for encoding in ENCODINGS_TO_TRY:
        try:
            df = pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding, low_memory=False)
        except UnicodeDecodeError as e:
            last_error = f"Encoding issue ({encoding} didn't work): {e}"
            continue
        except pd.errors.ParserError as e:
            return LoadResult(
                df=None, encoding_used=None,
                error=f"This doesn't look like a valid CSV file: {e}",
            )
        except Exception as e:
            return LoadResult(df=None, encoding_used=None, error=f"Couldn't read this file: {e}")
        else:
            if df.empty or len(df.columns) == 0:
                return LoadResult(
                    df=None, encoding_used=encoding,
                    error="The CSV was read but contains no data.",
                )
            is_large = len(df) > LARGE_DATASET_ROW_THRESHOLD
            return LoadResult(df=df, encoding_used=encoding, error=None, is_large=is_large)

    return LoadResult(
        df=None, encoding_used=None,
        error=f"Couldn't decode this file with any common encoding. Last error: {last_error}",
    )


if __name__ == "__main__":
    import types

    def _fake_uploaded_file(raw_bytes: bytes):
        f = types.SimpleNamespace()
        f.getvalue = lambda: raw_bytes
        return f

    print("-- clean UTF-8 --")
    result = load_csv_robust(_fake_uploaded_file(b"name,age\nAlice,30\nBob,25\n"))
    print(f"error={result.error}, encoding={result.encoding_used}, rows={len(result.df) if result.df is not None else None}")

    print("-- cp1252 (Windows Excel export with an accented character) --")
    cp1252_bytes = "name,city\nJos\xe9,S\xe3o Paulo\n".encode("cp1252")
    result = load_csv_robust(_fake_uploaded_file(cp1252_bytes))
    print(f"error={result.error}, encoding={result.encoding_used}, rows={len(result.df) if result.df is not None else None}")

    print("-- empty file --")
    result = load_csv_robust(_fake_uploaded_file(b""))
    print(f"error={result.error}")

    print("-- malformed CSV --")
    result = load_csv_robust(_fake_uploaded_file(b'a,b,c\n1,2\n"unterminated quote,3,4\n'))
    print(f"error={result.error}")
