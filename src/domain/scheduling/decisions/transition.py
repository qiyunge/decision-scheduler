from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Iterable, TypeVar, Callable,ClassVar

from domain.scheduling.decisions.invariants.exceptions import SchedulingException
from domain.scheduling.models.ids import TaskId
from domain.scheduling.models.task import TaskStatus

from domain.scheduling.decisions.transitions.transition import Transition
from domain.scheduling.models.state import SchedulingState
from domain.scheduling.decisions.action import Action, WaitAction, DispatchAction
from domain.scheduling.models.events import Event, TimeAdvanceEvent


# =========================================================
# Rule Protocols
# =========================================================

class ActionRule(Protocol):
    priority: ClassVar[int]

    def matches(self, state: SchedulingState, action: Action) -> bool: ...
    def apply(self, state: SchedulingState, action: Action) -> list[Event]: ...


class AdvanceRule(Protocol):
    priority: ClassVar[int]

    def matches(self, state: SchedulingState) -> bool: ...
    def apply(self, state: SchedulingState) -> list[Event]: ...


T = TypeVar("T")


def _select_unique(
    rules: Iterable[T],
    predicate: Callable[[T], bool],
    *,
    context: str,
) -> T:
    
  
    matched = [r for r in rules if predicate(r)]
    if len(matched) == 1:
        return matched[0]
    if len(matched) == 0:
        raise SchedulingException(f"[{context}] No rule matched (world underspecified).")
    names = ", ".join(getattr(r, "name", r.__class__.__name__) for r in matched)
    raise SchedulingException(f"[{context}] Multiple rules matched (conflict): {names}")


# =========================================================
# Action Rules
# =========================================================

@dataclass(frozen=True, slots=True)
class WaitRule:
    priority: ClassVar[int] = 0

    def matches(self, state: SchedulingState, action: Action) -> bool:
        return isinstance(action, WaitAction)

    def apply(self, state: SchedulingState, action: Action) -> list[Event]:
        return []


@dataclass(frozen=True, slots=True)
class DispatchRule:
    priority: ClassVar[int] = 10

    def matches(self, state: SchedulingState, action: Action) -> bool:
        return isinstance(action, DispatchAction)

    def apply(self, state: SchedulingState, action: Action) -> list[Event]:
        # 类型收窄
        act = action  # type: ignore[assignment]
        if act.task_id is None or act.machine_id is None:
            raise SchedulingException("Task ID and Machine ID must be provided for DispatchAction")
        return state.dispatch(machine_id=act.machine_id, task_id=act.task_id)


# =========================================================
# Advance Rules
# =========================================================

@dataclass(frozen=True, slots=True)
class FinishedNoAdvanceRule:
    priority: ClassVar[int] = 0

    def matches(self, state: SchedulingState) -> bool:
        return state.is_finished()

    def apply(self, state: SchedulingState) -> list[Event]:
        return []


@dataclass(frozen=True, slots=True)
class BusyJumpToCompletionRule:
    priority: ClassVar[int] = 10

    def matches(self, state: SchedulingState) -> bool:
        if state.is_finished():
            return False
        return state.next_completion_time() is not None

    def apply(self, state: SchedulingState) -> list[Event]:
        # 你的 state 已经实现：推进到下一个完成点，并返回对应事件
        nxt_time = state.next_completion_time()
        if nxt_time is None:
            return []
        state.advance_time_to(nxt_time)
        return []


@dataclass(frozen=True, slots=True)
class IdleJumpToNextReleaseRule:
    priority: ClassVar[int] = 20

    def matches(self, state: SchedulingState) -> bool:
        if state.is_finished():
            return False

        # 关键：只在“没有 running task”时才允许 jump to release
        if state.next_completion_time() is not None:
            return False

        # 如果有 ready task，也不需要跳时间
        if len(state.snapshot_ready_task_ids()) > 0:
            return False

        # 有未来 release 才跳
        return state.next_release_time() is not None

    def apply(self, state: SchedulingState) -> list[Event]:
        t1 = state.next_release_time()
        if t1 is None:
            return []
        rec = state.advance_time_to(t1)
        if rec is None:
            return []
        return [TimeAdvanceEvent(from_time=rec.from_time, to_time=rec.to_time)]


@dataclass(frozen=True, slots=True)
class IdleForeverRule:
    priority: ClassVar[int] = 999

    def matches(self, state: SchedulingState) -> bool:
        if state.is_finished():
            return False

        # “busy_until” 不再直接访问内部 dict：
        # 只要有下一次 completion，就说明仍有在跑的任务，不是 forever idle
        if state.next_completion_time() is not None:
            return False

        # 没有未来 release（pending 且 release_time > now）
        return state.next_release_time() is None

    def apply(self, state: SchedulingState) -> list[Event]:
        return []
# =========================================================
# RuleBasedTransition (Engine)
# =========================================================

class RuleBasedTransition(Transition):


    def __init__(self) -> None:
        self._action_rules: list[ActionRule] = sorted(
            [WaitRule(), DispatchRule()],
            key=lambda r: r.priority,
        )
        self._advance_rules: list[AdvanceRule] = sorted(
            [
                FinishedNoAdvanceRule(),
                BusyJumpToCompletionRule(),
                IdleJumpToNextReleaseRule(),
                IdleForeverRule(),
            ],
            key=lambda r: r.priority,
        )

    def apply(self, state: SchedulingState, action: Action) -> list[Event]:
        rule = _select_unique(
            self._action_rules,
            lambda r: r.matches(state, action),
            context="APPLY",
        )
        return rule.apply(state, action)

    def advance(self, state: SchedulingState) -> list[Event]:
        rule = _select_unique(
            self._advance_rules,
            lambda r: r.matches(state),
            context="ADVANCE",
        )
        return rule.apply(state)