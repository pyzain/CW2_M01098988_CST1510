# app/common/ai_tools.py
"""
Helpers for building a compact, JSON-safe AI context from incident DataFrames.
Designed to avoid circular references and remove likely PII before sending data to the model.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import json
import logging

_logger = logging.getLogger(__name__)

# Columns that are likely to contain PII -> drop by default from payload
DEFAULT_PII_KEYWORDS: List[str] = [
    "email", "e-mail", "ip", "ip_address", "ssn", "social", "password",
    "pwd", "token", "secret", "username", "user", "phone", "mobile"
]


def _mask_or_drop_pii_cols(df: pd.DataFrame, pii_keywords: List[str] = DEFAULT_PII_KEYWORDS) -> Tuple[pd.DataFrame, List[str]]:
    """
    Drop columns that likely contain PII based on keyword matching.
    Returns (clean_df, dropped_columns).
    """
    cols_to_drop = [c for c in df.columns if any(k in c.lower() for k in pii_keywords)]
    if cols_to_drop:
        _logger.debug("Dropping PII columns from AI payload: %s", cols_to_drop)
        return df.drop(columns=cols_to_drop), cols_to_drop
    return df, []


def _safe_sample_rows(df: pd.DataFrame, max_rows: int = 50) -> List[Dict[str, Any]]:
    """
    Return up to max_rows most recent rows as plain dicts (JSON-friendly).
    """
    if df is None or df.empty:
        return []
    if "timestamp" in df.columns:
        s = df.sort_values("timestamp", ascending=False).head(max_rows)
        return s.to_dict(orient="records")
    return df.head(max_rows).to_dict(orient="records")


def _summarize_numeric(df: pd.DataFrame, cols: List[str] = None) -> Dict[str, Dict[str, Any]]:
    """ Return numeric column summaries as plain Python types. """
    if df is None or df.empty:
        return {}
    numeric = df.select_dtypes(include=[np.number])
    if cols:
        numeric = numeric[[c for c in cols if c in numeric.columns]]
    desc = numeric.describe().to_dict()
    # convert numpy types to native
    safe = {}
    for col, stats in desc.items():
        safe[col] = {k: (int(v) if isinstance(v, (np.integer,)) else float(v) if isinstance(v, (np.floating,)) else v) for k, v in stats.items()}
    return safe


def _top_value_counts(df: pd.DataFrame, cols: List[str], topn: int = 10) -> Dict[str, Dict[str, int]]:
    res = {}
    for c in cols:
        if c in df.columns:
            vc = df[c].astype(str).value_counts().head(topn).to_dict()
            # ensure int counts
            res[c] = {str(k): int(v) for k, v in vc.items()}
    return res


def _convert_types_for_json(obj: Any) -> Any:
    """
    Convert numpy / pandas types to native Python types recursively.
    Use sparingly on structures that are already mostly native.
    """
    if isinstance(obj, dict):
        return {k: _convert_types_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_types_for_json(x) for x in obj]
    if isinstance(obj, tuple):
        return tuple(_convert_types_for_json(x) for x in obj)
    # pandas / numpy scalars
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def build_ai_context(
    df: pd.DataFrame,
    filters: Dict[str, Any] = None,
    include_cols: List[str] = None,
    max_sample_rows: int = 40
) -> Dict[str, Any]:
    """
    Build a compact, safe-to-serialize context describing the dashboard state.
    - Drops obvious PII columns
    - Converts problematic dtypes (categorical/numpy) to plain Python
    - Includes top counts, numeric summaries, small sample rows, and a short text summary
    """
    if df is None or df.empty:
        return {"note": "No incident data available."}

    df2 = df.copy()

    # Convert categorical dtypes to str early to avoid internal pd references
    for c in df2.columns:
        if df2[c].dtype.name == "category":
            df2[c] = df2[c].astype(str)

    # Mask / drop PII columns
    df2, dropped_cols = _mask_or_drop_pii_cols(df2)

    # Optionally restrict columns
    if include_cols:
        existing = [c for c in include_cols if c in df2.columns]
        df2 = df2[existing]

    # Core metadata
    context: Dict[str, Any] = {
        "n_rows": int(df2.shape[0]),
        "n_columns": int(df2.shape[1]),
        "columns": list(df2.columns),
        "dropped_pii_columns": dropped_cols,
        "filters": filters or {},
    }

    # Top counts for a few useful categorical columns
    cat_cols = [c for c in ["type", "severity", "status", "asset", "assigned_to"] if c in df2.columns]
    context["top_counts"] = _top_value_counts(df2, cat_cols, topn=10)

    # Numeric summaries
    context["numeric_summary"] = _summarize_numeric(df2)

    # Small sample rows (JSON-friendly)
    context["sample_rows"] = _safe_sample_rows(df2, max_rows=max_sample_rows)

    # Timeseries aggregate if possible (last 90 days)
    if "timestamp" in df2.columns:
        try:
            df2["date"] = pd.to_datetime(df2["timestamp"], errors="coerce").dt.floor("d")
            last_n_days = 90
            recent = df2[df2["date"] >= (pd.Timestamp.now() - pd.Timedelta(days=last_n_days))]
            timeseries = recent.groupby(["date", "type"]).size().reset_index(name="count")
            context["timeseries_last_90d_by_type"] = timeseries.to_dict(orient="records")
        except Exception:
            context["timeseries_last_90d_by_type"] = []
    else:
        context["timeseries_last_90d_by_type"] = []

    # Short text summary useful for RAG prompt header
    try:
        total = int(df2.shape[0])
        top_types = list(context["top_counts"].get("type", {}).items())[:5]
        top_sev = list(context["top_counts"].get("severity", {}).items())[:5]
        context["text_summary"] = {
            "total_incidents": total,
            "top_types": top_types,
            "top_severity": top_sev
        }
    except Exception:
        context["text_summary"] = {}

    # Ensure everything is JSON-serializable (convert numpy/pandas scalars to native)
    safe_context = _convert_types_for_json(context)
    try:
        json.dumps(safe_context)  # quick check that it's serializable
    except Exception:
        # last-resort fallback: stringify complex bits
        for k, v in list(safe_context.items()):
            try:
                json.dumps(v)
            except Exception:
                safe_context[k] = str(v)

    return safe_context
