from __future__ import annotations

import pandas as pd

from data_quant.calendars import assign_session, canonicalize_sessions


def test_assign_session_restores_input_order() -> None:
    sessions = canonicalize_sessions(
        pd.DataFrame(
            {
                "session": ["2024-01-02", "2024-01-03"],
                "open_at": ["2024-01-02T09:00:00Z", "2024-01-03T09:00:00Z"],
                "close_at": ["2024-01-02T16:00:00Z", "2024-01-03T16:00:00Z"],
            }
        ),
        timezone="UTC",
    )
    timestamps = pd.Series(["2024-01-03T10:00:00Z", "2024-01-02T10:00:00Z", "2024-01-02T18:00:00Z"])
    assigned = assign_session(timestamps, sessions)
    assert [str(value) if value is not None else None for value in assigned] == [
        "2024-01-03",
        "2024-01-02",
        None,
    ]
