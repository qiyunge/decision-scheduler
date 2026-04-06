
from abc import ABC, abstractmethod
from  ...models.state import SchedulingState
from ...models.task import TaskStatus
from ..actions import Action, WaitAction,DispatchAction
from ...semantics.events import DomainEvent

from ...invariants.exceptions import SchedulingException

class Transition(ABC):
    @abstractmethod
    def apply_action(self, state: SchedulingState, action: Action) -> tuple[DomainEvent, ...]:
        ...

    @abstractmethod
    def advance_environment(self, state: SchedulingState) -> tuple[DomainEvent, ...]:
        ...
class ActionDrivenTransition(Transition):
    def apply_action(
        self,
        state: SchedulingState,
        action: Action,
    ) -> tuple[DomainEvent, ...]:
        if isinstance(action, WaitAction):
            return ()

        if isinstance(action, DispatchAction):
            if action.task_id is None or action.machine_id is None:
                raise SchedulingException(
                    "Task ID and Machine ID must be provided for DispatchAction"
                )
            result = state._dispatch(
                machine_id=action.machine_id,
                task_id=action.task_id,
            )
            return tuple(result.events)

        raise SchedulingException(f"Unknown action type: {type(action).__name__}")
    
    def _settle_current_time_completions(self) -> tuple[DomainEvent, ...]:
        completed_machine_ids = [
            machine_id
            for machine_id, until_time in self._busy_until.items()
            if until_time == self._current_time
        ]

        events: list[DomainEvent] = []
        for machine_id in completed_machine_ids:
            result = self._complete_running_task_on_machine(machine_id)
            events.extend(result.events)

        return tuple(events)

    def advance_environment(
    self,
    state: SchedulingState,
) -> tuple[DomainEvent, ...]:
        if state.is_finished():
            return ()

        next_completion = state.next_completion_time()
        if next_completion is not None:
            events: list[DomainEvent] = []
            events.extend(state._advance_time_to(next_completion).events)

            completed_machine_ids = [
                machine_id
                for machine_id, until_time in state._state_core._busy_until.items()
                if until_time == state.current_time
            ]
            for machine_id in completed_machine_ids:
                events.extend(state._complete_running_task_on_machine(machine_id).events)

            return tuple(events)

        next_release = state.next_release_time()
        if next_release is not None:
            events: list[DomainEvent] = []
            events.extend(state._advance_time_to(next_release).events)

            completed_machine_ids = [
                machine_id
                for machine_id, until_time in state._state_core._busy_until.items()
                if until_time == state.current_time
            ]
            for machine_id in completed_machine_ids:
                events.extend(state._complete_running_task_on_machine(machine_id).events)

            return tuple(events)

        return ()