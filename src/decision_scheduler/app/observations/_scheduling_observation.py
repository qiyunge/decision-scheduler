from __future__ import annotations
from dataclasses import dataclass


from decision_scheduler.domain.models.ids import TaskId, MachineId
from decision_scheduler.domain.models.state import SchedulingState 


from typing import Protocol, Iterable

class Observation(Protocol):
    @property
    def current_time(self) -> int: ...
    @property
    def ready_tasks(self) -> frozenset[TaskId]: ...
    @property
    def idle_machines(self) -> frozenset[MachineId]: ...
    def task_deadline(self, tid: TaskId) -> int | None: ...
    def task_duration(self, tid: TaskId) -> int: ...
   

class StateObservation:
    def __init__(self, state: SchedulingState):
        self._state = state

    @property
    def current_time(self) -> int:
        return self._state.current_time
    @property
    def ready_tasks(self):
        return self._state.ready_task_ids 
    @property
    def idle_machines(self):
        return self._state.idle_machine_ids

    def task_deadline(self, tid):
        return self._state.task_query.deadline(tid)

    def task_duration(self, tid):
        return self._state.task_query.duration(tid)