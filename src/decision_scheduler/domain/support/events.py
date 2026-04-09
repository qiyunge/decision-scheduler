from dataclasses import dataclass
from typing import ClassVar

from ..models.task import TaskInit
from ..models.resource import MachineInit
# local imports
from ..models.ids import TaskId, MachineId
from .results import NaturalEffects

@dataclass(frozen=True)
class DomainEvent:
    name:ClassVar[str] = "BaseEvent"
    time :int

# --- domain notified events ---
@dataclass(frozen=True, slots=True)
class DomainNotifiedEvent(DomainEvent):
    name:ClassVar[str] = "DomainNotifiedEvent"

# --- domain initiated/completed events ---
"""Event registration rules:

"""

@dataclass(frozen=True, slots=True)
class DomainInitiatedEvent(DomainEvent):
    name:ClassVar[str] = "DomainInitiatedEvent"

@dataclass(frozen=True, slots=True)
class DomainCompletedEvent(DomainEvent):
    name:ClassVar[str] = "DomainCompletedEvent"

# --- create task events ---
@dataclass(frozen=True, slots=True)
class TaskCreationInitiatedEvent(DomainInitiatedEvent):
    name:ClassVar[str] = "TaskCreatingEvent"
    task_init: TaskInit

@dataclass(frozen=True, slots=True)
class TaskCreatedEvent(DomainCompletedEvent):
    name:ClassVar[str] = "TaskCreatedEvent"
    task_id: TaskId
    task_init: TaskInit
# --- machine events ---
@dataclass(frozen=True, slots=True)
class MachineCreationInitiatedEvent(DomainInitiatedEvent):
    name:ClassVar[str] = "MachineCreationInitiatedEvent"
    machine_init: MachineInit

@dataclass(frozen=True, slots=True)
class MachineCreatedEvent(DomainCompletedEvent):
    name:ClassVar[str] = "MachineCreatedEvent"
    machine_id: MachineId
    machine_init: MachineInit

#--- scheduling events ---
@dataclass(frozen=True, slots=True)
class TaskDispatchInitiatedEvent(DomainInitiatedEvent):
    name:ClassVar[str] = "TaskDispatchInitiatedEvent"
    task_id: TaskId
    machine_id: MachineId

@dataclass(frozen=True, slots=True)
class TaskDispatchedEvent(DomainCompletedEvent):
    name:ClassVar[str] = "TaskDispatchedEvent"
    task_id:  TaskId
    machine_id: MachineId


class TimeAdvanceInitiatedEvent(DomainInitiatedEvent):
    name:ClassVar[str] = "TimeAdvanceInitiatedEvent"
    new_time: int

@dataclass(frozen=True, slots=True)
class TimeAdvancedEvent(DomainCompletedEvent):
    name:ClassVar[str] = "TimeAdvanceEvent"
    old_time:int
    new_time:int

#--- task notified events ---

@dataclass(frozen=True, slots=True)
class TaskCompletedEvent(DomainNotifiedEvent):
    name:ClassVar[str] = "TaskCompletedEvent"
    task_id: TaskId
    machine_id: MachineId



@dataclass(frozen=True, slots=True)
class TaskReleasedEvent(DomainNotifiedEvent):
    name:ClassVar[str] = "TaskReleasedEvent"
    task_id: TaskId

#--- task c
@dataclass(frozen=True, slots=True)
class TaskStartedEvent(DomainNotifiedEvent):
    name:ClassVar[str] = "TaskStartedEvent"
    task_id: TaskId
    machine_id: MachineId

@dataclass(frozen=True, slots=True)
class SysFinishedEvent(DomainNotifiedEvent):
    name:ClassVar[str] = "SysFinishedEvent"

#--- time events ---
@dataclass(frozen=True, slots=True)
class NaturalProcessInitiatedEvent(DomainInitiatedEvent):
    name:ClassVar[str] = "NaturalProcessInitiatedEvent"
    new_time: int
    scheduled_effects: NaturalEffects
@dataclass(frozen=True, slots=True)
class NaturalProcessCompletedEvent(DomainCompletedEvent):
    name:ClassVar[str] = "NaturalProcessCompletedEvent"
    natural_effects: NaturalEffects
    released_events: tuple[TaskReleasedEvent, ...] = ()
    completed_events: tuple[TaskCompletedEvent, ...] = ()


