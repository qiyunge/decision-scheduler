from __future__ import annotations
from dataclasses import dataclass
from typing import Generic ,Sequence

from .types import S, A, E, O

@dataclass(frozen=True)
class TransitionResult(Generic[S,E]):
    next_state: S
    event: E

@dataclass(frozen=True)
class StepResult(Generic[S,O,A,E]):
    """
    One step trace record (good for debugging / metrics / replay).
    """
    prev_state: S
    obs: O
    action: A
    events: tuple[E, ...]
    next_state: S
    done: bool