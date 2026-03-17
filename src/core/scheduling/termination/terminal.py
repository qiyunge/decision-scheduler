from __future__ import annotations

from dataclasses import dataclass
from ..models.state import SchedulingState
from ..models.task import TaskStatus

@dataclass
class TerminalStatus:
    is_terminal: bool
    reason: str | None = None

def check_terminal_condition(state:SchedulingState) -> TerminalStatus:
    if state.is_finished():
        return TerminalStatus(is_terminal=True, reason="All tasks completed")
    if (not state.busy_until) and (len(state.ready_task_ids) == 0):
        future_release_exists = False
        for task_id, spec in state.task_specs.items():
            rt = state.task_runtimes[task_id]
            if rt.status == TaskStatus.PENDING and getattr(spec, 'release_time', 0) > state.current_time:
                future_release_exists = True
                break

        if not future_release_exists:
            return TerminalStatus(is_terminal=True, reason="DEADLOCK_NO_READY_NO_FUTURE_RELEASE")
        
    return TerminalStatus(is_terminal=False, reason="running")