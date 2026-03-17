from __future__ import annotations

from dataclasses import dataclass
from .ids import ResourceId,MachineId, TaskId

@dataclass
class Resource:
    id:ResourceId
    availability_time:int = 0

    def __post_init__(self):
        if self.availability_time < 0:
            raise ValueError("Availability time must be a non-negative integer.")   
        

@dataclass(frozen=True)
class _MachineSpec:
    # id:MachineId
    # availability_time:int = 0
    @classmethod
    def from_init(cls, machine_init:MachineInit) -> _MachineSpec:
        # For now, we don't have any parameters in MachineInit, but this method can be extended in the future if needed.
        return cls()

    def __post_init__(self):
        # if self.availability_time < 0:
        #     raise ValueError("Availability time must be a non-negative integer.")  
        pass
        
@dataclass
class _MachineRuntime:
    id:MachineId
    availability_time:int = 0

    def __post_init__(self):
        if self.availability_time < 0:
            raise ValueError("Availability time must be a non-negative integer.")
        

@dataclass
class MachineInit:
    pass  

@dataclass(frozen=True,slots=True)
class MachineView:
    id:MachineId
    availability_time:int = 0
    task_id: TaskId | None = None