from __future__ import annotations
from dataclasses import dataclass

from ...domain.dynamics.actions import Action
from ..observations import StateObservation,Observation
from ...domain.models.state import SchedulingState
from ..planning.planners import Planner
from ..policies import Policy
from ...domain.dynamics import Transition, ActionDrivenTransition
from ...domain.semantics.events import DomainEvent



@dataclass(frozen=True, slots=True)
class StepResult:
    action: Action
    events: tuple[DomainEvent, ...]
    is_terminal: bool


class Simulator:
    """
    Application service.
    Responsible for:
    - running rollout (decision -> apply -> advance) until finished (optional)
    Notes:
    - Does NOT own the state (caller passes state in).
    """

    def __init__(self,state: SchedulingState,
                  transition: ActionDrivenTransition,
                  planner: Planner) -> None:
        self._state = state
        self._planner = planner
        self._transition = transition

    def observe(self) -> Observation:
        return StateObservation(self._state)

    def step(self, policy: Policy) -> StepResult:
        print(
        "[STEP-ENV]",
        f"time={self._state.current_time}",
        f"finished={self._state.is_finished()}",
        f"busy_until={self._state._state_core._busy_until}",
        f"next_completion={self._state.next_completion_time()}",
        f"next_release={self._state.next_release_time()}",
    )
        if self._state.is_finished():
            return StepResult(action=None, events=tuple(), is_terminal=True)

        if self._decision_needed():
            action = self._planner.decide(self._state, policy)
            events = tuple(self._transition.apply_action(self._state, action))
            return StepResult(
                action=action,
                events=events,
                is_terminal=self._state.is_finished(),
            )

        events = tuple(self._transition.advance_environment(self._state))
        return StepResult(
            action=None,
            events=events,
            is_terminal=self._state.is_finished(),
    )

    def _decision_needed(self) -> bool:
        obs = self.observe()
        return bool(obs.ready_tasks) and bool(obs.idle_machines)
    
    def run(self,policy: Policy, *, max_steps: int = 100_000) -> tuple[SchedulingState,tuple[DomainEvent, ...]]:
        """
        Rollout until finished or step cap.
        Returns all events for replay/metrics.
        """
        all_events: list[DomainEvent] = []

        for _ in range(max_steps):
            if self._state.is_finished():
                break
            result = self.step(policy)
            all_events.extend(result.events)

            # 防止“死循环但不产生事件”的情况（可选但很推荐）
            # 如果 action=Wait 且 advance 也不推进，那系统会卡住。
            if not result.events and not result.is_terminal:
                # 你也可以选择 raise，或者 break 并标记为 deadlock
                break

        return self._state, tuple(all_events)