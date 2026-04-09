from __future__ import annotations

from ....domain.dynamics.actions import Action, WaitAction

from ....domain.dynamics.observations._scheduling_observation import StateObservation

from decision_scheduler.domain.models.state import SchedulingState
from  ....app.policies import Policy

class Planner:
    """
    
    """
    def decide(self, state: SchedulingState, policy: Policy)->Action:
        obs = StateObservation(state)
        print(f"Observation at time {obs.current_time}: ready_tasks={obs.ready_tasks},idle_machines={obs.idle_machines}")
       
        if (not obs.idle_machines) or (not obs.ready_tasks):
            return WaitAction()
        action = policy.select(obs)
        print("[DECIDE] action=", action, type(action), type(action).__module__)
        return action