from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypedDict, NotRequired

from .ids import TaskId, MachineId


class TaskStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True, slots=True)
class _TaskSpec:
    """
    Immutable task specification (theta).
    Used for task generation and scenario definition.
    """
    duration: int = 1
    release_time: int = 0
    deadline: int | None = None

    def __post_init__(self) -> None:
        if self.duration <= 0:
            raise ValueError("duration must be a positive integer.")
        if self.release_time < 0:
            raise ValueError("release_time must be a non-negative integer.")
        if self.deadline is not None and self.deadline <= 0:
            raise ValueError("deadline must be a positive integer or None.")


@dataclass(slots=True)
class _TaskRuntime:
    """
    Mutable runtime state for a task.
    Only aggregate/core should mutate it.
    """
    id: TaskId
    status: TaskStatus = TaskStatus.PENDING
    machine_id: MachineId | None = None
    start_time: int | None = None
    finish_time: int | None = None

    def validate(self) -> None:
        """
        Runtime consistency rules. Call in debug/audit when needed.
        """
        if self.status is TaskStatus.PENDING:
            if self.machine_id is not None or self.start_time is not None or self.finish_time is not None:
                raise ValueError("PENDING task must not have machine_id/start_time/finish_time.")
        elif self.status is TaskStatus.RUNNING:
            if self.machine_id is None or self.start_time is None:
                raise ValueError("RUNNING task must have machine_id and start_time.")
            if self.finish_time is not None:
                raise ValueError("RUNNING task must not have finish_time.")
        elif self.status is TaskStatus.COMPLETED:
            if self.finish_time is None:
                raise ValueError("COMPLETED task must have finish_time.")
        else:
            raise ValueError(f"Unknown status: {self.status}")


@dataclass(frozen=True, slots=True)
class TaskView:
    """
    Read-only DTO for external consumption (facade/app/simulator).
    """
    id: TaskId

    # spec (theta)
    duration: int
    release_time: int
    deadline: int | None

    # runtime
    status: TaskStatus
    machine_id: MachineId | None
    start_time: int | None
    finish_time: int | None


class TaskInit(TypedDict):
    duration: int
    release_time: int
    deadline: NotRequired[int | None]