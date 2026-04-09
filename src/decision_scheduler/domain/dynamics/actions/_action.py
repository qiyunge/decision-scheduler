from dataclasses import dataclass


from ...models.ids import TaskId, MachineId
from ...models.task import TaskInit
from ...models.resource import MachineInit


@dataclass(frozen=True)
class Action:...

@dataclass(frozen=True)
class DispatchAction(Action):
    machine_id:MachineId
    task_id:TaskId 
    

@dataclass(frozen=True)
class WaitAction(Action):...


@dataclass(frozen=True)
class WaitUntilConditionAction(Action):
    pass

@dataclass(frozen=True)
class WaitTaskCompletionAction(Action):
    pass

@dataclass(frozen=True)
class TaskCreateAction(Action):
    task_init: TaskInit


@dataclass(frozen=True)
class MachineCreateAction(Action):
    machine_init: MachineInit