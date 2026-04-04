from dataclasses import dataclass


from ..models.ids import TaskId, MachineId


@dataclass(frozen=True)
class Action:...

@dataclass(frozen=True)
class DispatchAction(Action):
    machine_id:MachineId
    task_id:TaskId 
    

@dataclass(frozen=True)
class WaitAction(Action):...

@dataclass(frozen=True)
class PreemptAction(Action):
    machine_id:MachineId
    task_id:TaskId 
   
    