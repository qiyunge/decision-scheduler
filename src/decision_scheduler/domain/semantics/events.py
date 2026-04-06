from dataclasses import dataclass
from typing import ClassVar

# local imports
from ..models.ids import TaskId, MachineId

@dataclass(frozen=True)
class DomainEvent:
    name:ClassVar[str] = "BaseEvent"
    time :int

@dataclass(frozen=True, slots=True)
class TaskCreatedEvent(DomainEvent):
    name:ClassVar[str] = "TaskCreatedEvent"
    task_id: TaskId
 
@dataclass(frozen=True, slots=True)
class MachineCreatedEvent(DomainEvent):
    name:ClassVar[str] = "MachineCreatedEvent"
    machine_id: MachineId

@dataclass(frozen=True, slots=True)
class TaskDispatchedEvent(DomainEvent):
    name:ClassVar[str] = "TaskDispatchedEvent"
    task_id:  TaskId
    machine_id: MachineId

@dataclass(frozen=True, slots=True)
class TimeAdvancedEvent(DomainEvent):
    name:ClassVar[str] = "TimeAdvanceEvent"
    old_time:int
    new_time:int 

@dataclass(frozen=True, slots=True)
class TaskCompletedEvent(DomainEvent):
    name:ClassVar[str] = "TaskCompletedEvent"
    task_id: TaskId
    machine_id: MachineId


@dataclass(frozen=True, slots=True)
class TaskStartedEvent(DomainEvent):
    name:ClassVar[str] = "TaskStartedEvent"
    task_id: TaskId
    machine_id: MachineId
 

@dataclass(frozen=True, slots=True)
class SysFinishedEvent(DomainEvent):
    name:ClassVar[str] = "SysFinishedEvent"
  