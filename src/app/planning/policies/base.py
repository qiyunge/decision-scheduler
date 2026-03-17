from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod



from ..observations.scheduling_observation import Observation
from core.scheduling.decisions.action import Action

class Policy(ABC):
    """
    Decision rule pi(Observation) -> Action
    Policy is a stateless function that maps the current observation to a decision (task selection).
    """
    @abstractmethod
    def select(self, obs:Observation) -> Action:
        raise NotImplementedError("select method must be implemented by subclasses.")