"""Timezone-aware trading-session validation."""

from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd

from data_quant.io.validation import parse_utc_timestamp


def validate_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {name!r}") from exc


def canonicalize_sessions(frame: pd.DataFrame, *, timezone: str) -> pd.DataFrame:
    validate_timezone(timezone)
    required = ["session", "open_at", "close_at"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Session table missing columns: {missing}")
    out = frame.copy()
    session_dates = pd.to_datetime(out["session"], errors="coerce")
    if session_dates.isna().any():
        raise ValueError("Session table contains invalid session dates.")
    out["session"] = session_dates.dt.date
    out["open_at"] = parse_utc_timestamp(out["open_at"], "open_at")
    out["close_at"] = parse_utc_timestamp(out["close_at"], "close_at")
    if (out["close_at"] <= out["open_at"]).any():
        raise ValueError("Every session close_at must be later than open_at.")
    if out["session"].duplicated().any():
        raise ValueError("Session dates must be unique within a calendar.")
    return out.sort_values("open_at").reset_index(drop=True)


def assign_session(timestamps: pd.Series, sessions: pd.DataFrame) -> pd.Series:
    events = pd.DataFrame({"_timestamp": parse_utc_timestamp(timestamps, "timestamp")})
    indexed = sessions[["session", "open_at", "close_at"]].sort_values("open_at")
    events["_event_order"] = range(len(events))
    matched = pd.merge_asof(
        events.sort_values("_timestamp"),
        indexed,
        left_on="_timestamp",
        right_on="open_at",
    )
    matched.loc[matched["_timestamp"] > matched["close_at"], "session"] = None
    return matched.sort_values("_event_order")["session"].reset_index(drop=True)
