# models/mutations.py

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TimeAdvanceRecord:
    from_time: int
    to_time: int