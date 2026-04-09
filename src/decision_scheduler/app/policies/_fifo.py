from __future__ import annotations

from dataclasses import dataclass

from ._base import Policy
from ...domain.dynamics.observations._scheduling_observation import Observation
from ...domain.dynamics.actions import Action, WaitAction,DispatchAction

class FIFOPolicy(Policy):
    def select(self, obs: Observation) -> Action:
        idle = obs.idle_machines
        ready = obs.ready_tasks
        if not idle or not ready:
            return WaitAction()
        mid = min(idle)
        tid = min(ready)
        return DispatchAction(task_id=tid, machine_id=mid)