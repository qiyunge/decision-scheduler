from __future__ import annotations
from typing import Any

from ...support.events import (DomainEvent,TaskDispatchedEvent,TimeAdvancedEvent, TaskCreatedEvent, MachineCreatedEvent,
                               TaskCreationInitiatedEvent, MachineCreationInitiatedEvent,TaskDispatchInitiatedEvent,TimeAdvanceInitiatedEvent)
from ...support.exceptions import InvalidActionError
from ...models.state import SchedulingState
from ...dynamics.actions import ( Action, WaitAction, DispatchAction, 
                                 WaitTaskCompletionAction,TaskCreateAction, MachineCreateAction)
from ...models.ids import MachineId, TaskId
from .base_transition import StaticRuntimeActionTransition, action_handler



class ActionDrivenTransition(StaticRuntimeActionTransition):

    @action_handler(WaitTaskCompletionAction)
    def _on_wait_task_completion(self, state: SchedulingState, action: WaitTaskCompletionAction) -> tuple[DomainEvent, ...]:
       
        next_time = state.next_task_completion_time
        if next_time is None:
            raise ValueError("WaitTaskCompletionAction is invalid: no running tasks.")

        return (
            TimeAdvanceInitiatedEvent(
                time = state.current_time,
                new_time = next_time,
               
            ),
        )

    @action_handler(TaskCreateAction)
    def _on_create_task(self, state: SchedulingState, action: TaskCreateAction) -> tuple[DomainEvent, ...]:
        return (TaskCreationInitiatedEvent(time=state.current_time, task_init=action.task_init),)

    @action_handler(MachineCreateAction)
    def _on_create_machine(self, state: SchedulingState, action: MachineCreateAction) -> tuple[DomainEvent, ...]:
        return (MachineCreationInitiatedEvent(time=state.current_time, machine_init=action.machine_init),)

  

    @action_handler(DispatchAction)
    def _on_dispatch(
        self,
        state: SchedulingState,
        action: DispatchAction,
    ) -> tuple[DomainEvent, ...]:
        self._validate_dispatch_action(state, action)
        return (
            TaskDispatchInitiatedEvent(
                time=state.current_time,
                machine_id=action.machine_id,
                task_id=action.task_id,
            ),
        )
    
 
    #  -- natural progression resolver ---

    # --- helper methods for action validation ---
    
    def _has_machine(self, state: SchedulingState, machine_id: MachineId) -> bool:
        return machine_id in state.machine_ids

    def _has_task(self, state: SchedulingState, task_id: TaskId) -> bool:
        return task_id in state.task_ids
    
    def _is_machine_idle(self, state: SchedulingState, machine_id: MachineId) -> bool:
        return machine_id in state.idle_machine_ids
    
    def _is_task_ready(self, state: SchedulingState, task_id: TaskId) -> bool:
        return task_id in state.ready_task_ids
    

    def _validate_dispatch_action(
        self,
        state: SchedulingState,
        action: DispatchAction,
    ) -> None:
        if not self._has_machine(state, action.machine_id):
            raise InvalidActionError(f"Unknown machine_id: {action.machine_id}")
        if not self._has_task(state, action.task_id):
            raise InvalidActionError(f"Unknown task_id: {action.task_id}")
        if not self._is_machine_idle(state, action.machine_id):
            raise InvalidActionError(f"Machine {action.machine_id} is not idle.")
        if not self._is_task_ready(state, action.task_id):
            raise InvalidActionError(f"Task {action.task_id} is not ready.")