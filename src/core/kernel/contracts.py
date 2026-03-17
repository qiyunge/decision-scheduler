from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

from .types import S, A, E, O
from .results import TransitionResult, ObservationResult

class Policy(ABC, Generic[O,A]):
    @abstractmethod
    def decide(self, obs: O) -> A:
        raise NotImplementedError
    
class Observer(ABC, Generic[S,O]):
    @abstractmethod
    def observe(self, state: S) -> O:
        raise NotImplementedError
    
class Transition(ABC, Generic[S,A,E]):
    @abstractmethod
    def apply(self, state: S, action: A) -> TransitionResult[S,E]:
        raise NotImplementedError
    
class Termination(ABC, Generic[S]):
    @abstractmethod
    def is_terminal(self, state: S) -> bool:
        raise NotImplementedError