from __future__ import annotations
from dataclasses import dataclass

from core.scheduling.decisions.action import Action

from ..planning.planner import Planner
from core.scheduling.models.scheduling_state import SchedulingState
from core.scheduling.models.task import TaskInit
from core.scheduling.models.resource import MachineInit
from ..planning.policies.base import Policy 
from core.scheduling.transitions.transition import Transition 
from core.scheduling.models.events import Event
@dataclass(frozen=True, slots=True)
class StepResult:
    action: Action
    events: tuple[Event, ...]
    is_terminal: bool


class Simulator:
    """
    Application service.
    Responsible for:
    - running rollout (decision -> apply -> advance) until finished (optional)
    Notes:
    - Does NOT own the state (caller passes state in).
    """

    def __init__(self, planner: Planner, transition: Transition) -> None:
        self.planner = planner
        self.transition = transition

    def step(self, state: SchedulingState, policy: Policy) -> StepResult:
        if state.is_finished():
            return StepResult(action=self.planner.decide(state, policy), events=tuple(), is_terminal=True)

        action = self.planner.decide(state, policy)

        events: list[Event] = []
        events.extend(self.transition.apply(state, action))
        events.extend(self.transition.advance(state))  # 关键：推进世界时间/触发完成/释放等

        return StepResult(action=action, events=tuple(events), is_terminal=state.is_finished())

    def run(self, state: SchedulingState, policy: Policy, *, max_steps: int = 100_000) -> tuple[SchedulingState,tuple[Event, ...]]:
        """
        Rollout until finished or step cap.
        Returns all events for replay/metrics.
        """
        all_events: list[Event] = []

        for _ in range(max_steps):
            if state.is_finished():
                break
            result = self.step(state, policy)
            all_events.extend(result.events)

            # 防止“死循环但不产生事件”的情况（可选但很推荐）
            # 如果 action=Wait 且 advance 也不推进，那系统会卡住。
            if not result.events and not result.is_terminal:
                # 你也可以选择 raise，或者 break 并标记为 deadlock
                break

        return state, tuple(all_events)