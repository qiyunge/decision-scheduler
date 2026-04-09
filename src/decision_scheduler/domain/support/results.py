from dataclasses import dataclass
from typing import Generic, TypeVar

# local imports
from ..models.ids import TaskId, MachineId

T = TypeVar("T")




@dataclass(frozen=True, slots=True)
class TimeAdvanceResult:
    old_time: int
    new_time: int

@dataclass(frozen=True, slots=True)
class TaskCompletionResult:
    task_id: TaskId
    machine_id: MachineId
    completion_time: int

@dataclass(frozen=True, slots=True)
class NaturalEffects:
    released_task_ids: tuple[TaskId, ...]
    completed_task_ids: tuple[TaskId, ...]