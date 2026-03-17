from __future__ import annotations

from dataclasses import dataclass

from .base import Policy
from ..observations.scheduling_observation import Observation
from core.scheduling.decisions.action import Action, WaitAction,DispatchAction

class FIFOPolicy(Policy):
    def select(self, obs: Observation) -> Action:
        idle = obs.idle_machines()
        ready = obs.ready_tasks()
        if not idle or not ready:
            return WaitAction()
        mid = min(idle)
        tid = min(ready)
        return DispatchAction(tid, mid)