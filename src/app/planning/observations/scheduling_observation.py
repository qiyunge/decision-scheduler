from __future__ import annotations
from dataclasses import dataclass


from domain.scheduling.models.ids import TaskId, MachineId
from domain.scheduling.models.state import SchedulingState 


from typing import Protocol, Iterable

class Observation(Protocol):
    @property
    def current_time(self) -> int: ...

    def ready_tasks(self) -> Iterable[TaskId]: ...
    def idle_machines(self) -> Iterable[MachineId]: ...
    def task_deadline(self, tid: TaskId) -> int | None: ...
    def task_duration(self, tid: TaskId) -> int: ...
   

class StateObservation:
    def __init__(self, state: SchedulingState):
        self._state = state

    @property
    def current_time(self) -> int:
        return self._state.current_time

    def ready_tasks(self):
        return self._state.snapshot_ready_task_ids()  

    def idle_machines(self):
        return self._state.snapshot_idle_machine_ids()

    def task_deadline(self, tid):
        return self._state.task_query().deadline(tid)

    def task_duration(self, tid):
        return self._state.task_query().duration(tid)