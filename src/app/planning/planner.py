from __future__ import annotations

from domain.scheduling.decisions.action import Action, WaitAction
from domain.scheduling.models import state

from .observations.scheduling_observation import StateObservation
from domain.scheduling.models.resource import Resource

from domain.scheduling.models.state import SchedulingState
from .policies.base import Policy

class Planner:
    """
    
    """
    def decide(self, state: SchedulingState, policy: Policy)->Action:
        obs = StateObservation(state)
        print(f"Observation at time {obs.current_time}: ready_tasks={obs.ready_tasks()}, idle_machines={obs.idle_machines()}")
       
        if (not obs.idle_machines()) or (not obs.ready_tasks()):
            return WaitAction()
        action = policy.select(obs)
        print("[DECIDE] action=", action, type(action), type(action).__module__)
        return action