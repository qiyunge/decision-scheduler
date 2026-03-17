from dataclasses import dataclass
from typing import ClassVar

@dataclass(frozen=True)
class Event:
    name:ClassVar[str] = "BaseEvent"


@dataclass(frozen=True)
class TimeAdvanceEvent(Event):
    name:ClassVar[str] = "TimeAdvanceEvent"
    from_time:int
    to_time:int 

@dataclass(frozen=True)
class TaskCompletedEvent(Event):
    name:ClassVar[str] = "TaskCompletedEvent"
    task_id: int
    machine_id: int 
    time:int 

@dataclass(frozen=True)
class TaskStartedEvent(Event):
    name:ClassVar[str] = "TaskStartedEvent"
    task_id: int
    machine_id: int 
    time:int

@dataclass(frozen=True)
class SysFinishedEvent(Event):
    name:ClassVar[str] = "SysFinishedEvent"
    time:int