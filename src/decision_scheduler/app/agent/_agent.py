
from dataclasses import dataclass
from abc import ABC, abstractmethod
from ...domain.dynamics.observations import StateObservation


from  ..policies import Policy, DummyPolicy
from ...domain.dynamics.actions import Action

@dataclass(frozen=True)
class Decision:
    decision_time: int
    action: Action

class Agent(ABC):

    def __init__(self, policy: Policy = DummyPolicy()):
        self._policy = policy

    def update_policy(self, policy: Policy):
        self._policy = policy
        
    @abstractmethod
    def decide(self, observation: StateObservation) -> Decision:
        raise NotImplementedError("decide method must be implemented by subclasses.")

class SchedulerAgent(Agent):
 
    def decide(self, observation: StateObservation)->Decision:
        action =self._policy.select(observation)

        return Decision(
            decision_time=observation.current_time,  # Replace with actual decision time if available
            action=action
        )
