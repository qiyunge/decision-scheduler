from __future__ import annotations

from dataclasses import dataclass

@dataclass
class Allocation:
    task_id:int
    resource_id:int
    start_time:int
    end_time:int


    def __post_init__(self):
        if self.start_time < 0:
            raise ValueError("Start time must be a non-negative integer.")
        if self.end_time < self.start_time:
            raise ValueError("End time must be greater than or equal to start time.")