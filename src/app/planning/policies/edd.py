from __future__ import annotations
from dataclasses import dataclass

from .base import Policy
from ..observations.scheduling_observation import Observation
from core.scheduling.decisions.action import Action, WaitAction,DispatchAction

from .spt import SPTPolicy


class EDDPolicy(Policy):
    '''
    Earliest Due Date policy.
    '''
   

    def select(self, obs: Observation) -> Action:
        if not obs.ready_tasks() or not obs.idle_machines():
            return WaitAction()
        
        def due(tid):
            
            return obs.task_deadline(tid)
        
        dues = [due(tid) for tid in obs.ready_tasks()]
        if any(d is None for d in dues):
            # if any task has no deadline, fall back to SPT
            spt_policy = SPTPolicy()
            return spt_policy.select(obs)
        else:
            tid = min(obs.ready_tasks(), key=due)
            mid = sorted(obs.idle_machines())[0]  # pick the first idle machine
            return DispatchAction(task_id=tid, machine_id=mid)
        