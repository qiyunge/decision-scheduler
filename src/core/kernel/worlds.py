from __future__ import annotations
from typing import Generic, Tuple

from .types import S, O, A, E
from .contracts import Observer, Transition, Terminal, Policy
from .results import StepResult


class World(Generic[S, O, A, E]):
    """
    Orchestrates: observe -> decide -> transition -> terminal
    This is the engine "glue", not a domain object.
    """

    def __init__(
        self,
        observer: Observer[S, O],
        transition: Transition[S, A, E],
        terminal: Terminal[S],
    ) -> None:
        self._observer = observer
        self._transition = transition
        self._terminal = terminal

    def step(self, state: S, policy: Policy[O, A]) -> StepResult[S, O, A, E]:
        obs = self._observer.observe(state)
        action = policy.decide(obs)
        tr = self._transition.apply(state, action)

        events: Tuple[E, ...] = tuple(tr.events)
        done = self._terminal.is_terminal(tr.state)

        return StepResult(
            prev_state=state,
            obs=obs,
            action=action,
            events=events,
            next_state=tr.state,
            done=done,
        )