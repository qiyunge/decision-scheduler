from __future__ import annotations

from core.scheduling.decisions.action import Action, WaitAction
from core.scheduling.models import state

from .observations.scheduling_observation import StateObservation
from core.scheduling.models.resource import Resource

from core.scheduling.models.scheduling_state import SchedulingState
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