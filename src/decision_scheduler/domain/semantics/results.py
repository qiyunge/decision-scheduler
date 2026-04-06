from dataclasses import dataclass
from typing import Generic, TypeVar

# local imports
from .events import DomainEvent
from ..models.ids import TaskId, MachineId

T = TypeVar("T")



@dataclass(frozen=True, slots=True)
class MutationResult(Generic[T]):
    value: T 
    events: tuple[DomainEvent, ...]

    @staticmethod
    def of(value: T, *events: DomainEvent) -> "MutationResult[T]":
        return MutationResult(value=value, events= events)

@dataclass(frozen=True, slots=True)
class TimeAdvanceResult:
    old_time: int
    new_time: int

@dataclass(frozen=True, slots=True)
class TaskCompletionResult:
    task_id: TaskId
    machine_id: MachineId
    completion_time: int