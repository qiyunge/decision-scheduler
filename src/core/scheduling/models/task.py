from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

from typing import TypedDict

from .ids import TaskId, MachineId


class TaskStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    # READY = "READY"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True,slots=True)
class _TaskSpec:
    '''
    Task specification, used for task generation.
    '''
    # id: TaskId
    duration:int = 1
    release_time:int = 0
    deadline:int | None = None

    def __post_init__(self):
        if self.duration <= 0:
            raise ValueError("Duration must be a positive integer.")
        if self.release_time < 0:
            raise ValueError("Release time must be a non-negative integer.")
        if self.deadline is not None and self.deadline <= 0:
            raise ValueError("Deadline must be a positive integer or None.")
        


@dataclass(slots=True)
class _TaskRuntime:
    '''
    Task runtime information, used for scheduling and state mutation.
    '''
    id: TaskId
    status: TaskStatus = TaskStatus.PENDING
    machine_id: MachineId | None = None
    start_time:int | None = None
    finish_time:int | None = None

    

# @dataclass(frozen=True)
# class Task:
#     id: TaskId
#     duration:int
#     release_time:int
#     deadline:int | None = None

#     def __post_init__(self):
#         if self.duration <= 0:
#             raise ValueError("Duration must be a positive integer.")
#         if self.release_time < 0:
#             raise ValueError("Release time must be a non-negative integer.")
#         if self.deadline is not None and self.deadline <= 0:
#             raise ValueError("Deadline must be a positive integer or None.")

@dataclass(frozen=True,slots=True)
class TaskView():
    id: TaskId
    status: TaskStatus
    machine_id: MachineId | None
    start_time: int | None
    finish_time: int | None

    duration: int
    release_time: int
    deadline: int | None


class TaskInit(TypedDict):
    duration:int
    release_time:int
    deadline:int | None 

  
   