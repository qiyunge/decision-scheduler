from __future__ import annotations
from dataclasses import dataclass

from ._base import Policy
from ...domain.dynamics.observations._scheduling_observation import Observation
from ...domain.dynamics.actions import Action, WaitAction,DispatchAction

class SPTPolicy(Policy):
    '''
    Shortest Processing Time policy.
    '''


    def select(self, obs: Observation) -> Action:
        if not obs.ready_tasks or not obs.idle_machines:
            return WaitAction()
        
        def duration(tid):
            return obs.task_duration(tid)
        
        tid = min(obs.ready_tasks, key=duration)
        mid = sorted(obs.idle_machines)[0]  # pick the first idle machine
        return DispatchAction( machine_id=mid,task_id=tid)