from __future__ import annotations


from ..models.state import SchedulingState
from ..dynamics.actions import Action,TaskCreateAction, MachineCreateAction
from ..dynamics.transitions import ActionDrivenTransition
from ..support.events import DomainCompletedEvent, DomainEvent, DomainInitiatedEvent,TaskCreationInitiatedEvent,MachineCreationInitiatedEvent
from ...domain.dynamics.observations import StateObservation

from ..models.task import TaskInit
from ..models.resource import MachineInit
from decision_scheduler.domain.models import task

from decision_scheduler.domain.support import events
class ExecutionResult:
    def __init__(self,initiated_events: tuple[DomainInitiatedEvent,...], completed_events: tuple[DomainCompletedEvent,...]):
        self.completed_events = completed_events
        self.initiated_events = initiated_events

class SchedulerWorld:
    def __init__(
        self,
        state: SchedulingState,
        transition: ActionDrivenTransition,
    ):
        self._state = state
        self._transition = transition

    @classmethod
    def create(cls,*,task_inits:tuple[TaskInit,...] = (), machine_inits:tuple[MachineInit,...] = ()) -> tuple["SchedulerWorld", ExecutionResult]:

        world = cls(
            state=SchedulingState(),
            transition=ActionDrivenTransition(),
        )
        execution_result = world.bootstrap(task_inits=task_inits, machine_inits=machine_inits)
        return world, execution_result
    @property  
    def is_finished(self) -> bool:
        return self._state.is_finished    
    
    def bootstrap(self, task_inits:tuple[TaskInit,...] =(), machine_inits:tuple[MachineInit,...] =())->ExecutionResult:
        initiated_events: list[DomainInitiatedEvent] = []
        completed_events: list[DomainCompletedEvent] = []

        for task_init in task_inits:
            ex_rst =self.execute(TaskCreateAction(task_init=task_init))
            initiated_events.extend(ex_rst.initiated_events)
            completed_events.extend(ex_rst.completed_events)    
            
        for machine_init in machine_inits:
            ex_rst =self.execute(MachineCreateAction(machine_init=machine_init))
            initiated_events.extend(ex_rst.initiated_events)
            completed_events.extend(ex_rst.completed_events)

       
        return ExecutionResult(
            initiated_events=tuple(initiated_events),
            completed_events=tuple(completed_events),
        )
           
    
    def observe_decision(self) -> StateObservation:
        return StateObservation(self._state)

    def execute(self, action: Action) -> ExecutionResult:
        initiated_events = self._transition.resolve_action(self._state, action)
        return self._complete_initiated_events(initiated_events)
    
    def advance_naturally(self) -> ExecutionResult:
        initiated_events = self._transition.resolve_natural_process(self._state)
        return self._complete_initiated_events(initiated_events)
    
 
    
    def _complete_initiated_events(self, initiated_events: tuple[DomainInitiatedEvent,...]) -> ExecutionResult:
        completed_events: list[DomainCompletedEvent] = []
        for initiated_event in initiated_events:
            print(f"Initiated natural event: {initiated_event}")
            current_completed_events = self._state.complete(initiated_event)
            completed_events.extend(current_completed_events)

        return ExecutionResult(
            initiated_events=initiated_events,
            completed_events=tuple(completed_events),
        )


    
   