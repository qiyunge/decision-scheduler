from __future__ import annotations
from dataclasses import dataclass


from ..models.ids import TaskId, MachineId
from ..models.state import SchedulingState as State


@dataclass(frozen=True)
class Observation:
    '''
    Minimal information about the current state of the system that the decision maker can observe.
    - State :full internal truth about the system, including history,allocations,etc.
    - Observation: what the decision maker can observe about the state. 
    '''
    now : int
    # tuple is better than set,because we dont need to modify the ready_tasks,
    # and tuple is more memory efficient than set.
    ready_tasks : tuple[TaskId,...] 
    idle_machines : tuple[MachineId,...]



def create_observation(state: State) -> Observation:
    '''
    Create an observation from the current state.
    This function is deterministic, and  side-effect free.
    IMPORTANT:
    - Do NOT mutate state here (no status changes).
    - Any state mutation belongs to transition().
    '''
    return Observation(
        now=state.current_time,
        ready_tasks=tuple(state.ready_task_ids),
        idle_machines=tuple(state.idle_machine_ids)
    )